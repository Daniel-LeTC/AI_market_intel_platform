import pandas as pd
import sys

try:
    file_path = "staging_data_local/20260129_data/new_product_metadata/list asin - how to draw - review& rating data 1.xlsx"
    df = pd.read_excel(file_path, nrows=0)
    print("Columns:", list(df.columns))
except Exception as e:
    print(e)
