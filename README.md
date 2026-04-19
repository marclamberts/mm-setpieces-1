# Michael Mackin Set Piece App

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data routing
- Corners → `Allsvenskan - Corners 2025.xlsx`
- Freekicks → `SWE SP.xlsx` filtered to `SP_Type = From Free Kick`
- Throw ins → `SWE SP.xlsx` filtered to `SP_Type = From Throw In`

## Notes
- All pages use `width="stretch"` instead of deprecated `use_container_width`
- The pitch is a compact vertical half-pitch using StatsBomb 120×80 coordinates
- SWE SP delivery maps use available shot end locations when explicit delivery end coordinates are missing
