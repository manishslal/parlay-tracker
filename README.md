# Parlay & Wager Tracker (minimal)

Brief README — how this project is organized and how to use it.

## Files & folders
- `app.py` — Flask backend. Serves endpoints: `/live`, `/todays`, `/historical`, `/stats`, and admin `/admin/compute_returns`.
- `index.html` — Frontend single-page UI.
- `Data/` — JSON fixtures stored here:
  - `Todays_Bets.json` — parlays pending processing.
  - `Live_Bets.json` — parlays currently in-progress.
  - `Historical_Bets.json` — completed parlays (with `odds`, `wager`, `returns`).
- `Tools/compute_returns.py` — utility to compute and persist missing `returns` fields.
- `tests/` — unit tests (pytest).

## Running the app
1. Use the project virtualenv Python located at `.venv/bin/python`.
2. Start the Flask app:

```bash
/Users/manishslal/Desktop/Scrapper/.venv/bin/python app.py
```

On startup the server will organize parlays into `Data/` files and automatically compute missing `returns` (rounded to 2 decimals).

## Admin endpoint (recompute returns on demand)
- Protect this endpoint by setting an environment variable `ADMIN_TOKEN` before starting the server.
- To force recompute:

```bash
export ADMIN_TOKEN="your-token"
curl -X POST http://127.0.0.1:5001/admin/compute_returns \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-token" \
  -d '{"force": true}'
```

The endpoint returns a JSON summary of updates.

## Compute script (local)
- You can run the compute script directly (it uses the `Data/` files):

```bash
python3 Tools/compute_returns.py
```

## Tests
- Run tests with the project's venv Python:

```bash
/Users/manishslal/Desktop/Scrapper/.venv/bin/python -m pytest -q
```

## Notes
- `returns` are calculated from American-style odds (e.g. `+150`) or from per-leg odds if provided; results are rounded to 2 decimal places.
- Keep `Data/` files in sync with `app.py` — the server and the `Tools/` scripts expect the same layout.
- If you want the admin endpoint exposed externally, add stronger auth (I can add basic auth or token validation via a small config file).

## Hosting the frontend on GitHub Pages + backend on Render (recommended)

1. Push this repo to GitHub.
2. Frontend (GitHub Pages):
  - In `index.html` the API base is configurable via `window.API_BASE` (defaults to `http://127.0.0.1:5001`).
  - In your GitHub Pages site, you can serve `index.html` from the repository root or `gh-pages` branch. To point the frontend at your deployed backend, create a small wrapper HTML that sets `window.API_BASE` before loading `index.html`.

3. Backend (Render example):
  - Create a Render Web Service connected to your GitHub repo.
  - Set the start command to: `gunicorn app:app --bind 0.0.0.0:$PORT` (or use the provided `Procfile`).
  - Add environment variable `ADMIN_TOKEN` on Render.
  - Deploy; Render will give you a public URL like `https://my-parlay-app.onrender.com`.

4. Point the frontend at the backend:
  - Either edit `index.html` to set `window.API_BASE = 'https://my-parlay-app.onrender.com'` before the script runs, or host a tiny `config.html` that sets `window.API_BASE` and then includes `index.html`.

If you'd like, I can:
- Add a tiny `config.html` that reads `API_BASE` from a query param and loads the app (handy for GitHub Pages).
- Prepare a GitHub repo layout and sample `gh-pages` branch content.

