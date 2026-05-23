from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "Data" / "SP"
OUTPUT_DIR = ROOT / "Data" / "SP_Parquet"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(SOURCE_DIR.glob("*.xls*")):
        if path.name.startswith("~$"):
            continue
        df = pd.read_excel(path, engine="openpyxl")
        output = OUTPUT_DIR / f"{path.stem}.parquet"
        df.to_parquet(output, engine="pyarrow", index=False, compression="zstd")
        print(f"{path.name}: {len(df):,} rows, {len(df.columns)} columns -> {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
