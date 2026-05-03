Run with:

```bash
streamlit run app.py
```

The app runs from a single Streamlit entry file. Use the sidebar selector inside
`app.py` to switch between Home, Corners, Freekicks, Throw-ins, HOPS, and Delay
Analysis.

Bundled restart data lives in three folders: `Data/Corners`, `Data/SP`, and
`Data/HOPS`. The app loads every Excel workbook in those folders, including the
Serie A corner and SP workbooks. Corner CSV files in `Data/Corners` are loaded
as well.

Exports and PDF reports are prepared on demand so normal filtering and view
switching stay lighter.
