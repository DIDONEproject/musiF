import sys


import os

# from musif import FeaturesExtractor
# from musif import FeaturesGenerator
from musif.extract.extract import FeaturesExtractor
from musif.reports.generate import FeaturesGenerator
import pandas as pd
sys.path.insert(0, "../musif")
sys.path.insert(0, "../musif/musif") 


if __name__ == "__main__":

    parts = ["vnI", "obI"]#, "voice"]
    # parts = ["vnI", "ten"]

    arias_path="./arias/time_signatures/"
    arias_path="./arias/"

    # df = FeaturesExtractor("martiser/myconfig.yml").extract(arias_path, parts)
    # df.to_csv('martiser/dataframe.csv', index=False)

    df=pd.read_csv('martiser/dataframe.csv')
    path = './'
    FeaturesGenerator("martiser/myconfig.yml").generate_reports(df, 1, path, parts)