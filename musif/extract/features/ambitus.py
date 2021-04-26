from typing import List

from musif.extract.features.prefix import get_part_prefix

from musif.config import Configuration

LOWEST_NOTE = "AmbitusLowestNote"
HIGHEST_NOTE = "AmbitusHighestNote"
LOWEST_INDEX = "AmbitusLowestIndex"
HIGHEST_INDEX = "AmbitusHighestIndex"
LOWEST_MEAN_NOTE = "AmbitusLowestMeanNote"
LOWEST_MEAN_INDEX = "AmbitusLowestMeanIndex"
HIGHEST_MEAN_NOTE = "AmbitusHighestMeanNote"
HIGHEST_MEAN_INDEX = "AmbitusHighestMeanIndex"
LARGEST_INTERVAL = "AmbitusLargestInterval"
LARGEST_SEMITONES = "AmbitusLargestSemitones"
SMALLEST_INTERVAL = "AmbitusSmallestInterval"
SMALLEST_SEMITONES = "AmbitusSmallestSemitones"
ABSOLUTE_INTERVAL = "AmbitusAbsoluteInterval"
ABSOLUTE_SEMITONES = "AmbitusAbsoluteSemitones"
MEAN_INTERVAL = "AmbitusMeanInterval"
MEAN_SEMITONES = "AmbitusMeanSemitones"

ALL_FEATURES = [LOWEST_INDEX, LOWEST_NOTE, HIGHEST_INDEX, HIGHEST_NOTE, HIGHEST_MEAN_INDEX, HIGHEST_MEAN_NOTE, LOWEST_MEAN_INDEX, LOWEST_MEAN_NOTE,
                LARGEST_INTERVAL, LARGEST_SEMITONES, SMALLEST_INTERVAL, SMALLEST_SEMITONES, ABSOLUTE_INTERVAL, ABSOLUTE_SEMITONES, MEAN_INTERVAL, MEAN_SEMITONES]

def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    this_aria_ambitus = part_data["ambitus_solution"]
    lowest_note, highest_note = part_data["ambitus_pitch_span"]
    lowest_note_text = lowest_note.nameWithOctave.replace("-", "b")
    highest_note_text = highest_note.nameWithOctave.replace("-", "b")
    lowest_index = int(lowest_note.ps)
    highest_index = int(highest_note.ps)
    joined_notes = ",".join([lowest_note_text, highest_note_text])

    return {
        LOWEST_NOTE: lowest_note_text,
        HIGHEST_NOTE: highest_note_text,
        LOWEST_INDEX: lowest_index,
        HIGHEST_INDEX: highest_index,
        LOWEST_MEAN_NOTE: lowest_note_text,
        LOWEST_MEAN_INDEX: lowest_index,
        HIGHEST_MEAN_NOTE: highest_note_text,
        HIGHEST_MEAN_INDEX: highest_index,
        LARGEST_INTERVAL: this_aria_ambitus.name,
        LARGEST_SEMITONES: this_aria_ambitus.semitones,
        SMALLEST_INTERVAL: this_aria_ambitus.name,
        SMALLEST_SEMITONES: this_aria_ambitus.semitones,
        ABSOLUTE_INTERVAL: joined_notes,
        ABSOLUTE_SEMITONES: joined_notes,
        MEAN_INTERVAL: joined_notes,
        MEAN_SEMITONES: joined_notes,
    }

def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    if len(parts_data) == 0:
        return {}
    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data["abbreviation"])
        for feature_name in ALL_FEATURES:
            features[f"{part_prefix}{feature_name}"] = part_features[feature_name]
    return features
