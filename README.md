# Michael Mackin Set Piece - Streamlit App

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Included pages
- Landing page: `app.py`
- `Corners`
- `Freekicks`
- `Throw ins`

## Notes on the uploaded data
- The source workbook does not contain a `League` column, so the app creates `Allsvenskan` as a default competition label.
- The source workbook does not contain a match date, so `Last 10 games` is estimated from the 10 highest `match_id` values for each team.
