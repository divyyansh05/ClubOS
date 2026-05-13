import pandas as pd
import json

internal_file = "data/source/GroupE.pack.english/Tema5.data_visualization.dataset/Tema5.internal_metrics.dataset.xlsx"
benchmark_file = "data/source/GroupE.pack.english/Tema5.data_visualization.dataset/Tema5.benchmark.dataset.xlsx"

def inspect_file(filepath):
    print(f"Inspecting File: {filepath}")
    try:
        xls = pd.ExcelFile(filepath)
        print(f"Sheets: {xls.sheet_names}")
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            print(f"\n--- Sheet: {sheet} ---")
            print(f"Row count: {len(df)}")
            print(f"Columns: {list(df.columns)}")
            if not df.empty:
                print("First row values:")
                print(df.iloc[0].to_dict())
            if 'month' in df.columns or 'Month' in df.columns:
                col = 'month' if 'month' in df.columns else 'Month'
                dates = pd.to_datetime(df[col], errors='coerce')
                min_date = dates.min()
                max_date = dates.max()
                print(f"Date range: {min_date} to {max_date}")
            print("=" * 40)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

inspect_file(internal_file)
print("\n#############################################\n")
inspect_file(benchmark_file)
