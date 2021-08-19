from config import Configuration
from collections import Counter
from typing import List

import ms3
import pandas as pd

from musif.extract.features.prefix import get_score_prefix
from pandas import DataFrame

from .__harmony_utils import get_numerals_lists, get_chord_types, get_keyareas, get_chords
from musif.common.constants import RESET_SEQ, get_color

ALPHA = "abcdefghijklmnopqrstuvwxyz"


HARMONIC_RHYTHM = "Harmonic_rhythm"
HARMONIC_RHYTHM_BEATS= "Harmonic_rhythm_beats"

NUMERALS_T='numerals_T'
NUMERALS_D='numerals_D'
NUMERALS_SD='numerals_SD'
NUMERALS_sharp_LN='numerals_#LN'
NUMERALS='numerals_S'

ADDITIONS_4_6_64_74_94='4_6_64_74_94' 
ADDITIONS_9='+9' 
OTHERS_NO_AUG='others_no_+'
OTHERS_AUG='others_+'

###############################################################################
# This function generates a dataframe with the measures and the local key     #
# present in each one of them based on the 'modulations' atribute in the json #
###############################################################################
def compute_modulations(partVoice, partVoice_expanded, modulations):
    try:
        measures = [m.measureNumber for m in partVoice]
        measures_expanded = [m.measureNumber for m in partVoice_expanded]
        
        first_modulation = modulations[0]
        key = []
        for m in modulations[1:]:
            key += [first_modulation[0]] * measures.index(m[1] - first_modulation[1] + 1)
            first_modulation = m
        key += [first_modulation[0]] * (measures[-1] - first_modulation[1] + 1)
        if measures[-1] != measures_expanded[-1]: #there are repetitions TODO: test
            measures_expanded = measures_expanded[measures_expanded.index(measures[-1]):] #change the starting point
            first_modulation = modulations[0]
            for m in modulations[1:]:
                if m[1] <= len(measures_expanded):
                    key += [first_modulation[0]] * measures_expanded.index(m[1] - first_modulation[1] + 1)
                    first_modulation = m
        return pd.DataFrame({'measures_continued': measures_expanded, 'key': key})
    except:
        print('Please, review the format of the modulation\'s indications in the JSON file. It needs to have the following format: [(<local key>, <starting measure>), ... ]')
        return None


def get_harmonic_rhythm(ms3_table, sections)-> dict:
    hr={}
    measures = ms3_table.mc.dropna().tolist()
    playthrough= ms3_table.playthrough.dropna().tolist()

    measures_compressed=[i for j, i in enumerate(measures) if i != measures[j-1]]
    
    chords = ms3_table.chord.dropna().tolist()
    chords_length=len([i for j, i in enumerate(chords) if i != chords[j-1]])
    # beats = ms3_table.mc_onset.dropna().tolist()
    # voice = ['N' if str(v) == 'nan' else v for v in ms3_table.voice.tolist()]
    time_signatures = ms3_table.timesig.tolist()
    
    harmonic_rhythm = chords_length/len(measures_compressed)
    # Cases with no time signature changes
    if len(Counter(time_signatures)) == 1:
        harmonic_rhythm_beats = chords_length/int(time_signatures[0].split('/')[0])
    else:
        #create a timesignatures adapted to measures without repetitions. OR/AND just finde changes in TS and 
        # correlate them with measures to find length of the different periods
        periods_ts=[]
        time_changes=[]
        for t in range(1, len(time_signatures)):
            if time_signatures[t] != time_signatures[t-1]:
                #We find what measure in compressed list corresponds to the change in time signature
                time_changes.append(time_signatures[t-1])

                periods_ts.append(len(measures_compressed[0:playthrough[t-1]])-sum(periods_ts))

        #Calculating harmonuc rythom according to beasts periods
        harmonic_rhythm_beats = chords_length/sum([period * int(time_changes[j].split('/')[0]) for j, period in enumerate(periods_ts)])

    hr[HARMONIC_RHYTHM]=harmonic_rhythm
    hr[HARMONIC_RHYTHM_BEATS]=harmonic_rhythm_beats

    # voice_measures = get_measures_per_possibility(list(set(voice)), measures, voice, beats, time_signatures)
    # annotations_voice = {'Voice': voice.count(1), 'No_voice': voice.count(0)}
    # voice_measures['Voice'] = voice_measures.pop(1) if 1 in voice_measures else 0
    # voice_measures['No_voice'] = voice_measures.pop(0) if 0 in voice_measures else 0

    # everything = dict(voice_measures)#, **measures_section)
    # list_annotations = dict(annotations_voice)#, **annotations_sections)
    
    # for k in everything:
    #     everything[k] = round(everything[k]/list_annotations[k] if list_annotations[k] != 0 else 0, 2)
    
    # avg = sum(list(everything.values())) / (len(everything))
    # return dict(everything, **{'Average': avg})

    return hr

def get_numerals(lausanne_table):
    numerals = lausanne_table.numeral.dropna().tolist()
    keys = lausanne_table.globalkey.dropna().tolist()
    relativeroots = lausanne_table.relativeroot.tolist()
    """
    list_grouppings = []
    for x, i in enumerate(numerals):
        #TODO cuando tengamos los chords de 3, ver cómo coger los grouppings
        if str(relativeroot[x]) != 'nan': # or '/' in chord
            major = relativeroot[x].isupper()
        else: 
            major = keys[x].isupper()
        grouping = harmonic_analysis['NFLG2M' if major else 'NFLG2m'].tolist()
        
        try:
            first_characters = parse_chord(i)
            grado = numerals_defined.index(first_characters)
            a = grouping[grado]    
            if str(a) == 'nan':
                print('nan numeral with ', i) #TODO: #vii sigue fallando, major no se coge bien. Repasar las condiciones
            list_general_groupings.append(a)
        except:
            print('Falta el numeral: ', i) """

    _, ng2 = get_numerals_lists(numerals, relativeroots, keys)
    numerals_counter = Counter(ng2)
    
    nc = {}
    for n in numerals_counter:
        nc['Numerals_'+str(n)] = round((numerals_counter[n]/sum(list(numerals_counter.values()))), 2)
    return nc 



def get_additions(lausanne_table):
    additions = lausanne_table.changes.tolist()
    additions_cleaned = []
    for i, a in enumerate(additions):
        if isinstance(a, int):
            # a_int = 
            additions_cleaned.append(int(a))
        else:
            additions_cleaned.append(str(a))

    a_c = Counter(additions_cleaned)


    additions_counter = {ADDITIONS_4_6_64_74_94: 0, 
                        ADDITIONS_9: 0,
                        OTHERS_NO_AUG: 0, 
                        OTHERS_AUG: 0}

    for a in a_c:
        c = a_c[a]
        a = str(a)
        
        if a == '+9':
            additions_counter[ADDITIONS_9] = c
        elif a in ['4', '6', '64', '74', '94', '4.0', '6.0', '64.0', '74.0', '94.0']:
            additions_counter[ADDITIONS_4_6_64_74_94] += c
        elif '+' in a:
            additions_counter[OTHERS_AUG] += c
        else:
            additions_counter[OTHERS_NO_AUG] += c

    ad = {}
    for a in additions_counter:
        if additions_counter[a] != 0:
            ad['additions_'+str(a)] = additions_counter[a] / sum(list(additions_counter.values()))
    return ad

def get_harmony_data(score_data: dict, harmonic_analysis: DataFrame, sections: list = None) -> dict:
    
    # 1. Harmonic_rhythm
    harmonic_rhythm = get_harmonic_rhythm(harmonic_analysis, sections)
    # harmonic_rhythm = {'Harmonic rhythm_'+k: hr[k] for k in hr}

    # 2. Modulations TODO: revisar 

    ### --- DEPENDE DE SECTIONS Y NO TENEMOS YET ---
    # modulations = get_modulations(harmonic_analysis, sections, major = score_data['mode'] == 'major')
    # 3. Numerals
    numerals = get_numerals(harmonic_analysis)
    # 4. Chord_types
    chord_types = get_chord_types(harmonic_analysis) 
    # 5. Additions
    additions = get_additions(harmonic_analysis)

    # key_name = str(score_data['key']).split(" ")[0].strip().replace('-','b') #coger solo la string de antes del espacio? y así quitar major y minor
    # key_name = key_name if score_data['mode'] == 'major' else key_name.lower()
    # score_data['key'] = key_name

    return dict( **harmonic_rhythm, **numerals, **chord_types, **additions)#, **modulations) #score_data was also returned before

def parse_score(mscx_file: str, cfg: Configuration):
    harmonic_analysis = None
    # annotations=msc3_score.annotations
    has_table = True
    try:
        cfg.read_logger.info(get_color('INFO')+'Getting harmonic analysis...' + RESET_SEQ)
        msc3_score = ms3.score.Score(mscx_file, logger_cfg={'level':'ERROR'})
        harmonic_analysis = msc3_score.mscx.expanded
        mn = ms3.parse.next2sequence(msc3_score.mscx.measures.set_index('mc').next)
        mn = pd.Series(mn, name='mc_playthrough')
        harmonic_analysis = ms3.parse.unfold_repeats(harmonic_analysis,mn)
    
    except Exception as e:
        cfg.read_logger.error(get_color('ERROR')+'An error occurred parsing the score {}: {}{}'.format(mscx_file,e, RESET_SEQ))
        with open('failed_files.txt', 'a') as file:  # Use file to refer to the file object
            file.write(str(mscx_file) + '\n')

        harmonic_analysis_expanded = None
        has_table = False

    return harmonic_analysis, has_table

def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    features={}
    sections=[]
    try:
        #### GET FILE FROM LAUSSANE OR FROM MODULATIONS IN THE JSON_DATA ####
        # modulations = json_data['Modulations'] if 'Modulations' in json_data and len(json_data['Modulations']) != 0 else None
        # gv = dict(name_variables, **excel_variables, **general_variables, **grouped_variables, **scoring_variables, **clef_dic, **total) 
        if 'mscx_path' in score_data:
            
            path=score_data['mscx_path']
            # This takes a while!!
            harmonic_analysis, has_table = parse_score(path, cfg)
            has_table = True

        # elif modulations is not None: # The user may have written only the not-expanded version
        #     has_table = True

        #     if modulations is not None and harmonic_analysis is None:
        #         harmonic_analysis = compute_modulations(partVoice, partVoice_expanded, modulations) #TODO: Ver qué pasa con par voice y como se puede hacer con la info que tenemos
        # #         pass
                    # Obtain score sections:
                    # sections = musical_form.get_form_measures(score, repeat_elements) #TODO: prove functionality
            
            score = score_data['score']
            repeat_elements= score_data['repetition_elements']
            score_prefix = get_score_prefix()

        else:
            has_table = False
            harmonic_analysis = None
            cfg.read_logger.warn(get_color('WARNING')+'No Musescore file was found.'+ RESET_SEQ)
            return {}

        #     Get the array based on harmonic_analysis.mc
        # sections = continued_sections(sections, harmonic_analysis.mc)
        if harmonic_analysis is not None:
            ################
            # HARMONY DATA #
            ################
            
            all_harmonic_info = get_harmony_data(score_data, harmonic_analysis, sections)
            
            # #############
            # # KEY AREAS #
            # #############

            keyareas = get_keyareas(harmonic_analysis, major = score_data['mode'] == 'major')

            # #############
            # #  CHORDS   #
            # #############

            chords, chords_g1, chords_g2 = get_chords(harmonic_analysis)

            ## COLLECTING FEATURES 

            #Harmonic Rhythm
            features[f"{HARMONIC_RHYTHM}"] = all_harmonic_info[HARMONIC_RHYTHM]
            features[f"{HARMONIC_RHYTHM_BEATS}"] = all_harmonic_info[HARMONIC_RHYTHM_BEATS]
            
            #NUMERALS
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.startswith('numerals')})
            
            # KEY AREAS
            features.update({k:v for (k, v) in keyareas.items()})
            
            # CHORD TYPES
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.startswith('chord_types_')})
            
            #CHORDS
            features.update({k:v for (k, v) in chords.items() if k.startswith('chords_')})
            features.update({k:v for (k, v) in chords_g1.items() if k.startswith('chords_')})
            features.update({k:v for (k, v) in chords_g2.items() if k.startswith('chords_')})

            # ADDITIONS
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.startswith('additions_')})
        return features

    except Exception as e:
        cfg.read_logger.error('Harmony problem found: ', e)
        return features
