"""Dataset registry for the multi-dataset benchmark (master prompt v2 P3; docs/KAGGLE_DATASETS.md rules).

Each entry is declarative: source URL, licence, provenance, SHA-256 of the raw file, target rule, dropped columns with
reasons, and a column spec (numeric / binary / ordinal / nominal with declared levels). A single generic loader turns
the raw file into a numeric feature matrix (NaN = missing) and a binary label (1 = disease / event).
Category-to-number mappings come from the declared spec, not from the data, so nothing is fitted outside a fold;
imputation, scaling and feature selection stay inside the per-fold Pipeline (preprocess.make_preprocessor).
Raw files live in data/raw/<name>/ (git-ignored, never committed).

python -m backend.ml.quantum.registry fetch [--name NAME]   download + verify checksums
python -m backend.ml.quantum.registry summary               rows, features, class balance, missingness
"""

import argparse
import hashlib
import io
import json
import logging
import os
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = Path(os.getenv("QML_DATA_DIR", ROOT / "data" / "raw"))
USER_AGENT = "sih26139-benchmark/1.0 (research prototype)"


@dataclass(frozen=True)
class Column:
    name: str
    kind: str = "numeric"  # numeric | binary | ordinal | nominal
    levels: tuple = ()     # binary: (negative, positive); ordinal: low..high; nominal: one-hot levels
    zero_is_missing: bool = False
    max_value: float | None = None  # values above a declared physiological maximum are data-entry errors -> missing


@dataclass(frozen=True)
class DatasetEntry:
    name: str
    title: str
    split: str             # development | confirmation | sanity
    source: str
    url: str
    file: str              # file name inside data/raw/<name>/ (downloaded as-is)
    member: str | None     # member inside a zip archive, if any
    sha256: str | None     # of the downloaded file; None until first verified fetch is recorded
    licence: str
    provenance: str
    positive_class: str
    target: str
    positive_values: tuple
    reader: dict = field(default_factory=dict)   # pandas/arff read options
    columns: tuple = ()                          # Column specs for the kept features
    dropped: dict = field(default_factory=dict)  # column -> reason
    leakage_notes: str = ""
    builtin: bool = False                        # loaded by data.py (WDBC, Cleveland)
    group_column: str | None = None              # rows sharing a group (same subject) never split across folds
    group_regex: str | None = None               # first capture group of this regex on group_column = group key


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def raw_path(entry: DatasetEntry) -> Path:
    return RAW_DIR / entry.name / entry.file


def fetch(entry: DatasetEntry, force: bool = False) -> Path:
    """Download the raw file once; verify its SHA-256 against the registry when one is recorded."""
    path = raw_path(entry)
    if force or not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(entry.url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - fixed https URLs from the registry
            data = resp.read()
        path.write_bytes(data)
    digest = sha256(path)
    if entry.sha256 and digest != entry.sha256:
        raise ValueError(f"{entry.name}: checksum mismatch ({digest} != registry {entry.sha256})")
    return path


def _read_raw(entry: DatasetEntry) -> pd.DataFrame:
    path = fetch(entry)
    opts = dict(entry.reader)
    fmt = opts.pop("format", "csv")
    if entry.member:
        with zipfile.ZipFile(path) as z:
            data = z.read(entry.member)
    else:
        data = path.read_bytes()
    text = data.decode(opts.pop("encoding", "utf-8"), errors="replace")
    if fmt == "arff":
        return _read_arff(text, opts.get("na_values", ["?"]))
    if fmt == "excel":
        return pd.read_excel(io.BytesIO(data), **opts)
    return pd.read_csv(io.StringIO(text), **opts)


def _read_arff(text: str, na_values) -> pd.DataFrame:
    """Tolerant ARFF reader (UCI's CKD file has stray spaces/tabs and an extra trailing comma on some rows)."""
    names, rows, in_data = [], [], False
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        low = s.lower()
        if low.startswith("@attribute"):
            names.append(s.split()[1].strip("'\""))
        elif low.startswith("@data"):
            in_data = True
        elif in_data:
            vals = [v.strip().strip("'\"") for v in s.split(",")]
            rows.append((vals + [None] * len(names))[:len(names)])
    df = pd.DataFrame(rows, columns=names)
    return df.replace({v: np.nan for v in na_values} | {"": np.nan})


def _encode(series: pd.Series, col: Column) -> pd.DataFrame:
    s = series.copy()
    if col.kind == "numeric":
        out = pd.to_numeric(s, errors="coerce")
        if col.zero_is_missing:
            out = out.mask(out == 0)
        if col.max_value is not None:
            out = out.mask(out > col.max_value)
        return out.to_frame(col.name)
    s = s.map(lambda v: str(v).strip() if pd.notna(v) else v)
    if col.kind == "binary":
        neg, pos = (str(x) for x in col.levels)
        return s.map({neg: 0.0, pos: 1.0}).to_frame(col.name)
    if col.kind == "ordinal":
        return s.map({str(v): float(i) for i, v in enumerate(col.levels)}).to_frame(col.name)
    if col.kind == "nominal":  # one-hot over declared levels; unseen/missing -> all NaN (imputed in-fold)
        cols = {f"{col.name}={lv}": np.where(s.isna(), np.nan, (s == str(lv)).astype(float)) for lv in col.levels}
        return pd.DataFrame(cols, index=s.index)
    raise ValueError(f"unknown column kind {col.kind}")


def _builtin(entry: DatasetEntry):
    from backend.ml.quantum import data  # local import: data.py dispatches non-built-in names to this module
    return data.load_builtin(entry.name)


def groups(entry: DatasetEntry) -> np.ndarray | None:
    """Group key per row (same order as load), or None when rows are independent."""
    if not entry.group_column:
        return None
    df = _read_raw(entry)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[df[entry.target].notna()]
    col = df[entry.group_column].astype(str)
    return (col.str.extract(entry.group_regex, expand=False) if entry.group_regex else col).to_numpy()


def load(entry: DatasetEntry) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Numeric features (NaN = missing), binary label (1 = positive_class), feature names."""
    if entry.builtin:
        return _builtin(entry)
    df = _read_raw(entry)
    df.columns = [str(c).strip() for c in df.columns]
    target = df[entry.target].map(lambda v: str(v).strip() if pd.notna(v) else v)
    keep = target.notna()
    df, target = df[keep], target[keep]
    y = target.isin([str(v) for v in entry.positive_values]).astype(int).to_numpy()
    parts = [_encode(df[c.name], c) for c in entry.columns]
    X = pd.concat(parts, axis=1)
    return X.to_numpy(dtype=float), y, list(X.columns)


def describe(entry: DatasetEntry) -> dict:
    """Rows, features, class balance and missingness (recorded in docs and checked by the acceptance rules)."""
    X, y, names = load(entry)
    return {"name": entry.name, "split": entry.split, "rows": int(len(y)), "features": len(names),
            "positives": int(y.sum()), "positive_rate": round(float(y.mean()), 4),
            "minority": int(min(y.sum(), len(y) - y.sum())),
            "missing_cells_pct": round(100 * float(np.isnan(X).mean()), 2),
            "duplicate_rows": int(pd.DataFrame(np.column_stack([X, y])).duplicated().sum()),
            "accepted": bool(len(y) >= 150 and min(y.sum(), len(y) - y.sum()) >= 30)}


REGISTRY: dict[str, DatasetEntry] = {}


def register(entry: DatasetEntry) -> DatasetEntry:
    REGISTRY[entry.name] = entry
    return entry


def names(split: str | None = None) -> list[str]:
    return [n for n, e in REGISTRY.items() if split is None or e.split == split]


# ---------------------------------------------------------------------------------------------------------------
# Entries. Built-in datasets keep their v1 names and loaders (data.py); all others use the generic loader.
# Per-dataset inspection (columns, drops, leakage, licence, provenance) was done by one subagent per dataset in
# master prompt v2 P3 and integrated here; summary counts are in docs/DATASETS.md.
# ---------------------------------------------------------------------------------------------------------------

register(DatasetEntry(
    name="breast_cancer", title="Breast Cancer Wisconsin (Diagnostic)", split="development",
    source="UCI ML Repository id 17 via scikit-learn load_breast_cancer (bundled CSV)",
    url="https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic", file="breast_cancer.csv",
    member=None, sha256="ff5fc1f247213db5fd49539610bcd5a98033bbd0307524fde3127251752aa073", licence="CC BY 4.0",
    provenance="Real clinical: digitised fine-needle-aspirate images, University of Wisconsin Hospitals (1995)",
    positive_class="malignant", target="diagnosis", positive_values=("malignant",), builtin=True,
    leakage_notes="30 image features of one FNA per patient; no identifiers in the scikit-learn copy."))

register(DatasetEntry(
    name="heart", title="Heart Disease (Cleveland)", split="development",
    source="UCI ML Repository id 45, processed.cleveland.data",
    url="https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
    file="processed.cleveland.data", member=None,
    sha256="a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8", licence="CC BY 4.0",
    provenance="Real clinical: Cleveland Clinic Foundation angiography cohort (Detrano et al. 1989)",
    positive_class="heart disease present (num > 0)", target="num", positive_values=("1", "2", "3", "4"), builtin=True,
    leakage_notes="Categorical codes (cp, restecg, slope, thal) kept as numeric codes as in v1; 'ca' and 'thal' have "
                  "a few '?' values imputed in-fold."))

register(DatasetEntry(
    name="pima",
    title="Pima Indians Diabetes (NIDDK; OpenML 37 'diabetes')",
    split="development",
    source="OpenML data_id 37 'diabetes' v1 (from the UCI ML Repository copy donated 1990 by V. Sigillito, JHU APL; "
           "original owner NIDDK)",
    url="https://openml.org/data/v1/download/37/diabetes.arff",
    file="diabetes.arff",
    member=None,
    sha256="4eddd5b2b64679e8888348e306520a393d6a28e1ddc9643cfb76fc5d912d6d40",
    licence="Public (OpenML dataset metadata, data_id 37, checked 2026-10-08); no further terms stated; "
            "cite Smith et al. 1988 (Proc. SCAMC, pp. 261-265)",
    provenance="Real clinical data: NIDDK study of the Pima Indian population near Phoenix, AZ; 768 women aged >= 21 "
               "(Smith et al. 1988). Research examination measurements (OGTT glucose and insulin, BP, skinfold, BMI). "
               "Not synthetic. Local MD5 3cbaa3e54586aa88cf6aacb4033e4470 equals OpenML's md5_checksum.",
    positive_class="diabetes by WHO criteria (tested_positive)",
    target="class",
    positive_values=("tested_positive",),
    reader={"format": "arff"},
    columns=(
        Column("preg"),                          # number of pregnancies; 0 is a real value
        Column("plas", zero_is_missing=True),    # 2-h OGTT plasma glucose (mg/dl); 0 = missing
        Column("pres", zero_is_missing=True),    # diastolic blood pressure (mm Hg); 0 = missing
        Column("skin", zero_is_missing=True),    # triceps skinfold thickness (mm); 0 = missing
        Column("insu", zero_is_missing=True),    # 2-h serum insulin (mu U/ml); 0 = missing (48.7%, < 50%)
        Column("mass", zero_is_missing=True),    # BMI (kg/m^2); 0 = missing
        Column("pedi"),                          # diabetes pedigree function (family history score)
        Column("age"),                           # age (years)
    ),
    dropped={},
    leakage_notes="No identifier or alternative-target columns; all 8 predictors are measured at the index "
                  "examination. The outcome uses WHO criteria (2-h post-load glucose >= 200 mg/dl), so 'plas' is "
                  "criterion-related; index-exam plas never reaches 200 (max 199), consistent with forecasting later "
                  "onset, so it is kept but expected to dominate. Zeros in plas/pres/skin/insu/mass are missing codes "
                  "(NaN, imputed in-fold); insu 48.7% missing, skin 29.6%. No exact duplicates; no subject id.",
))

register(DatasetEntry(
    name="ilpd",
    title="Indian Liver Patient Dataset (ILPD)",
    split="development",
    source="UCI Machine Learning Repository, dataset 225 (donors B. Ramana, N. Venkateswarlu; donated 2012-05-20; "
           "DOI 10.24432/C5D02C)",
    url="https://archive.ics.uci.edu/static/public/225/ilpd+indian+liver+patient+dataset.zip",
    file="ilpd.zip",
    member="Indian Liver Patient Dataset (ILPD).csv",
    sha256="60e18fbfe7f84daf58c178ea280ba5fe8db7e2507aabce01b57425b3b822cf0b",
    licence="CC BY 4.0",
    provenance="Real clinical records: 583 patients from north-east Andhra Pradesh, India (UCI page); routine liver-"
               "function tests plus age and sex; Age capped at 90. The UCI page says 584 records and no missing "
               "values, but the file has 583 rows and 4 blank A/G Ratio cells.",
    positive_class="liver patient (Selector = 1)",
    target="Selector",
    positive_values=("1",),
    reader={"format": "csv", "header": None,
            "names": ["Age", "Gender", "TB", "DB", "Alkphos", "Sgpt", "Sgot", "TP", "ALB", "A/G Ratio", "Selector"],
            "dtype": {"Selector": str}},
    columns=(
        Column("Age"),
        Column("Gender", "binary", ("Female", "Male")),
        Column("TB"),
        Column("DB"),
        Column("Alkphos"),
        Column("Sgpt"),
        Column("Sgot"),
        Column("TP"),
        Column("ALB"),
        Column("A/G Ratio"),
    ),
    dropped={},
    leakage_notes="No identifier or outcome columns. The Selector label was likely assigned using these same liver "
                  "tests (incorporation bias), so discrimination is optimistic versus screening; hospital case-control-"
                  "like sample (71% positive). 13 exact duplicate rows (adjacent pairs, same label): the benchmark keeps "
                  "identical rows in the same fold. A/G Ratio ~ ALB/(TP-ALB) is redundant. 3 rows have DB > TB "
                  "(implausible, kept as-is).",
))

register(DatasetEntry(
    name="heart_failure",
    title="Heart Failure Clinical Records",
    split="confirmation",
    source="UCI Machine Learning Repository, dataset 519 (doi:10.24432/C5Z89R); Chicco & Jurman 2020, BMC Med Inform "
           "Decis Mak 20:16; original data Ahmad et al. 2017, PLoS ONE 12(7):e0181001",
    url="https://archive.ics.uci.edu/static/public/519/heart+failure+clinical+records.zip",
    file="heart_failure.zip",
    member="heart_failure_clinical_records_dataset.csv",
    sha256="f0739603e2f9573ffc7d509573cbf9bcb4cc889e4eea0f35a75bec68fc9163d7",
    licence="CC BY 4.0 (UCI dataset page)",
    provenance="Real clinical: records of 299 heart-failure patients (LVSD, NYHA III/IV), Faisalabad Institute of "
               "Cardiology and Allied Hospital, Pakistan, Apr-Dec 2015 (Chicco & Jurman 2020; file matches sex split, "
               "age range and follow-up range). 25 platelets values equal 263358.03 = mean of the other values "
               "(upstream mean imputation): read as missing and imputed in-fold.",
    positive_class="died during the follow-up period (DEATH_EVENT = 1)",
    target="DEATH_EVENT",
    positive_values=("1",),
    reader={"format": "csv", "na_values": {"platelets": ["263358.03"]}},
    columns=(
        Column("age"),
        Column("anaemia", "binary", ("0", "1")),
        Column("creatinine_phosphokinase"),
        Column("diabetes", "binary", ("0", "1")),
        Column("ejection_fraction"),
        Column("high_blood_pressure", "binary", ("0", "1")),
        Column("platelets"),
        Column("serum_creatinine"),
        Column("serum_sodium"),
        Column("sex", "binary", ("0", "1")),  # 1 = man
        Column("smoking", "binary", ("0", "1")),
    ),
    dropped={"time": "outcome leakage: follow-up period in days, not known at baseline and ended by the outcome "
                     "(median 44.5 vs 172 days, r = -0.53 with DEATH_EVENT)"},
    leakage_notes="`time` dropped. The file is sorted by `time`, so row order correlates with the label: folds are "
                  "shuffled and the row index is never a feature. Label = death within a variable 4-285-day "
                  "follow-up (censored survivors labelled 0: label noise). Blood-value timing undocumented; treated as "
                  "baseline.",
))

register(DatasetEntry(
    name="parkinsons",
    title="Parkinson's disease voice measurements (Little et al.)",
    split="confirmation",
    source="UCI Machine Learning Repository, id 174 (doi:10.24432/C59C74)",
    url="https://archive.ics.uci.edu/static/public/174/parkinsons.zip",
    file="parkinsons.zip",
    member="parkinsons.data",
    sha256="9baccfbcdac15d6d9347b37c2a352fb31d65c52e367df5a47d7543a55c75b0ab",
    licence="CC BY 4.0 (UCI page); cite Little et al. 2007 BioMed Eng OnLine 6:23 and Little et al. 2009 IEEE TBME",
    provenance="Real clinical: sustained-phonation recordings (National Centre for Voice and Speech, Denver), dysphonia "
               "features by M. Little (Oxford); donated 2008. File: 195 recordings from 32 subject codes (24 PD, 8 "
               "healthy); parkinsons.names says 31 people.",
    positive_class="Parkinson's disease (status = 1)",
    target="status",
    positive_values=("1",),
    reader={"format": "csv"},
    columns=tuple(Column(c) for c in (
        "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)", "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ",
        "Jitter:DDP", "MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5", "MDVP:APQ", "Shimmer:DDA",
        "NHR", "HNR", "RPDE", "DFA", "spread1", "spread2", "D2", "PPE")),
    dropped={"name": "identifier (subject code + recording number, e.g. phon_R01_S01_1); used only for the group key"},
    leakage_notes="Repeated measures: 195 recordings from 32 subjects (6-7 each); status constant within subject. "
                  "Folds are grouped by subject (StratifiedGroupKFold) via group_regex on `name`. Jitter:DDP = 3 x "
                  "MDVP:RAP and Shimmer:DDA = 3 x Shimmer:APQ3 (collinear pairs, kept as published).",
    group_column="name",
    group_regex=r"^phon_R01_(S\d{2})_\d+$",
))

register(DatasetEntry(
    name="early_diabetes",
    title="Early Stage Diabetes Risk Prediction",
    split="confirmation",
    source="UCI Machine Learning Repository #529 (doi:10.24432/C5VG8H); Islam, Ferdousi, Rahman & Bushra",
    url="https://archive.ics.uci.edu/static/public/529/early+stage+diabetes+risk+prediction+dataset.zip",
    file="early_diabetes.zip",
    member="diabetes_data_upload.csv",
    sha256="67594c0f11257688b57493798e70737b7156ba37a2e6ac75507ae3a35221a388",
    licence="CC BY 4.0",
    provenance="Real patient survey: questionnaires from patients of Sylhet Diabetes Hospital, Bangladesh, approved by a "
               "doctor (UCI page). Hospital-based, case-control-like sample. 269/520 rows are exact duplicates of an "
               "earlier row (251 unique, no label conflicts); kept as published, grouped in CV.",
    positive_class="diabetes (class == Positive)",
    target="class",
    positive_values=("Positive",),
    reader={"format": "csv"},
    columns=(Column("Age"), Column("Gender", "binary", ("Female", "Male")),
             *(Column(c, "binary", ("No", "Yes")) for c in (
                 "Polyuria", "Polydipsia", "sudden weight loss", "weakness", "Polyphagia", "Genital thrush",
                 "visual blurring", "Itching", "Irritability", "delayed healing", "partial paresis",
                 "muscle stiffness", "Alopecia", "Obesity"))),
    dropped={},
    leakage_notes="No identifier or post-diagnosis column. 269/520 exact duplicate rows: the benchmark keeps identical "
                  "rows in the same fold. Respondents were diabetes-hospital patients, so symptom recall may reflect "
                  "known status; Polyuria/Polydipsia are near-diagnostic. Obesity is a Yes/No judgement, not BMI.",
))

register(DatasetEntry(
    name="mammographic",
    title="Mammographic Mass (UCI 161)",
    split="confirmation",
    source="UCI Machine Learning Repository, id 161 (doi:10.24432/C53K6Z)",
    url="https://archive.ics.uci.edu/static/public/161/mammographic+mass.zip",
    file="mammographic.zip",
    member="mammographic_masses.data",
    sha256="4c5158166aa7f1503e14d95be4c95fe66a734474f614441ede226314b93db6e7",
    licence="CC BY 4.0 (UCI dataset page); cite Elter (2007), doi:10.24432/C53K6Z",
    provenance="Real clinical: 961 masses on full-field digital mammograms, Institute of Radiology, University "
               "Erlangen-Nuremberg, 2003-2006; donated 2007 by M. Elter (Elter et al., Med. Phys. 34:4164, 2007).",
    positive_class="malignant mass (severity = 1)",
    target="severity",
    positive_values=("1",),
    reader={"format": "csv", "header": None, "names": ["bi_rads", "age", "shape", "margin", "density", "severity"],
            "na_values": ["?"], "dtype": str},
    columns=(
        Column("age"),
        Column("shape", "nominal", ("1", "2", "3", "4")),         # round, oval, lobular, irregular
        Column("margin", "nominal", ("1", "2", "3", "4", "5")),   # circumscribed .. spiculated
        Column("density", "ordinal", ("4", "3", "2", "1")),       # fat-containing < low < iso < high
    ),
    dropped={"bi_rads": "outcome leakage: radiologists' double-read BI-RADS final assessment (UCI: 'non-predictive'), "
                        "a malignancy judgement summarising the other descriptors; code 6 = biopsy-proven cancer; "
                        "invalid codes 0 and 55 present"},
    leakage_notes="BI-RADS dropped. Shape, margin and density are BI-RADS descriptors read before biopsy. Population: "
                  "masses already referred to biopsy/follow-up, not screening. 353 duplicate (X, y) rows (542 distinct "
                  "patterns): identical rows kept in the same fold.",
))

register(DatasetEntry(
    name="dtc_recurrence",
    title="Differentiated Thyroid Cancer Recurrence (UCI 915)",
    split="confirmation",
    source="UCI Machine Learning Repository, dataset 915 (DOI 10.24432/C5632J)",
    url="https://archive.ics.uci.edu/static/public/915/differentiated+thyroid+cancer+recurrence.zip",
    file="dtc_recurrence.zip",
    member="Thyroid_Diff.csv",
    sha256="66007e38af856f439fc5e8d1bfd49db4e3cd963723f0b4d363e61f4bdd7bab11",
    licence="CC BY 4.0 (UCI page); credit Borzooei & Tarokhian, DOI 10.24432/C5632J",
    provenance="Real clinical: retrospective cohort of 383 patients with well-differentiated thyroid cancer followed >= "
               "10 years, Hamadan University of Medical Sciences, Iran (Borzooei et al. 2023, "
               "doi:10.1007/s00405-023-08299-w).",
    positive_class="recurrence of differentiated thyroid cancer (Recurred = Yes)",
    target="Recurred",
    positive_values=("Yes",),
    reader={"format": "csv"},
    columns=(
        Column("Age"),
        Column("Gender", "binary", ("F", "M")),
        Column("Smoking", "binary", ("No", "Yes")),
        Column("Hx Smoking", "binary", ("No", "Yes")),
        Column("Hx Radiothreapy", "binary", ("No", "Yes")),
        Column("Thyroid Function", "nominal", ("Euthyroid", "Clinical Hyperthyroidism", "Subclinical Hyperthyroidism",
                                               "Clinical Hypothyroidism", "Subclinical Hypothyroidism")),
        Column("Physical Examination", "nominal", ("Normal", "Single nodular goiter-left", "Single nodular goiter-right",
                                                   "Multinodular goiter", "Diffuse goiter")),
        Column("Adenopathy", "nominal", ("No", "Right", "Left", "Bilateral", "Posterior", "Extensive")),
        Column("Pathology", "nominal", ("Papillary", "Micropapillary", "Follicular", "Hurthel cell")),
        Column("Focality", "binary", ("Uni-Focal", "Multi-Focal")),
        Column("Risk", "ordinal", ("Low", "Intermediate", "High")),
        Column("T", "ordinal", ("T1a", "T1b", "T2", "T3a", "T3b", "T4a", "T4b")),
        Column("N", "ordinal", ("N0", "N1a", "N1b")),
        Column("M", "ordinal", ("M0", "M1")),
        Column("Stage", "ordinal", ("I", "II", "III", "IVA", "IVB")),
    ),
    dropped={"Response": "outcome leakage: ATA response-to-therapy category assessed during follow-up, not at diagnosis; "
                         "overlaps the target (Structural Incomplete 89/91 recurred, Excellent 1/208)"},
    leakage_notes="Response dropped. Kept columns are available by the end of initial diagnosis/treatment (post-operative "
                  "prognosis task, not screening). Risk and Stage are composites of other kept columns. Near-"
                  "deterministic categories: Risk=High 32/32, M1 18/18 recurred. 26 duplicate encoded rows (one "
                  "profile carries both labels): identical rows kept in the same fold.",
))

register(DatasetEntry(
    name="ckd",
    title="Chronic Kidney Disease (UCI 336)",
    split="confirmation",
    source="UCI Machine Learning Repository, dataset 336 (Rubini, Soundarapandian & Eswaran, 2015; DOI 10.24432/C5G020); "
           "UCI's processed CSV export (the zip holds a .rar)",
    url="https://archive.ics.uci.edu/static/public/336/data.csv",
    file="ckd.csv",
    member=None,
    sha256="0eeea8d17f5ad8792d854999d6ddf1602ec4e116616f6ccdfdaef0ba8109e694",
    licence="CC BY 4.0 (UCI dataset page)",
    provenance="Real clinical: 400 patient records (24 clinical/lab attributes) collected from a hospital over ~2 months, "
               "donated July 2015. Case-control style (250 ckd / 150 notckd), not a screening cohort.",
    positive_class="ckd (chronic kidney disease)",
    target="class",
    positive_values=("ckd",),
    reader={"format": "csv", "na_values": ["NaN", "?", ""]},
    columns=(
        Column("age"), Column("bp"),
        Column("sg"), Column("al"), Column("su"),  # equally spaced dipstick codes; zeros are real negative results
        Column("rbc", "binary", ("normal", "abnormal")),
        Column("pc", "binary", ("normal", "abnormal")),
        Column("pcc", "binary", ("notpresent", "present")),
        Column("ba", "binary", ("notpresent", "present")),
        Column("bgr"), Column("bu"), Column("sc"), Column("sod"), Column("pot"), Column("hemo"), Column("pcv"),
        Column("wbcc"), Column("rbcc"),
        Column("htn", "binary", ("no", "yes")),
        Column("dm", "binary", ("no", "yes")),
        Column("cad", "binary", ("no", "yes")),
        Column("appet", "binary", ("good", "poor")),
        Column("pe", "binary", ("no", "yes")),
        Column("ane", "binary", ("no", "yes")),
    ),
    dropped={},
    leakage_notes="No column derived from the label. sc and al are KDIGO diagnostic criteria (kept). Case-control "
                  "design: every notckd row is normal on every attribute, so classes are nearly separable (hemo alone "
                  "~0.93 accuracy): expect AUC near 1 and a ceiling effect. Missingness depends on class (impute in-fold, "
                  "no missing indicators). Implausible values kept as recorded. Stray tabs handled by strip().",
))

register(DatasetEntry(
    name="thyroid_sick",
    title="Thyroid disease: sick euthyroid vs negative (Garvan Institute, OpenML 38 'sick')",
    split="confirmation",
    source="OpenML data_id 38 'sick' v1 (UCI Thyroid Disease id 102; Garvan Institute, Sydney / J. R. Quinlan)",
    url="https://openml.org/data/v1/download/38/sick.arff",
    file="sick.arff",
    member=None,
    sha256="85c39615380ca4c05c17a53c3faad9523924958d1e9bc5af0dcbefc6339e7800",
    licence="CC BY 4.0 (UCI Thyroid Disease, id 102, DOI 10.24432/C5D010); OpenML data_id 38 lists 'Public'; "
            "cite Quinlan (1986)",
    provenance="Real clinical thyroid-function referrals, Garvan Institute (Sydney) via J. R. Quinlan, 1987. Raw MD5 "
               "ee5cb4b7f41a5f44b0cd234f675ab492 equals OpenML's md5_checksum.",
    positive_class="sick (sick euthyroid syndrome)",
    target="Class",
    positive_values=("sick",),
    reader={"format": "arff"},
    columns=(
        Column("age", max_value=120),  # one data-entry error (455) -> missing
        Column("sex", "binary", ("F", "M")),
        *(Column(c, "binary", ("f", "t")) for c in (
            "on_thyroxine", "query_on_thyroxine", "on_antithyroid_medication", "sick", "pregnant", "thyroid_surgery",
            "I131_treatment", "query_hypothyroid", "query_hyperthyroid", "lithium", "goitre", "tumor", "psych")),
        Column("TSH"), Column("T3"), Column("TT4"), Column("T4U"), Column("FTI"),
        Column("referral_source", "nominal", ("SVHC", "other", "SVI", "STMW", "SVHD")),
    ),
    dropped={
        "TBG": ">50% missing: 100% missing (never measured)",
        "TBG_measured": "constant: 'f' in all 3772 rows",
        "hypopituitary": "near-constant: 't' in 1 of 3772 rows",
        **{f"{lab}_measured": "duplicates the lab value's missingness; test-ordering flag encodes clinician suspicion "
                              "and the work-up behind the label" for lab in ("TSH", "T3", "TT4", "T4U", "FTI")},
    },
    leakage_notes="The label (sick euthyroid) was assigned from this same thyroid panel plus clinical context: expect "
                  "high AUC. *_measured flags dropped, but missingness of kept labs still differs by class (T3 missing "
                  "21.6% of negatives vs 1.3% of positives); imputed in-fold without indicators. The 'sick' input is a "
                  "referral-form flag of non-thyroidal illness, not the label. referral_source acts as a site proxy. "
                  "61 exact duplicate records (all negative) kept in the same fold. 6.1% positive.",
))

register(DatasetEntry(
    name="cervical",
    title="Cervical Cancer (Risk Factors)",
    split="confirmation",
    source="UCI Machine Learning Repository, dataset 383 (K. Fernandes, J. S. Cardoso, J. Fernandes; 2017; "
           "DOI 10.24432/C5Z310)",
    url="https://archive.ics.uci.edu/static/public/383/cervical+cancer+risk+factors.zip",
    file="cervical.zip",
    member="risk_factors_cervical_cancer.csv",
    sha256="d86f38fbb1f4c40c22c240127875d7a83a2f96238f7ed5a388e2277cfb79a742",
    licence="CC BY 4.0",
    provenance="Real clinical/survey data: 858 patients at Hospital Universitario de Caracas, Venezuela (Fernandes, "
               "Cardoso & Fernandes, IbPRIA 2017); '?' marks questions patients declined to answer.",
    positive_class="positive biopsy (Biopsy = 1)",
    target="Biopsy",
    positive_values=("1",),
    reader={"format": "csv", "na_values": ["?"]},
    columns=(
        Column("Age"), Column("Number of sexual partners"), Column("First sexual intercourse"),
        Column("Num of pregnancies"),
        Column("Smokes", "binary", ("0.0", "1.0")), Column("Smokes (years)"), Column("Smokes (packs/year)"),
        Column("Hormonal Contraceptives", "binary", ("0.0", "1.0")), Column("Hormonal Contraceptives (years)"),
        Column("IUD", "binary", ("0.0", "1.0")), Column("IUD (years)"),
        Column("STDs", "binary", ("0.0", "1.0")), Column("STDs (number)"),
        *(Column(c, "binary", ("0.0", "1.0")) for c in (
            "STDs:condylomatosis", "STDs:vaginal condylomatosis", "STDs:vulvo-perineal condylomatosis",
            "STDs:syphilis", "STDs:pelvic inflammatory disease", "STDs:genital herpes", "STDs:molluscum contagiosum",
            "STDs:HIV", "STDs:Hepatitis B", "STDs:HPV")),
        Column("STDs: Number of diagnosis"),
        *(Column(c, "binary", ("0", "1")) for c in ("Dx:Cancer", "Dx:CIN", "Dx:HPV", "Dx")),
    ),
    dropped={
        "Hinselmann": "alternative target / outcome leakage: colposcopy result from the same work-up as the biopsy",
        "Schiller": "alternative target / outcome leakage: Schiller test result from the same work-up",
        "Citology": "alternative target / outcome leakage: cytology result from the same work-up",
        "STDs: Time since first diagnosis": ">50% missing (91.7%)",
        "STDs: Time since last diagnosis": ">50% missing (91.7%)",
        "STDs:cervical condylomatosis": "constant (0 in all non-missing rows)",
        "STDs:AIDS": "constant (0 in all non-missing rows)",
    },
    leakage_notes="Target is Biopsy only. Dx:* kept: prior diagnoses from the medical history, known at the screening "
                  "visit (Dx:Cancer = 1 in 18 rows, 6 biopsy-positive). Missingness is outcome-associated (Hormonal "
                  "Contraceptives '?' in 13.4% of negatives vs 0% of positives): imputed in-fold without indicators. "
                  "Redundant indicator/count pairs kept for in-fold selection. Donor-imputed constants kept as-is. "
                  "26 duplicate encoded rows kept in the same fold. 6.4% positive.",
))

register(DatasetEntry(
    name="hepatitis",
    title="Hepatitis (UCI id 46): survival of hepatitis patients",
    split="confirmation",
    source="UCI Machine Learning Repository, dataset 46 (donor G. Gong, CMU, via B. Cestnik; 1988; DOI 10.24432/C5Q59J)",
    url="https://archive.ics.uci.edu/static/public/46/hepatitis.zip",
    file="hepatitis.zip",
    member="hepatitis.data",
    sha256="8573c2898714fb32ef8162291dcabd483a1ba9701123cab262f5acace3112d87",
    licence="CC BY 4.0",
    provenance="Real clinical records: 155 hepatitis patients with vital status (DIE 32 / LIVE 123), history, "
               "examination and liver-panel tests (Diaconis & Efron 1983; Cestnik et al. 1987). No identifiers.",
    positive_class="DIE (Class = 1)",
    target="Class",
    positive_values=("1",),
    reader={"format": "csv", "header": None, "na_values": ["?"], "dtype": str,
            "names": ["Class", "AGE", "SEX", "STEROID", "ANTIVIRALS", "FATIGUE", "MALAISE", "ANOREXIA", "LIVER_BIG",
                      "LIVER_FIRM", "SPLEEN_PALPABLE", "SPIDERS", "ASCITES", "VARICES", "BILIRUBIN", "ALK_PHOSPHATE",
                      "SGOT", "ALBUMIN", "PROTIME", "HISTOLOGY"]},
    columns=(
        Column("AGE"),
        Column("SEX", "binary", ("1", "2")),  # 1 = male -> 0
        *(Column(c, "binary", ("2", "1")) for c in (  # yes/no items: data fit 1 = yes (see notes)
            "STEROID", "ANTIVIRALS", "FATIGUE", "MALAISE", "ANOREXIA", "LIVER_BIG", "LIVER_FIRM", "SPLEEN_PALPABLE",
            "SPIDERS", "ASCITES", "VARICES")),
        *(Column(c, zero_is_missing=True) for c in ("BILIRUBIN", "ALK_PHOSPHATE", "SGOT", "ALBUMIN", "PROTIME")),
        Column("HISTOLOGY", "binary", ("2", "1")),
    ),
    dropped={},
    leakage_notes="Yes/no codes are undocumented; the data fit 1 = yes (ASCITES raw 1: 14/20 died vs 17/130). Turney's "
                  "costs/hepatitis.delay marks history/exam items and HISTOLOGY 'immediate', labs 'delayed'; nothing is "
                  "documented as recorded after death. HISTOLOGY may be a care-process proxy. STEROID/ANTIVIRALS are "
                  "treatments (confounding by indication). PROTIME 43.9% missing (< 50%, kept). Minority 32: wide "
                  "intervals expected.",
))

register(DatasetEntry(
    name="statlog_heart",
    title="Statlog (Heart)",
    split="sanity",
    source="UCI Machine Learning Repository, dataset 145 (ESPRIT StatLog project), DOI 10.24432/C57303",
    url="https://archive.ics.uci.edu/static/public/145/statlog+heart.zip",
    file="statlog_heart.zip",
    member="heart.dat",
    sha256="04e44018af4f4b32008029fbfb1079e112d3b372bb032dd1ae361c74d7528b2c",
    licence="CC BY 4.0 (UCI dataset page)",
    provenance="Real clinical, but NOT independent: all 270 rows equal a Cleveland row on all 13 features with the same "
               "binary label (checked against processed.cleveland.data); a subset of the complete Cleveland rows.",
    positive_class="heart disease present (class 2)",
    target="class",
    positive_values=("2",),
    reader={"format": "csv", "sep": r"\s+", "header": None, "dtype": str, "na_values": ["?"],
            "names": ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang",
                      "oldpeak", "slope", "ca", "thal", "class"]},
    columns=(
        Column("age"),
        Column("sex", "binary", ("0.0", "1.0")),
        Column("cp", "nominal", ("1.0", "2.0", "3.0", "4.0")),
        Column("trestbps", zero_is_missing=True),
        Column("chol", zero_is_missing=True),
        Column("fbs", "binary", ("0.0", "1.0")),
        Column("restecg", "nominal", ("0.0", "1.0", "2.0")),
        Column("thalach"),
        Column("exang", "binary", ("0.0", "1.0")),
        Column("oldpeak"),
        Column("slope", "ordinal", ("1.0", "2.0", "3.0")),
        Column("ca"),
        Column("thal", "nominal", ("3.0", "6.0", "7.0")),
    ),
    dropped={},
    leakage_notes="Complete overlap with Cleveland: pipeline/reproducibility sanity check only, never external "
                  "validation, never in the statistics.",
))


def write_docs(path: Path) -> None:
    """docs/DATASETS.md generated from the registry (counts computed from the raw files, never typed by hand)."""
    lines = ["# Datasets (generated by `python -m backend.ml.quantum.registry docs`; do not edit by hand)", "",
             "Raw files are downloaded to data/raw/ (git-ignored) and verified by SHA-256. Acceptance rules: "
             "docs/KAGGLE_DATASETS.md. Split: docs/PREREGISTRATION.md.", "",
             "| Dataset | Split | Rows | Encoded features | Positives (rate) | Minority | Missing cells | "
             "Duplicate rows | Licence |", "|---|---|---|---|---|---|---|---|---|"]
    details = []
    for n, e in REGISTRY.items():
        d = describe(e)
        lines.append(f"| {e.title} (`{n}`) | {e.split} | {d['rows']} | {d['features']} | {d['positives']} "
                     f"({d['positive_rate']:.1%}) | {d['minority']} | {d['missing_cells_pct']}% | {d['duplicate_rows']} "
                     f"| {e.licence.split(';')[0].split('(')[0].strip()} |")
        dropped = "; ".join(f"`{c}`: {r}" for c, r in e.dropped.items()) or "none"
        details += [f"## {e.title} (`{n}`)", "", f"- Source: {e.source} ({e.url})", f"- SHA-256: `{e.sha256}`",
                    f"- Licence: {e.licence}", f"- Provenance: {e.provenance}",
                    f"- Target: `{e.target}` in {list(e.positive_values)} = {e.positive_class}",
                    f"- Dropped columns: {dropped}", f"- Leakage notes: {e.leakage_notes}",
                    *([f"- Group-aware folds: `{e.group_column}` / `{e.group_regex}`"] if e.group_column else []), ""]
    lines += ["", "Not run: Kaggle-only candidates (Stroke, Framingham, Cardiovascular 70k, Lung cancer survey): "
              "Kaggle credentials not present. Rejected: Breast Cancer Coimbra (116 rows < 150).", "", *details]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cmd", choices=["fetch", "summary", "docs"])
    parser.add_argument("--name", default=None)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "DATASETS.md")
    args = parser.parse_args(argv)
    if args.cmd == "docs":
        write_docs(args.out)
        return
    names = [args.name] if args.name else [n for n, e in REGISTRY.items() if not e.builtin]
    for n in names:
        e = REGISTRY[n]
        if args.cmd == "fetch":
            p = fetch(e)
            print(f"{n:16s} {sha256(p)}  {p.stat().st_size:>8d} bytes")
        else:
            print(json.dumps(describe(e)))


if __name__ == "__main__":
    main()
