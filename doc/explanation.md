# How this project works (plain-language guide)

This doc explains what the project does, how the code is organized now, and how to run
and deploy the new Streamlit app. 
## 1. What this project does

It's a shipment-logistics analysis for a candy distributor. Given a CSV of orders
(order date, ship date, ship mode, city/state/region, division, customer), it:

1. Cleans the data (fixes dates, drops bad rows).
2. Calculates **Shipping Lead Time** = Ship Date − Order Date, and flags shipments as
   **Delayed** if that's more than 5 days.
3. Groups shipments into **routes** (Division → State, Division → Region) and scores
   each route's efficiency (fast + consistent + high volume = better score).
4. Summarizes performance by state, region, and ship mode.
5. Finds **bottleneck routes** — routes that ship a lot of volume *and* are slow.
6. Produces a KPI summary (the headline numbers).

## 2. `.py` vs `.ipynb` — what's the difference?

- **`.ipynb` (notebook)** — an interactive document (used in Google Colab / Jupyter)
  made of "cells" you run one at a time, mixing code with output and text. Great for
  exploring data step by step, but it can't be served as a web app on its own — it
  needs a notebook environment to open.
- **`.py` (script)** — plain Python code that runs top-to-bottom from a terminal
  (`python file.py`) or is imported by other Python code/tools. This is the format
  Streamlit (and most deployment platforms) need.

In this repo, `UnifiedMentorProject.ipynb` and `UnifiedMentorProject-Atul.ipynb` are
just Colab exports — they contain the exact same code as `unifiedmentorproject.py`,
just wrapped in the notebook format. `unifiedmentorproject.py` is the original,
terminal-runnable script. Nothing in these three files was changed.

## 3. What's new: the Streamlit app

Two new files hold the app:

- **`analysis.py`** — the same calculations as `unifiedmentorproject.py`, rewritten as
  reusable functions that take a DataFrame in and return result tables out (instead of
  reading/writing files on disk). This is the "engine."
- **`app.py`** — the Streamlit "front end." It shows a file upload box in the browser,
  calls the engine in `analysis.py`, and displays the results as tables, charts, and
  download buttons.

### App flow

```
Browser: upload Nassau Candy Distributor.csv
        │
        ▼
app.py: analysis.load_and_validate()   ──►  checks required columns exist
        │
        ▼
analysis.run_analysis(df)
        │
        ├─ clean_data()          → parses dates, drops bad rows, adds Shipping Lead Time / Delayed
        ├─ add_route_features()  → builds Route_State / Route_Region
        ├─ summarize_routes()    → route efficiency scores (top/bottom 10)
        ├─ summarize_geo()       → state & region summaries
        ├─ compute_bottlenecks() → high-volume + slow routes
        ├─ summarize_shipmode()  → ship mode performance
        └─ build_kpi_summary()   → headline KPIs
        │
        ▼
app.py: renders each table + a chart, with a "Download CSV" button
```

Nothing is written to disk on the server — every result table gets a download button
so you can save the CSVs yourself, matching the files the original script used to write
(`route_state_summary.csv`, `kpi_summary.csv`, etc.).

## 4. Running the app on your own computer

1. Install the dependencies (one-time, from the project folder):
   ```bash
   pip install -r requirements.txt
   ```
2. Start the app:
   ```bash
   streamlit run app.py
   ```
3. Your browser opens automatically at `http://localhost:8501`. Upload
   `Nassau Candy Distributor.csv` and the tables/charts appear.

You do **not** need the CSV sitting in the folder anymore — you upload it through the
browser each time.

## 5. Deploying it online (Streamlit Community Cloud — free)

1. Push this repo to GitHub (if it isn't already there).
2. Go to https://share.streamlit.io and sign in with your GitHub account.
3. Click "New app," pick this repository and branch, and set the entry point file to
   `app.py`.
4. Click "Deploy." Streamlit Cloud reads `requirements.txt` automatically and installs
   `streamlit`, `pandas`, and `numpy` for you.
5. After a minute or two you'll get a public URL (like
   `https://your-app-name.streamlit.app`) you can share with anyone — they upload their
   own CSV and see the results, no installation needed on their end.

## 6. Where to change behavior later

All the tunable settings live at the top of `analysis.py`:

- `DELAY_THRESHOLD_DAYS` — how many days late counts as "Delayed" (currently 5).
- The `COL_*` constants — the exact column names expected in the CSV.
- The weights inside `summarize_routes()` (0.5 / 0.3 / 0.2) — how much lead time,
  variability, and volume each count toward the efficiency score.

You don't need to touch `app.py` for those kinds of changes — only `analysis.py`.
