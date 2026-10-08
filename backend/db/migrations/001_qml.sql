-- 001_qml.sql - optional Supabase persistence for SIH26139 hybrid QML experiments.
-- NOT APPLIED. The app persists results to backend/ml/quantum/results/*.json by default.
create extension if not exists "pgcrypto";

create table public.qml_datasets (
  id            uuid primary key default gen_random_uuid(),
  owner_id      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name          text not null,
  source_url    text,
  licence       text,
  is_synthetic  boolean not null default false,
  n_samples     integer check (n_samples >= 0),
  n_features    integer check (n_features >= 0),
  target        text,
  created_at    timestamptz not null default now(),
  unique (owner_id, name)
);

create table public.qml_experiments (
  id             uuid primary key default gen_random_uuid(),
  owner_id       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  dataset_id     uuid not null references public.qml_datasets(id) on delete cascade,
  name           text not null,
  seed           integer not null default 42,
  n_folds        integer not null default 5 check (n_folds between 2 and 20),
  feature_method text not null check (feature_method in ('pca','mutual_info')),
  n_features     integer not null check (n_features between 2 and 16),
  git_sha        text,
  status         text not null default 'pending' check (status in ('pending','running','done','failed')),
  created_at     timestamptz not null default now(),
  finished_at    timestamptz
);

create table public.qml_model_runs (
  id             uuid primary key default gen_random_uuid(),
  owner_id       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  experiment_id  uuid not null references public.qml_experiments(id) on delete cascade,
  model_name     text not null check (model_name in ('logreg','svm_rbf','random_forest','mlp','qsvm','vqc','hybrid_qnn')),
  family         text not null check (family in ('classical','quantum','hybrid')),
  backend        text,
  n_qubits       integer check (n_qubits between 1 and 32),
  circuit_depth  integer check (circuit_depth >= 0),
  n_params       integer check (n_params >= 0),
  hyperparams    jsonb not null default '{}'::jsonb,
  train_time_s   double precision,
  infer_ms       double precision,
  artifact_path  text,
  created_at     timestamptz not null default now()
);

create table public.qml_metrics (
  id          bigint generated always as identity primary key,
  owner_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  run_id      uuid not null references public.qml_model_runs(id) on delete cascade,
  fold        integer,
  metric      text not null check (metric in ('accuracy','sensitivity','specificity','auc','f1','gen_gap','kernel_alignment')),
  value       double precision not null,
  std         double precision,
  curve       jsonb,
  created_at  timestamptz not null default now(),
  unique nulls not distinct (run_id, fold, metric)
);

create index on public.qml_experiments (dataset_id);
create index on public.qml_model_runs (experiment_id);
create index on public.qml_metrics (run_id);

alter table public.qml_datasets    enable row level security;
alter table public.qml_experiments enable row level security;
alter table public.qml_model_runs  enable row level security;
alter table public.qml_metrics     enable row level security;

create policy qml_datasets_owner    on public.qml_datasets    for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy qml_experiments_owner on public.qml_experiments for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy qml_model_runs_owner  on public.qml_model_runs  for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy qml_metrics_owner     on public.qml_metrics     for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
