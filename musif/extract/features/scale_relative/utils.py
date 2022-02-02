from collections import Counter
from itertools import chain
from typing import List, Union

import pandas as pd
import roman
from music21 import pitch, scale
from music21.note import Note
from pandas.core.frame import DataFrame
from musif.common.sort import sort_dict

from musif.extract.features.core.handler import DATA_KEY
from musif.extract.features.harmony.utils import (get_function_first,
                                                  get_function_second)

accidental_abbreviation = {"": "", "sharp": "#", "flat": "b", "double-sharp": "x", "double-flat": "bb"}


def get_keys_functions(list_keys, mode):
    result_dict = {t: get_function_first(t, mode) for t in set(list_keys)}
    first_function = [result_dict[t] for t in list_keys]
    second_function = [get_function_second(g1) for g1 in first_function]
    return first_function, second_function
    
def continued_sections(sections: list, mc):
    extended_sections = []
    repeated_measures = Counter(mc)
    for i, c in enumerate(repeated_measures):
        extended_sections.append([sections[i]] * repeated_measures[c])
    return list(chain(*extended_sections))
    
def IsAnacrusis(harmonic_analysis):
    return harmonic_analysis.mn.dropna().tolist()[0] == 0
    
def get_tonality_per_beat(harmonic_analysis, tonality):
    tonality_map = {}
    for index, degree in enumerate(harmonic_analysis.localkey):
        beat = harmonic_analysis.beats[index]
        tonality_map[beat] = get_localTonalty(tonality, degree.strip())

    # Fill measures without a value
    if 0 not in tonality_map:
        tonality_map[0]=tonality_map[1] if 1 in tonality_map else tonality_map[2]
        
    for beat in range(1, max(list(tonality_map.keys()))):
        if beat not in tonality_map.keys():
            tonality_map[beat] = tonality_map[beat-1]

    tonality_map=sort_dict(tonality_map, sorted(tonality_map.keys()))
    return tonality_map


def get_emphasised_scale_degrees_relative(notes_list: list, score_data: dict) -> List[list]:
    harmonic_analysis, tonality = extract_harmony(score_data)
    tonality_map = get_tonality_per_beat(harmonic_analysis, tonality)
    emph_degrees = get_emphasized_degrees(notes_list, tonality_map)
    
    return emph_degrees

def get_emphasized_degrees(notes_list: List[Note], tonality_map: dict)-> dict:
    local_tonality=''
    notes_per_degree_relative = {
        to_full_degree(degree, accidental): 0
        for accidental in ["", "sharp", "flat"]
        for degree in [1, 2, 3, 4, 5, 6, 7]
    }

    for j, note in enumerate(notes_list):
        if note.isChord:
          note = note[0]

        note_name = note.name
        note_offset = int(note.offset) + 1 #music21 starts offsets in 0

        if note_offset is None:
            note_offset = notes_list[j-1].offset

        if note_offset in tonality_map:
            local_tonality = tonality_map[note_offset]

        degree_value = get_note_degree(local_tonality, note_name)

        if str(degree_value) not in notes_per_degree_relative:
            notes_per_degree_relative[str(degree_value)] = 1
        else:
            notes_per_degree_relative[str(degree_value)] += 1

    return notes_per_degree_relative


def get_modulations(lausanne_table: DataFrame, sections, major = True):
    keys = lausanne_table.localkey.dropna().tolist()
    grouping, _ = get_keys_functions(keys, mode = 'M' if major else 'm')
    modulations_sections = {group:[] for group in grouping}
    last_key = ''
    for i, key in enumerate(keys):
        if (key.lower() != 'i') and key != last_key:
            section = sections[i]
            last_key = key
            modulation = grouping[i]
            modulations_sections[modulation].append(section)

        if last_key == key and sections[i] != section:
            section = sections[i]
            modulations_sections[modulation].append(section)
    
    ms = {}
    for m in modulations_sections:
        if len(modulations_sections[m]) != 0:
            ms['Modulations'+str(m)] = len(list(set(modulations_sections[m])))
    return ms

def extract_harmony(score_data):
    harmonic_analysis=score_data.get('MS3_score', pd.DataFrame())

    tonality=str(score_data[DATA_KEY])
    # measures = harmonic_analysis.mc.dropna().tolist() if IsAnacrusis(harmonic_analysis) else harmonic_analysis.mn.dropna().tolist()

    return harmonic_analysis, tonality


def get_note_degree(key, note):
  if key[0].isupper():
    scl = scale.MajorScale(key.split(' ')[0])
  else:
    scl = scale.MinorScale(key.split(' ')[0])

  degree = scl.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch(note))
  accidental = degree[1].fullName if degree[1] != None else ''

  acc = ''
  if accidental == 'sharp':
    acc = '#'
  elif accidental == 'flat':
    acc = 'b'
  elif accidental == 'double-sharp':
    acc = 'x'
  elif accidental == 'double-flat':
    acc = 'bb'

  return acc + str(degree[0])
            
def get_localTonalty(globalkey, degree):
    accidental=''
    if '#' in degree:
        accidental = '#'
        degree = degree.replace('#', '')

    elif 'b' in degree:
        accidental = '-'
        degree = degree.replace('b', '')

    degree_int = roman.fromRoman(degree.upper())

    if 'major' in globalkey:
        pitch_scale = scale.MajorScale(globalkey.split()[0]).pitchFromDegree(degree_int).name 
    else:
        pitch_scale = scale.MinorScale(globalkey.split(' ')[0]).pitchFromDegree(degree_int).name 
    
    if ('#' or 'b') in [char for char in pitch_scale][-1:]: #checks for exceptions in which we already have an accidental
        modulation= scale.MajorScale(globalkey.split()[0]).pitchFromDegree(degree_int-1).name if 'major' in globalkey else scale.MinorScale(globalkey.split(' ')[0]).pitchFromDegree(degree_int-1).name 

    else:
        modulation = pitch_scale + accidental


    return modulation.upper() if degree.isupper() else modulation.lower()

def to_full_degree(degree: Union[int, str], accidental: str) -> str:
    return f"{accidental_abbreviation[accidental]}{degree}"
