from ast import List
import csv
import pandas as pd


# def read_dicts_from_csv(file_path: str) -> List[dict]:
#     with open(file_path, "r", encoding='utf8') as file:
#         return [obj for obj in csv.DictReader(file)]

if __name__ == "__main__":
    #Arias.csv
    arias_route=r'../../../_Ana/Music Analysis/Arias_change.xlsx'
    df_arias = pd.read_excel(arias_route, header=2)
    df_arias.rename(columns={'ID': 'AriaId', 'Country':'Territory', 'Type': 'RoleType'}, inplace=True)
    df_arias['Gender']= [str(i).split(' ')[0] for i in df_arias['RoleType']]
    columns=['AriaId','Form','Character','Gender','RoleType','City','Territory']
    df_arias=df_arias[columns]
    df_arias.to_csv(r'../../musif/metadata/score/aria.csv', index=False)

    #clefs.csv
    clefs_route=r'../../../_Ana/Music Analysis/Arias_clefs.xlsx'
    df_clefs = pd.read_excel(clefs_route, header=1)
    df_clefs.rename(columns={'ID': 'AriaId', 'Clef 1': 'Clef1', 'Clef 2': 'Clef2',  'Clef 3': 'Clef3'}, inplace=True)
    columns=['AriaId','Character','Clef1', 'Clef2', 'Clef3']
    df_clefs=df_clefs[columns]
    df_clefs.to_csv(r'../../musif/metadata/score/clefs.csv', index=False)
    pass