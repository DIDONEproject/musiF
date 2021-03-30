from typing import List, Tuple

from pandas import DataFrame

from musif.common.sort import sort_dict
from musif.config import Configuration
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_score_prefix, get_sound_prefix
from musif.musicxml import Measure, Note, Part

NOTES = "Notes"
SOUNDING_MEASURES = "SoundingMeasures"
MEASURES = "Measures"
SOUNDING_DENSITY = "SoundingDensity"
DENSITY = "Density"


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    notes = part_data["notes"]
    sounding_measures = part_data["sounding_measures"]
    measures = part_data["sounding_measures"]
    features = {
        NOTES: len(notes),
        SOUNDING_MEASURES: len(sounding_measures),
        MEASURES: len(measures),
        SOUNDING_DENSITY: len(notes) / len(sounding_measures),
        DENSITY: len(notes) / len(measures),
    }
    return features


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    features = {}
    df_parts = DataFrame(parts_features)
    df_sound = df_parts.groupby("SoundAbbreviation").aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    df_family = df_parts.groupby("FamilyAbbreviation").aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    df_score = df_parts.aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    for part_features in parts_features:
        part_prefix = get_part_prefix(part_features['PartAbbreviation'])
        features[f"{part_prefix}{NOTES}"] = part_features[NOTES]
        features[f"{part_prefix}{SOUNDING_MEASURES}"] = part_features[SOUNDING_MEASURES]
        features[f"{part_prefix}{MEASURES}"] = part_features[MEASURES]
        features[f"{part_prefix}{SOUNDING_DENSITY}"] = part_features[SOUNDING_DENSITY]
        features[f"{part_prefix}{DENSITY}"] = part_features[DENSITY]
    for sound in df_sound.index:
        sound_prefix = get_sound_prefix(sound)
        features[f"{sound_prefix}{NOTES}"] = df_sound.loc[sound, NOTES].tolist()
        features[f"{sound_prefix}{SOUNDING_MEASURES}"] = df_sound.loc[sound, SOUNDING_MEASURES].tolist()
        features[f"{sound_prefix}{MEASURES}"] = df_sound.loc[sound, MEASURES].tolist()
        features[f"{sound_prefix}{SOUNDING_DENSITY}"] = features[f"{sound_prefix}{NOTES}"] / features[f"{sound_prefix}{SOUNDING_MEASURES}"]
        features[f"{sound_prefix}{DENSITY}"] = features[f"{sound_prefix}{NOTES}"] / features[f"{sound_prefix}{MEASURES}"]
    for family in df_family.index:
        family_prefix = get_family_prefix(family)
        features[f"{family_prefix}{NOTES}"] = df_family.loc[family, NOTES].tolist()
        features[f"{family_prefix}{SOUNDING_MEASURES}"] = df_family.loc[family, SOUNDING_MEASURES].tolist()
        features[f"{family_prefix}{MEASURES}"] = df_family.loc[family, MEASURES].tolist()
        features[f"{family_prefix}{SOUNDING_DENSITY}"] = features[f"{family_prefix}{NOTES}"] / features[f"{family_prefix}{SOUNDING_MEASURES}"]
        features[f"{family_prefix}{DENSITY}"] = features[f"{family_prefix}{NOTES}"] / features[f"{family_prefix}{MEASURES}"]
    score_prefix = get_score_prefix()
    features[f"{score_prefix}{NOTES}"] = df_score[NOTES].tolist()
    features[f"{score_prefix}{SOUNDING_MEASURES}"] = df_score[SOUNDING_MEASURES].tolist()
    features[f"{score_prefix}{MEASURES}"] = df_score[MEASURES].tolist()
    features[f"{score_prefix}{SOUNDING_DENSITY}"] = features[f"{score_prefix}{NOTES}"] / features[f"{score_prefix}{SOUNDING_MEASURES}"]
    features[f"{score_prefix}{DENSITY}"] = features[f"{score_prefix}{NOTES}"] / features[f"{score_prefix}{MEASURES}"]

    return features


def get_measures(part: Part) -> List[Measure]:
    return [element for element in part.getElementsByClass('Measure')]


def get_notes_and_measures(part: Part) -> Tuple[List[Note], List[Measure], List[Measure]]:
    notes = []
    measures = get_measures(part)
    sounding_measures = []
    for measure in measures:
        if len(measure.notes) > 0:
            sounding_measures.append(measure)
        for note in measure.notes:
            set_ties(note, notes)
    return notes, sounding_measures, measures


def set_ties(subject, my_notes_list):
    """
    This function converts tied notes into a unique note
    """
    if not isinstance(subject, Note):
        return
    if subject.tie is None:
        my_notes_list.append(subject)
        return
    if subject.tie.type != "stop" and subject.tie.type != "continue":
        my_notes_list.append(subject)
        return
    if isinstance(my_notes_list[-1], Note):
        my_notes_list[-1].duration.quarterLength += subject.duration.quarterLength  # sum tied notes' length
        return
    back_counter = -1
    while isinstance(my_notes_list[back_counter], tuple):
        back_counter -= -1
    else:
        my_notes_list[
            back_counter
        ].duration.quarterLength += subject.duration.quarterLength  # sum tied notes' length across measures


def calculate_densities(notes_list, measures_list, names_list, cfg: Configuration):
    density_list = []
    try:
        for i, part in enumerate(names_list):
            density = round(notes_list[i]/measures_list[i], 3)
            density_list.append({f'{names_list[i]}': density})

        density_dict = dict((key, d[key]) for d in density_list for key in d)
        density_sorting = cfg.scoring_order
        density_dict = sort_dict(density_dict, density_sorting, cfg)
        return density_dict
    except:
        cfg.read_logger.error('Densities problem found: ', exc_info=True)
        return {}


    #
    #
    # for i, _ in enumerate(parts):
    #     # Criteria: split anything that might have two voices in the same part and is not a violin or a voice
    #     if (df.names[i].replace('I','') not in ['vn', 'voice'] and df['names'][i].endswith('I')):
    #         df['notes'][i] = df['notes'][i]+df['notes'][i+1]
    #         df['measures'][i] = df['measures'][i]+df['measures'][i+1]
    #         df['names'][i] = df.names[i].replace('I', '')
    #         df = df.drop([i+1], axis=0)
    #         df.reset_index(drop=True, inplace=True)
    #         del partVoices[i+1]
    #         continue
    #     if (df.names[i].startswith('voice') and num_voices > 1):
    #         df['notes'][i] = sum(df['notes'][i:i+num_voices])
    #         df['measures'][i] = sum(df['measures'][i:i+num_voices])
    #         df = df.drop([i+1], axis=0)
    #         df.reset_index(drop=True, inplace=True)
    #         del partVoices[i+1]
    #         continue
    #
    # return calculate_densities(notes_list, measures_list, names_list)
