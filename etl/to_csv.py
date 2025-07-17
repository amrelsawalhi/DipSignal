import pandas as pd
import os


def append_unique_rows(new_data: pd.DataFrame, csv_path1: str, csv_path2: str = None, subset_cols=["date"]):
    if "date" not in new_data.columns:
        raise ValueError("new_data must contain a 'date' column")

    new_data["date"] = pd.to_datetime(new_data["date"]).dt.date

    if os.path.exists(csv_path1):
        existing_data = pd.read_csv(csv_path1)
        existing_data["date"] = pd.to_datetime(existing_data["date"]).dt.date
        combined = pd.concat([existing_data, new_data], ignore_index=True)
        combined = combined.drop_duplicates(subset=subset_cols)
    else:
        combined = new_data.drop_duplicates(subset=subset_cols)

    if csv_path2 is None:
        csv_path2 = csv_path1

    combined.to_csv(csv_path2, index=False)
    print(f"✅ Updated {csv_path2} with {len(combined) - (len(existing_data) if 'existing_data' in locals() else 0)} new rows")
