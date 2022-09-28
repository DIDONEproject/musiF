import sys
sys.path.insert(0, "../musif/")
# sys.path.append('../')
from musif.extract.extract import FeaturesExtractor
from musif.reports.generate import ReportsGenerator
from musif.process.processor import DataProcessor

import pandas as pd

if __name__ == "__main__":
    data_dir = r'tests/data/static/features'
    musescore_dir=data_dir

    data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Dem08M-Padre_perdona-1771-Sarti[1.12][1172].xml'
    
    data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Did57M-Zen-Fra_tutte-1753-Perez[2.12][0255].xml'
    
    #test
    # data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Did03M-Son_regina-1730-Sarro[1.05][0006].xml'
    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'
    
    df = FeaturesExtractor("scripts/config_tests.yml", data_dir=data_dir, musescore_dir=musescore_dir).extract()
    df.to_csv('martiser/'+'test.csv', index=False)
    # df=pd.read_csv('arias_test.csv')
    path = '.'
    # ReportsGenerator("scripts/config_tests.yml").generate_reports(df, path, num_factors=0, visualizations=True)
    
    