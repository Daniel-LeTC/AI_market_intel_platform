import pandas as pd
import glob
import os

target_asins = [
    "B0CCVGQ3Y9", "B0CD7YPQK5", "B0CGVDPNN3", "B0CMZMJN7P", "B0DZ2VDLZV",
    "B0DF7K9F9D", "B0BFLGL83C", "B0C9J997WT", "B0DZ2T631C", "B0DKTNNS1C",
    "B0BY31VFKX", "B093ZNGLYJ", "B0CM9DB6WF", "B0CSYBS1N3", "B0CCHYB4KY",
    "B0DPPSXQ43", "B0BWPTNMNV", "B0DCCBBNW5", "B0D7P4FRNK", "B0D6VBT8T1",
    "B0DQQD6NJ7", "B07VKBSB4P", "B0CXDSG8ZM", "B0BGS8QTSM", "B07R2DR3YL",
    "B0F5QXF4L8"
]

files = glob.glob("staging_data/*.xlsx")
found = {}

for f in files:
    try:
        df = pd.read_excel(f, nrows=1000) # Quick scan
        # Check columns
        cols = df.columns.tolist()
        asin_col = next((c for c in cols if c.lower() in ['asin', 'parentasin']), None)
        if not asin_col: continue
        
        present = df[df[asin_col].isin(target_asins)]
        if not present.empty:
            found[os.path.basename(f)] = present[asin_col].unique().tolist()
    except:
        pass

print("--- SEARCH RESULTS ---")
for f, asins in found.items():
    print(f"{f}: Found {len(asins)} ASINs")
