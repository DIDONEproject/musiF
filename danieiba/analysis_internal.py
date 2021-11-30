import pandas as pd

from musif.common.utils import read_dicts_from_csv
from musif.extract.features.ambitus.constants import HIGHEST_NOTE_INDEX, LOWEST_NOTE_INDEX
from musif.extract.features.core.constants import FILE_NAME, SOUNDING_MEASURES_MEAN
from musif.extract.features.density.constants import DENSITY, SOUNDING_DENSITY
from musif.extract.features.file_name.constants import ARIA_ID, ARIA_LABEL
from musif.extract.features.interval.constants import ABSOLUTE_INTERVALLIC_KURTOSIS, ABSOLUTE_INTERVALLIC_MEAN, \
    ABSOLUTE_INTERVALLIC_SKEWNESS, ABSOLUTE_INTERVALLIC_STD, INTERVALLIC_KURTOSIS, INTERVALLIC_MEAN, \
    INTERVALLIC_SKEWNESS, INTERVALLIC_STD, INTERVALS_AUGMENTED_ALL_PER, INTERVALS_DIMINISHED_ALL_PER, \
    INTERVALS_MAJOR_ALL_PER, INTERVALS_MINOR_ALL_PER, INTERVALS_PERFECT_ALL_PER, LEAPS_ALL_PER, REPEATED_NOTES_PER, \
    STEPWISE_MOTION_ALL_PER
from musif.extract.features.key.constants import KEY, KEY_SIGNATURE_TYPE, MODE
from musif.extract.features.lyrics.constants import SYLLABIC_RATIO
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scoring.constants import FAMILY_INSTRUMENTATION, INSTRUMENTATION, NUMBER_OF_PARTS, VOICES
from musif.extract.features.tempo.constants import NUMERIC_TEMPO, TEMPO, TEMPO_GROUPED_1, TEMPO_GROUPED_2, \
    TIME_SIGNATURE, TIME_SIGNATURE_GROUPED

if __name__ == "__main__":
    df = pd.read_csv("myfeatures.csv", low_memory=False)
    passions = read_dicts_from_csv("passions.csv")
    data_by_aria_label = {label_data["Label"]: label_data for label_data in passions}
    label_by_col = {
        "Basic_passion": "Label_BasicPassion",
        "Passion": "Label_Passions",
        "Value": "Label_Sentiment",
        "Time": "Label_Time",
    }
    for col, label in label_by_col.items():
        values = []
        for index, row in df.iterrows():
            data_by_aria = data_by_aria_label.get(row["AriaLabel"])
            label_value = data_by_aria[col] if data_by_aria else None
            values.append(label_value)
        df[label] = values

    data_list = []
    for index, row in df.iterrows():
        voice = row[VOICES]
        if pd.isnull(voice):
            print(row["FileName"])
            continue
        if "," in voice:
            voice = voice.split(",")[0]
        input_parts = [voice, "vnI", "bs"]
        output_parts = ["Voice", "vnI", "bs"]
        input_parts_prefixes = [get_part_prefix(part_prefix) for part_prefix in input_parts]
        output_parts_prefixes = [get_part_prefix(part_prefix) for part_prefix in output_parts]
        data_item = {
            "AriaId": row[ARIA_ID],
            "FileName": row[FILE_NAME],
            "Mode": row[MODE],
            "Key": row[KEY],
            "KeySignatureType": row[KEY_SIGNATURE_TYPE],
            "NumberOfParts": row[NUMBER_OF_PARTS],
            "FamilyInstrumentation": row[FAMILY_INSTRUMENTATION],
            "Instrumentation": row[INSTRUMENTATION],
            "Tempo": row[TEMPO],
            "TempoNumeric": row[NUMERIC_TEMPO],
            "TempoGrouped1": row[TEMPO_GROUPED_1],
            "TempoGrouped2": row[TEMPO_GROUPED_2],
            "TimeSignature": row[TIME_SIGNATURE],
            "TimeSignatureGrouped": row[TIME_SIGNATURE_GROUPED],
            f"{get_part_prefix('Voice')}SyllabicRatio": row[f"{get_part_prefix(voice)}{SYLLABIC_RATIO}"],
            "Score_Density": row[f"Score_{DENSITY}"],
            "Score_SoundingDensity": row[f"Score_{SOUNDING_DENSITY}"],
            "Score_SoundingMeasuresMean": row[f"Score_{SOUNDING_MEASURES_MEAN}"],
            "Label_TextId": row[ARIA_LABEL],
            "Label_Sentiment": row["Label_Sentiment"],
            "Label_BasicPassion": row["Label_BasicPassion"],
            "Label_Passions": row["Label_Passions"],
            "Label_Time": row["Label_Time"],
        }
        for input_part, output_part in zip(input_parts_prefixes, output_parts_prefixes):
            data_item[f"{output_part}HighestNoteIndex"] = row[f"{input_part}{HIGHEST_NOTE_INDEX}"]
            data_item[f"{output_part}LowestNoteIndex"] = row[f"{input_part}{LOWEST_NOTE_INDEX}"]
            data_item[f"{output_part}Density"] = row[f"{input_part}{DENSITY}"]
            data_item[f"{output_part}SoundingDensity"] = row[f"{input_part}{SOUNDING_DENSITY}"]
            data_item[f"{output_part}IntervallicMean"] = row[f"{input_part}{INTERVALLIC_MEAN}"]
            data_item[f"{output_part}IntervallicStd"] = row[f"{input_part}{INTERVALLIC_STD}"]
            data_item[f"{output_part}IntervallicSkewness"] = row[f"{input_part}{INTERVALLIC_SKEWNESS}"]
            data_item[f"{output_part}IntervallicKurtosis"] = row[f"{input_part}{INTERVALLIC_KURTOSIS}"]
            data_item[f"{output_part}AbsoluteIntervallicMean"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_MEAN}"]
            data_item[f"{output_part}AbsoluteIntervallicStd"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_STD}"]
            data_item[f"{output_part}AbsoluteIntervallicSkewness"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_SKEWNESS}"]
            data_item[f"{output_part}AbsoluteIntervallicKurtosis"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_KURTOSIS}"]
            data_item[f"{output_part}IntervalsDiminishedAll"] = row[f"{input_part}{INTERVALS_DIMINISHED_ALL_PER}"]
            data_item[f"{output_part}IntervalsMinorAll"] = row[f"{input_part}{INTERVALS_MINOR_ALL_PER}"]
            data_item[f"{output_part}IntervalsPerfectAll"] = row[f"{input_part}{INTERVALS_PERFECT_ALL_PER}"]
            data_item[f"{output_part}IntervalsMajorAll"] = row[f"{input_part}{INTERVALS_MAJOR_ALL_PER}"]
            data_item[f"{output_part}IntervalsAugmentedAll"] = row[f"{input_part}{INTERVALS_AUGMENTED_ALL_PER}"]
            data_item[f"{output_part}LeapsAll"] = row[f"{input_part}{LEAPS_ALL_PER}"]
            data_item[f"{output_part}StepwiseMotionAll"] = row[f"{input_part}{STEPWISE_MOTION_ALL_PER}"]
            data_item[f"{output_part}RepeatedNotes"] = row[f"{input_part}{REPEATED_NOTES_PER}"]
        data_list.append(data_item)
    df_analysis = pd.DataFrame(data_list)
    df_analysis = df_analysis.reindex(sorted(df_analysis.columns), axis=1)
    df_analysis.sort_values("AriaId", inplace=True)
    df_analysis.to_csv("analysis4.csv", index=False)
    print()
