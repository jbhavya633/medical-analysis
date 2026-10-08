"""Registry loaders, each tested on a tiny fixture in the raw file's own format (never on the downloaded data).

Per-dataset fixtures were written by the per-dataset inspection subagents (master prompt v2 P3) and integrated here.
"""

import dataclasses
import io
import zipfile

import numpy as np
import pytest

from backend.ml.quantum import registry


def _entry(name):
    return dataclasses.replace(registry.REGISTRY[name], sha256=None)


def test_pima_loader(tmp_path, monkeypatch):
    arff = (
        "% tiny Pima fixture (same layout as OpenML 37)\n"
        "@relation pima_diabetes\n"
        "@attribute 'preg' real\n@attribute 'plas' real\n@attribute 'pres' real\n@attribute 'skin' real\n"
        "@attribute 'insu' real\n@attribute 'mass' real\n@attribute 'pedi' real\n@attribute 'age' real\n"
        "@attribute 'class' { tested_negative, tested_positive}\n"
        "@data\n"
        "6,148,72,35,0,33.6,0.627,50,tested_positive\n"
        "1,85,66,29,0,26.6,0.351,31,tested_negative\n"
        "0,0,70,25,120,30.1,0.400,28,tested_negative\n"
        "8,183,64,0,0,23.3,0.672,32,tested_positive\n"
        "1,89,66,23,94,28.1,0.167,21,tested_negative\n"
        "0,137,40,35,168,43.1,2.288,33,tested_positive\n"
    )
    (tmp_path / "pima").mkdir()
    (tmp_path / "pima" / "diabetes.arff").write_text(arff, encoding="utf-8")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("pima"))
    assert X.shape == (6, 8)
    assert names == ["preg", "plas", "pres", "skin", "insu", "mass", "pedi", "age"]
    assert y.tolist() == [1, 0, 0, 1, 0, 1]
    assert np.isnan(X[2, names.index("plas")])             # zero glucose -> missing
    assert np.isnan(X[0, names.index("insu")])             # zero insulin -> missing
    assert np.isnan(X[3, names.index("skin")])             # zero skinfold -> missing
    assert X[2, names.index("preg")] == 0.0                # zero pregnancies is a real value
    assert int(np.isnan(X).sum()) == 5


def test_ilpd_loader(tmp_path, monkeypatch):
    rows = ["60,Female,0.8,0.2,190,18,22,6.9,3.4,0.97,1",
            "48,Male,7.5,3.9,520,88,140,6.1,2.6,0.74,1",
            "33,Male,2.1,1.0,310,45,60,7.0,3.0,,1",  # blank A/G Ratio, as in the raw file
            "41,Female,0.7,0.2,170,20,25,7.2,3.8,1.12,2",
            "29,Male,0.9,0.2,160,22,19,7.6,4.1,1.17,2"]
    (tmp_path / "ilpd").mkdir()
    with zipfile.ZipFile(tmp_path / "ilpd" / "ilpd.zip", "w") as z:
        z.writestr("Indian Liver Patient Dataset (ILPD).csv", "\r\n".join(rows) + "\r\n")  # no header, CRLF
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("ilpd"))
    assert names == ["Age", "Gender", "TB", "DB", "Alkphos", "Sgpt", "Sgot", "TP", "ALB", "A/G Ratio"]
    assert X.shape == (5, 10)
    assert y.tolist() == [1, 1, 1, 0, 0]
    assert X[:, names.index("Gender")].tolist() == [0.0, 1.0, 1.0, 0.0, 1.0]
    assert np.isnan(X).sum() == 1 and np.isnan(X[2, names.index("A/G Ratio")])


def _zip(tmp_path, name, file, member, text):
    (tmp_path / name).mkdir()
    with zipfile.ZipFile(tmp_path / name / file, "w") as z:
        z.writestr(member, text)


def test_heart_failure_loader(tmp_path, monkeypatch):
    csv = ("age,anaemia,creatinine_phosphokinase,diabetes,ejection_fraction,high_blood_pressure,platelets,"
           "serum_creatinine,serum_sodium,sex,smoking,time,DEATH_EVENT\n"
           "75,0,582,0,20,1,265000,1.9,130,1,0,4,1\n55,0,7861,0,38,0,263358.03,1.1,136,1,0,6,1\n"
           "65,1,146,1,20,0,162000,1.3,129,0,1,7,1\n60.667,1,151,1,40,1,201000,1,136,0,0,172,0\n"
           "50,0,196,0,45,0,395000,1.6,136,1,1,285,0\n45,1,2413,0,38,0,140000,1.4,140,0,1,280,0\n")
    _zip(tmp_path, "heart_failure", "heart_failure.zip", "heart_failure_clinical_records_dataset.csv", csv)
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("heart_failure"))
    assert X.shape == (6, 11) and y.tolist() == [1, 1, 1, 0, 0, 0]
    assert "time" not in names
    assert X[:, names.index("anaemia")].tolist() == [0.0, 0.0, 1.0, 1.0, 0.0, 1.0]
    p = X[:, names.index("platelets")]
    assert np.isnan(p[1]) and p[0] == 265000.0  # upstream mean-imputation value read as missing


def test_parkinsons_loader_and_groups(tmp_path, monkeypatch):
    header = ("name,MDVP:Fo(Hz),MDVP:Fhi(Hz),MDVP:Flo(Hz),MDVP:Jitter(%),MDVP:Jitter(Abs),MDVP:RAP,MDVP:PPQ,"
              "Jitter:DDP,MDVP:Shimmer,MDVP:Shimmer(dB),Shimmer:APQ3,Shimmer:APQ5,MDVP:APQ,Shimmer:DDA,NHR,HNR,"
              "status,RPDE,DFA,spread1,spread2,D2,PPE")
    recs = [("phon_R01_S01_1", 1), ("phon_R01_S01_2", 1), ("phon_R01_S01_3", 1),
            ("phon_R01_S07_1", 0), ("phon_R01_S07_2", 0), ("phon_R01_S07_3", 0)]
    lines = [header]
    for i, (rec, status) in enumerate(recs):
        feats = [f"{100.0 + 10 * i + k:.5f}" for k in range(22)]
        lines.append(",".join([rec, *feats[:16], str(status), *feats[16:]]))
    _zip(tmp_path, "parkinsons", "parkinsons.zip", "parkinsons.data", "\r\n".join(lines) + "\r\n")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    entry = _entry("parkinsons")
    X, y, names = registry.load(entry)
    assert X.shape == (6, 22) and y.tolist() == [1, 1, 1, 0, 0, 0]
    assert "name" not in names and names[16] == "RPDE" and X[1, 16] == 126.0
    assert registry.groups(entry).tolist() == ["S01"] * 3 + ["S07"] * 3


def test_early_diabetes_loader(tmp_path, monkeypatch):
    header = ("Age,Gender,Polyuria,Polydipsia,sudden weight loss,weakness,Polyphagia,Genital thrush,"
              "visual blurring,Itching,Irritability,delayed healing,partial paresis,muscle stiffness,"
              "Alopecia,Obesity,class")
    rows = ["40,Male,No,Yes,No,Yes,No,No,No,Yes,No,Yes,No,Yes,Yes,Yes,Positive",
            "58,Female,Yes,Yes,Yes,Yes,Yes,Yes,Yes,Yes,Yes,Yes,Yes,Yes,Yes,Yes,Positive",
            "30,Male,No,No,No,No,No,No,No,No,No,No,No,No,No,No,Negative",
            "30,Male,No,No,No,No,No,No,No,No,No,No,No,No,No,No,Negative",
            "47,Female,Yes,No,No,No,No,No,No,No,No,No,No,No,No,No,Negative"]
    _zip(tmp_path, "early_diabetes", "early_diabetes.zip", "diabetes_data_upload.csv",
         "\r\n".join([header, *rows]) + "\r\n")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("early_diabetes"))
    assert X.shape == (5, 16) and y.tolist() == [1, 1, 0, 0, 0] and not np.isnan(X).any()
    assert X[:, 1].tolist() == [1.0, 0.0, 1.0, 1.0, 0.0]
    assert X[0, 2:].tolist() == [0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1]


def test_mammographic_loader(tmp_path, monkeypatch):
    rows = ["5,67,3,5,3,1", "4,43,1,1,?,1", "4,28,1,1,3,0", "4,70,?,?,3,0", "2,52,2,4,2,0", "55,46,4,3,1,1"]
    _zip(tmp_path, "mammographic", "mammographic.zip", "mammographic_masses.data", "\r\n".join(rows) + "\r\n")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("mammographic"))
    assert X.shape == (6, 11) and "bi_rads" not in names
    assert y.tolist() == [1, 1, 0, 0, 0, 1]
    assert X[0, 1:5].tolist() == [0, 0, 1, 0] and np.isnan(X[3, 1:5]).all()
    density = X[:, 10]
    assert np.isnan(density[1]) and density[[0, 4, 5]].tolist() == [1, 2, 3]


def test_dtc_recurrence_loader(tmp_path, monkeypatch):
    header = ("Age,Gender,Smoking,Hx Smoking,Hx Radiothreapy,Thyroid Function,Physical Examination,Adenopathy,"
              "Pathology,Focality,Risk,T,N,M,Stage,Response,Recurred")
    rows = ["27,F,No,No,No,Euthyroid,Single nodular goiter-left,No,Micropapillary,Uni-Focal,Low,T1a,N0,M0,I,Excellent,No",
            "45,M,Yes,No,No,Clinical Hyperthyroidism,Single nodular goiter-right,Right,Papillary,Multi-Focal,"
            "Intermediate,T3a,N1b,M0,I,Structural Incomplete,Yes",
            "67,M,Yes,Yes,Yes,Euthyroid,Normal,Extensive,Hurthel cell,Multi-Focal,High,T4b,N1a,M1,IVB,"
            "Structural Incomplete,Yes"]
    _zip(tmp_path, "dtc_recurrence", "dtc_recurrence.zip", "Thyroid_Diff.csv", "\r\n".join([header, *rows]) + "\r\n")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("dtc_recurrence"))
    assert X.shape == (3, 31) and y.tolist() == [0, 1, 1]
    assert not any(n.startswith("Response") for n in names)
    assert X[:, names.index("T")].tolist() == [0.0, 3.0, 6.0] and X[:, names.index("Stage")].tolist() == [0, 0, 4]
    assert X[2, names.index("Pathology=Hurthel cell")] == 1.0


def test_ckd_loader(tmp_path, monkeypatch):
    header = "age,bp,sg,al,su,rbc,pc,pcc,ba,bgr,bu,sc,sod,pot,hemo,pcv,wbcc,rbcc,htn,dm,cad,appet,pe,ane,class"
    rows = [
        "48,80,1.02,1,0,NaN,normal,notpresent,notpresent,121,36,1.2,NaN,NaN,15.4,44,7800,5.2,yes,yes,no,good,no,no,ckd",
        "62,80,1.01,2,3,normal,normal,notpresent,notpresent,423,53,1.8,NaN,NaN,9.6,31,7500,NaN,no,\tno,no,poor,no,yes,ckd\t",
        "40,80,1.025,0,0,normal,normal,notpresent,notpresent,140,10,1.2,135,5,15,48,10400,4.5,no,no,no,good,no,no,notckd",
        "23,80,1.025,0,0,normal,abnormal,notpresent,notpresent,70,36,1,?,4.6,17,52,9800,5,no,no,no,good,no,no,notckd"]
    (tmp_path / "ckd").mkdir()
    (tmp_path / "ckd" / "ckd.csv").write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("ckd"))
    assert X.shape == (4, 24) and y.tolist() == [1, 1, 0, 0]
    assert X[:, names.index("dm")].tolist() == [1.0, 0.0, 0.0, 0.0]  # '\tno' -> 0
    assert X[1, names.index("appet")] == 1.0 and X[2, names.index("al")] == 0.0
    assert np.isnan(X[0, names.index("rbc")]) and np.isnan(X[3, names.index("sod")])


def test_statlog_heart_loader(tmp_path, monkeypatch):
    rows = ["52.0 1.0 1.0 138.0 240.0 1.0 0.0 155.0 0.0 1.1 3.0 0.0 6.0 1",
            "66.0 1.0 4.0 150.0 300.0 0.0 2.0 112.0 1.0 2.5 2.0 2.0 7.0 2",
            "59.0 0.0 4.0 142.0 0.0 0.0 1.0 131.0 1.0 3.0 3.0 1.0 7.0 2"]
    _zip(tmp_path, "statlog_heart", "statlog_heart.zip", "heart.dat", "\n".join(rows) + "\n")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("statlog_heart"))
    assert X.shape == (3, 20) and y.tolist() == [0, 1, 1]
    assert names[-3:] == ["thal=3.0", "thal=6.0", "thal=7.0"] and np.isnan(X[2, names.index("chol")])


def test_hepatitis_loader(tmp_path, monkeypatch):
    rows = ["2,30,2,1,2,2,2,2,1,2,2,2,2,2,1.00,85,18,4.0,?,1",
            "1,50,1,1,2,1,1,2,2,2,1,1,1,2,2.30,280,98,3.0,40,2",
            "2,34,1,?,2,2,2,2,2,2,2,2,2,2,0.90,95,28,4.0,75,1",
            "1,62,1,2,2,1,1,2,?,?,2,1,1,1,1.00,?,60,2.9,0,2",
            "2,41,1,2,1,1,2,2,2,2,2,2,2,2,0.70,81,53,5.0,74,1"]
    _zip(tmp_path, "hepatitis", "hepatitis.zip", "hepatitis.data", "\n".join(rows) + "\n")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("hepatitis"))
    assert X.shape == (5, 19) and y.tolist() == [0, 1, 0, 1, 0]
    assert X[:, names.index("ASCITES")].tolist() == [0.0, 1.0, 0.0, 1.0, 0.0]
    assert X[:, names.index("SEX")].tolist() == [1.0, 0.0, 0.0, 0.0, 0.0]
    assert np.isnan(X[0, names.index("PROTIME")]) and np.isnan(X[3, names.index("PROTIME")])
    assert int(np.isnan(X).sum()) == 6


def test_thyroid_sick_loader(tmp_path, monkeypatch):
    flags = ["on_thyroxine", "query_on_thyroxine", "on_antithyroid_medication", "sick", "pregnant",
             "thyroid_surgery", "I131_treatment", "query_hypothyroid", "query_hyperthyroid", "lithium", "goitre",
             "tumor", "hypopituitary", "psych"]
    header = ["@relation sick", "@attribute 'age' integer", "@attribute 'sex' { F, M}"]
    header += [f"@attribute '{f}' {{ f, t}}" for f in flags]
    for lab in ["TSH", "T3", "TT4", "T4U", "FTI"]:
        header += [f"@attribute '{lab}_measured' {{ t, f}}", f"@attribute '{lab}' real"]
    header += ["@attribute 'TBG_measured' { f}", "@attribute 'TBG' real",
               "@attribute 'referral_source' { SVHC, other, SVI, STMW, SVHD}",
               "@attribute 'Class' { negative, sick}", "@data"]
    rows = ["41,F,f,f,f,f,f,f,f,f,f,f,f,f,f,f,t,1.3,t,2.5,t,125,t,1.14,t,109,f,?,SVHC,negative",
            "455,F,t,f,f,f,f,f,f,f,f,f,f,f,f,f,t,0.16,t,1.9,t,175,f,?,f,?,f,?,other,negative",
            "65,M,f,f,f,t,f,f,f,f,f,f,f,f,f,f,t,1.5,t,0.6,t,80,t,0.95,t,84,f,?,SVI,sick",
            "58,?,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,?,t,0.8,t,95,t,1.0,t,95,f,?,SVI,sick"]
    (tmp_path / "thyroid_sick").mkdir()
    (tmp_path / "thyroid_sick" / "sick.arff").write_text("\n".join(header + rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("thyroid_sick"))
    assert X.shape == (4, 25) and y.tolist() == [0, 0, 1, 1]
    assert np.isnan(X[1, names.index("age")])  # 455 > declared maximum -> missing
    assert X[:, names.index("on_thyroxine")].tolist() == [0.0, 1.0, 0.0, 0.0]
    assert X[2, names.index("sex")] == 1.0 and np.isnan(X[3, names.index("sex")])
    assert X[2, names.index("referral_source=SVI")] == 1.0
    assert not {"TBG", "TBG_measured", "TSH_measured", "hypopituitary"} & set(names)


def test_cervical_loader(tmp_path, monkeypatch):
    header = ("Age,Number of sexual partners,First sexual intercourse,Num of pregnancies,Smokes,Smokes (years),"
              "Smokes (packs/year),Hormonal Contraceptives,Hormonal Contraceptives (years),IUD,IUD (years),STDs,"
              "STDs (number),STDs:condylomatosis,STDs:cervical condylomatosis,STDs:vaginal condylomatosis,"
              "STDs:vulvo-perineal condylomatosis,STDs:syphilis,STDs:pelvic inflammatory disease,"
              "STDs:genital herpes,STDs:molluscum contagiosum,STDs:AIDS,STDs:HIV,STDs:Hepatitis B,STDs:HPV,"
              "STDs: Number of diagnosis,STDs: Time since first diagnosis,STDs: Time since last diagnosis,"
              "Dx:Cancer,Dx:CIN,Dx:HPV,Dx,Hinselmann,Schiller,Citology,Biopsy")
    z12 = ",".join(["0.0"] * 12)
    rows = [f"34,?,17.0,1.0,0.0,0.0,0.0,1.0,3.0,0.0,0.0,0.0,0.0,{z12},0,?,?,0,0,0,0,0,0,0,0",
            "45,3.0,16.0,4.0,1.0,20.0,5.0,1.0,10.0,1.0,4.0,1.0,2.0,1.0,0.0,0.0,1.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,"
            "1,3.0,3.0,1,0,1,1,1,1,0,1",
            f"30,1.0,20.0,2.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,{z12},0,?,?,0,0,0,0,0,1,1,1"]
    _zip(tmp_path, "cervical", "cervical.zip", "risk_factors_cervical_cancer.csv", "\n".join([header, *rows]) + "\n")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    X, y, names = registry.load(_entry("cervical"))
    assert X.shape == (3, 28) and y.tolist() == [0, 1, 1]
    for col in ("Hinselmann", "Schiller", "Citology", "STDs:AIDS", "STDs: Time since first diagnosis"):
        assert col not in names
    assert np.isnan(X[0, names.index("Number of sexual partners")])
    assert X[1, names.index("Smokes")] == 1.0 and X[1, names.index("Dx")] == 1.0


# --- generic registry behaviour -------------------------------------------------------------------------------

def test_checksum_mismatch_is_rejected(tmp_path, monkeypatch):
    (tmp_path / "pima").mkdir()
    (tmp_path / "pima" / "diabetes.arff").write_text("@relation x\n", encoding="utf-8")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    with pytest.raises(ValueError, match="checksum"):
        registry.fetch(registry.REGISTRY["pima"])


def test_encoders_and_groups(tmp_path, monkeypatch):
    csv = "id,sex,stage,colour,val,out\nS1_a,M,II,red,0,yes\nS1_b,F,I,blue,3, no\nS2_a,M,III,,5,yes\nS3_a,F,I,green,,no\n"
    (tmp_path / "toy").mkdir()
    (tmp_path / "toy" / "toy.csv").write_text(csv, encoding="utf-8")
    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    entry = registry.DatasetEntry(
        name="toy", title="toy", split="sanity", source="", url="https://example.invalid", file="toy.csv", member=None,
        sha256=None, licence="", provenance="", positive_class="yes", target="out", positive_values=("yes",),
        columns=(registry.Column("sex", "binary", ("F", "M")), registry.Column("stage", "ordinal", ("I", "II", "III")),
                 registry.Column("colour", "nominal", ("red", "blue")), registry.Column("val", zero_is_missing=True)),
        group_column="id", group_regex=r"^(S\d+)_")
    X, y, names = registry.load(entry)
    assert names == ["sex", "stage", "colour=red", "colour=blue", "val"]
    assert y.tolist() == [1, 0, 1, 0]
    assert X[:, 0].tolist() == [1, 0, 1, 0] and X[:, 1].tolist() == [1, 0, 2, 0]
    assert X[0, 2:4].tolist() == [1, 0] and np.isnan(X[2, 2]) and X[3, 2:4].tolist() == [0, 0]  # green: unseen level
    assert np.isnan(X[0, 4]) and np.isnan(X[3, 4])
    assert registry.groups(entry).tolist() == ["S1", "S1", "S2", "S3"]
    d = registry.describe(entry)
    assert d["rows"] == 4 and d["positives"] == 2 and not d["accepted"]


def test_fetch_downloads_once_and_cli(tmp_path, monkeypatch, capsys):
    calls = []

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        return Resp(b"col\n1\n")

    monkeypatch.setattr(registry, "RAW_DIR", tmp_path)
    monkeypatch.setattr(registry.urllib.request, "urlopen", fake_urlopen)
    entry = dataclasses.replace(registry.REGISTRY["pima"], sha256=None)
    monkeypatch.setitem(registry.REGISTRY, "pima", entry)
    p = registry.fetch(entry)
    registry.fetch(entry)  # cached: no second download
    assert p.read_bytes() == b"col\n1\n" and len(calls) == 1
    registry.main(["fetch", "--name", "pima"])
    assert "pima" in capsys.readouterr().out


def test_write_docs(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "REGISTRY", {"breast_cancer": registry.REGISTRY["breast_cancer"]})
    registry.main(["docs", "--out", str(tmp_path / "D.md")])
    text = (tmp_path / "D.md").read_text(encoding="utf-8")
    assert "| 569 | 30 | 212 (37.3%)" in text and "Kaggle credentials not present" in text


def test_builtin_entries_delegate_to_data_module():
    X, y, names = registry.load(registry.REGISTRY["breast_cancer"])
    assert X.shape == (569, 30) and y.sum() == 212
    assert registry.groups(registry.REGISTRY["breast_cancer"]) is None
    assert set(registry.names("development")) >= {"breast_cancer", "heart", "pima", "ilpd"}
