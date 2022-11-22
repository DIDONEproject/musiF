from statistics import mean

from typing import List, Optional


from musif.extract.constants import DATA_PART_ABBREVIATION, VOICES_LIST


def _filter_parts_data(
    parts_data: List[dict], parts_filter: Optional[List[str]]
) -> List[dict]:

    if parts_filter is None:
        return parts_data

    if "voice" in parts_filter:
        parts_filter.remove("voice")
        parts_filter.extend(VOICES_LIST)

    parts_filter_set = set(parts_filter)

    return [
        part_data
        for part_data in parts_data
        if part_data[DATA_PART_ABBREVIATION] in parts_filter_set
    ]


def _part_matches_filter(
    part_abbreviation: str, parts_filter: Optional[List[str]]
) -> bool:

    if parts_filter is None:
        return True
    parts_filter_set = set(parts_filter)
    return part_abbreviation in parts_filter_set


# shouldn't this function stay in musif.extract.features.interval.common?
# it's used only there...
def _mix_data_with_precedent_data(prev_features: dict, new_features: dict) -> None:

    for key in new_features.keys():
        if "max" in key.lower() or "highest" in key.lower():
            prev_features[key] = max(prev_features[key], new_features[key])

        elif "min" in key.lower() or "lowest" in key.lower():
            # shouldn't this be min?
            prev_features[key] = max(prev_features[key], new_features[key])

        if type(new_features[key]) != str:
            # this is run even if we have used max and min...it looks uncorrect
            prev_features[key] = mean([prev_features[key], new_features[key]])
