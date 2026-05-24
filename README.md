Run with:

```bash
streamlit run app.py
```

The app runs from a single Streamlit entry file. Use the sidebar selector inside
`app.py` to switch between Home, Corners, Freekicks, Throw-ins, HOPS, and Delay
Analysis.

Bundled restart data lives in three folders: `Data/Corners`, `Data/SP`, and
`Data/HOPS`. Corners and SP phases load from Parquet files. `Data/SP` contains
phase-specific files such as `Eredivisie - Freekicks.parquet` and
`Eredivisie - Throwins.parquet`, so the app does not need separate prepared or
archive SP folders.

Exports and PDF reports are prepared on demand so normal filtering and view
switching stay lighter.
