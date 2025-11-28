import pandas as pd

meta = pd.read_csv("DisperseArt_InformationVisualization/raw_data/metadata.csv")
wkt = pd.read_csv("DisperseArt_InformationVisualization/raw_data/wkt.csv")

full = meta.merge(wkt, on="site", how="left")

full.to_csv("cultural_damage_full.csv", index=False)
