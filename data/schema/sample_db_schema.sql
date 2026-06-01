CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  project_name TEXT NOT NULL,
  status TEXT NOT NULL,
  assignee_name TEXT,
  priority TEXT,
  priority_rank INTEGER,
  due_bucket TEXT,
  due_date TEXT,
  created_bucket TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE projects (
  id INTEGER PRIMARY KEY,
  project_name TEXT NOT NULL,
  status TEXT NOT NULL,
  priority TEXT,
  priority_rank INTEGER,
  created_bucket TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE documents (
  id INTEGER PRIMARY KEY,
  project_name TEXT,
  status TEXT NOT NULL,
  created_bucket TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE jobs (
  id INTEGER PRIMARY KEY,
  project_name TEXT,
  status TEXT NOT NULL,
  created_bucket TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE evaluation_runs (
  id INTEGER PRIMARY KEY,
  project_name TEXT,
  status TEXT,
  score REAL,
  created_bucket TEXT,
  created_at TEXT NOT NULL
);
