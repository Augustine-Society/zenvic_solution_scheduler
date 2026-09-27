# Zenvic Solution Scheduler

Zenvic Solution Scheduler is a Streamlit-based workforce attendance and roster management dashboard. It gives supervisors and workers a shared interface for registering workers, planning weekly shifts, recording daily attendance, reviewing historical logs, and exporting attendance data as CSV files.

The application uses Supabase as its cloud database and is organized around four operational views:

- **Live Station:** Walk-up clock-in and clock-out with a real-time attendance board.
- **Daily Archive:** Review attendance for a selected date, filter records, and download CSV reports.
- **Worker Audit:** Inspect an individual worker's shift history, cumulative hours, and on-site/WFH breakdown.
- **Roster Manager:** Plan current or upcoming weekly schedules, including on-site, WFH, and rest-day assignments.

## Features

- Worker registration with duty number, name, department, and active status.
- On-site and work-from-home clock-in modes.
- Clock-out processing with calculated hours worked.
- Duplicate daily punch protection.
- Live attendance KPIs for on-site, WFH, clocked-out, and not-arrived workers.
- Weekly schedule planning with configurable shift times.
- Rest-day assignments.
- Historical attendance search and status filtering.
- Worker-specific attendance analytics.
- CSV exports for daily logs and individual worker history.
- Supabase-backed shared data storage.

## Technology stack

- **Python**
- **Streamlit** for the web interface
- **Supabase** for PostgreSQL-backed cloud storage and API access
- **Pandas** for table preparation, filtering, styling, and analytics
- **python-dateutil** for date-related utilities

## Project structure

```text
.
├── app.py                    # Streamlit entry point and global navigation
├── requirements.txt           # Python dependencies
├── setup.py                  # Optional project file/folder bootstrap script
├── sql.txt                   # Supabase schema and seed worker records
├── test.py                   # Basic Supabase connectivity check
├── .streamlit/
│   └── secrets.toml          # Local Streamlit secrets configuration
└── src/
    ├── components.py         # Shared UI components, KPIs, formatting, and data merging
    ├── db.py                 # Supabase client and worker, punch, and schedule operations
    └── views/
        ├── daily_archive.py  # Historical daily attendance view
        ├── live_station.py   # Live kiosk and attendance board
        ├── roster_manager.py # Weekly roster planning interface
        └── worker_audit.py   # Worker history and attendance analytics
```

## Data model

The database schema in `sql.txt` defines three tables:

- `workers`: Worker directory with duty number, name, department, and active status.
- `schedules`: Planned shifts with date, shift type, start time, and end time.
- `punch_logs`: Actual attendance records with status, clock-in/out times, and total hours.

The schema enforces one schedule per worker per date and one punch record per worker per date.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Augustine-Society/zenvic_solution_scheduler.git
cd zenvic_solution_scheduler
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Supabase

Create a Supabase project, run the SQL in `sql.txt` in the Supabase SQL editor, and configure the connection values through Streamlit secrets.

Create `.streamlit/secrets.toml` with the following structure:

```toml
[supabase]
url = "https://your-project.supabase.co"
key = "your-supabase-key"
```

Use an appropriate Supabase key for the deployment environment. Do not commit real credentials to Git, and rotate any credentials that may have been exposed in source files or test scripts.

## Run the application

Start the Streamlit dashboard with:

```bash
streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## Verify the database connection

The repository includes a simple connectivity script:

```bash
python test.py
```

This script queries the `workers` table and prints the returned records. Ensure that the Supabase credentials are configured before running it.

## Usage overview

1. Open **Register New Worker** in the sidebar to add a worker.
2. Use **Live Station** to select a worker and clock them in as **On Duty** or **WFH**.
3. Clock the worker out when the shift ends; total hours are calculated automatically.
4. Use **Weekly Roster Manager** to assign upcoming shifts and rest days.
5. Use **Daily Log Archive** to inspect and export attendance for a selected date.
6. Use **Worker-Wise Audit** to review an individual's historical records and cumulative hours.

## Notes

- The application expects the Supabase tables from `sql.txt` to exist before normal use.
- Attendance statuses are `On Duty`, `WFH`, and `Clocked Out`.
- Schedule types are `On-Site`, `WFH`, and `Rest Day`.
- The current implementation calculates elapsed hours from the local application server clock.
- Generated Python cache files should not be committed; add `__pycache__/` and `*.pyc` to `.gitignore` in future cleanup work.

## License

No license file is currently included. Add a license before distributing the project publicly.
