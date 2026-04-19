# Michael Mackin Set Piece App

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Included
- Landing page with light-theme professional styling
- Corners page with:
  - vertical half-pitch visuals
  - StatsBomb 120x80 coordinate logic
  - shotmap
  - delivery map
  - richer sidebar filters
- Freekicks and Throw ins template pages

## Notes
- The bundled corners workbook is `Allsvenskan - Corners 2025.xlsx`
- `Last 10 games` is approximated from descending `match_id`
- Freekicks and Throw ins will activate when their source workbooks are added and mapped in `utils.py`
