# Contributing

## Development Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -v
```

## Branch Naming
- `feature/<name>`
- `fix/<name>`
- `docs/<name>`
- `release/<version>`

## Pull Requests
- one focused change;
- tests included or updated;
- documentation updated when behavior changes;
- no `.env`, virtual environments, caches, or generated reports committed.
