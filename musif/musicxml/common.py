import copy
from typing import Dict, List, Tuple, Union

from music21.interval import Interval
from music21.note import Note
from music21.scale import MajorScale, MinorScale
from music21.stream import Measure, Part, Score, Voice
from music21.text import assembleLyrics
from musif.common import group
from roman import toRoman

MUSICXML_FILE_EXTENSION = "xml"

# TODO: Documennt all this module

def is_voice(part: Part) -> bool:
    """
    Returns True if the part is a singer part, otherwise returns False
    
    Parameters
    ----------
    part : Part
      Music21 part to check if it's a singer part
    """

    instrument = part.getInstrument(returnDefault=False)
    if instrument is None or instrument.instrumentSound is None:
        return False
    return "voice" in instrument.instrumentSound

def split_layers(score: Score, split_keywords: List[str]):
    """
    Function used to split possible layers. Those instruments that include to parts in the same staff
    will be separated in two diferent parts so they can be treated separately. 
    
    Parameters
    ----------
    score : Score
        Music21 score to scan and separate parts in it according to split_keywords list
    
    split_keywords: List[str]
        List containing key words of instruments susceptible to be splitted. i.e. [oboe, viola]
      
    """

    final_parts = []
    for part_index, part in enumerate(score.parts):
        instrument = part.getInstrument(returnDefault=False)

        possible_layers = False
        for keyword in split_keywords:
            if keyword in instrument.instrumentSound:
                possible_layers = True
                break

        if possible_layers:
            has_voices = False
            for measure in part.elements:
                if isinstance(measure, Measure) and any(isinstance(e, Voice) for e in measure.elements):
                    has_voices = True
                    break

            if has_voices:  # recorrer los compases buscando las voices y separamos en dos parts
                _separate_info_in_two_parts(score, final_parts, part)
            else:
                final_parts.append(part)  # without any change
                score.remove(part)
        else:
            final_parts.append(part)  # without any change
            score.remove(part)

    for part in final_parts:
        try:
            score.insert(0, part)
        except:
            pass

def get_notes_and_measures(part: Part) -> Tuple[List[Note], List[Note], List[Measure], List[Measure]]:
    """
    Obtains lists of notes, tied notes, measures, measures that containg notes, and notes and rests.
    Information that is useful in the subsequent process of extraction.
    
    Parameters
    ----------
    part : Part
      Music21 part to extract the info from.
      
    """

    measures = list(part.getElementsByClass(Measure))
    sounding_measures = [
        measure for measure in measures if len(measure.notes) > 0]
    original_notes = [note for measure in measures for note in measure.notes]
    notes_and_rests = [
        note for measure in measures for note in measure.notesAndRests]
    tied_notes = _tie_notes(original_notes)
    return original_notes, tied_notes, measures, sounding_measures, notes_and_rests


def _tie_notes(original_notes: List[Note]) -> List[Note]:
    tied_notes = []
    for note in original_notes:
        if not isinstance(note, Note):
            pass
        last_note = tied_notes[-1] if len(tied_notes) > 0 else None
        if _must_be_tied(note, last_note):
            tied_notes[-1].duration.quarterLength += note.duration.quarterLength
        else:
            tied_notes.append(note)
    return tied_notes


def _must_be_tied(elem, last_elem) -> bool:
    if last_elem is None:
        return False
    if not isinstance(elem, Note):
        return False
    if elem.tie is None:
        return False
    if elem.tie.type != "stop" and elem.tie.type != "continue":
        return False
    if not isinstance(last_elem, Note):
        return False
    return True


def _separate_info_in_two_parts(score, final_parts, part):
    parts_splitted = part.voicesToParts().elements
    num_measure = 0
    for measure in part.elements:
        # add missing information to both parts (dynamics, text annotations, etc are missing)
        i = 1
        if isinstance(measure, Measure):
            num_measure += 1
            if any(
                not isinstance(e, Voice) for e in measure.elements
            ):
                not_voices_elements = [
                    e for e in measure.elements if not isinstance(e, Voice)
                ]  # elements such as clefs, dynamics, text annotations...
                for p in parts_splitted:
                    if measure.measureNumber == 0 and isinstance(measure, Measure):
                        number = measure.measureNumber+1
                        # only add elements if we are in am measure
                        if isinstance(p.elements[num_measure], Measure):
                            p.elements[num_measure].elements += tuple(
                                e for e in not_voices_elements if e not in p.elements[num_measure].elements
                            )
                    if measure.measureNumber > 0:
                        if not isinstance(p.elements[num_measure], Measure):
                            continue
                        p.elements[num_measure].elements += tuple(
                            e for e in not_voices_elements if e not in p.elements[num_measure].elements
                        )
    for num, p in enumerate(parts_splitted, 1):
        p_copy = copy.deepcopy(part)  # TODO: this line takes > 10% of the time
        p_copy.id = p_copy.id + " " + toRoman(num)  # only I or II
        p_copy.partName = p_copy.partName + " " + toRoman(num)  # only I or II
        p_copy.elements = p.elements
        final_parts.append(p_copy)
    score.remove(part)  # already inserted


def _get_part_clef(part):
    """
    Extracts the clef in the score by checking the first measure of the part 
    
    Parameters
    ----------
        part : Part
      Music21 part to extract the info from
    
    """
    for elem in part.elements:
        if isinstance(elem, Measure):
            if hasattr(elem, "clef"):
                return elem.clef.sign + "-" + str(elem.clef.line)
    return ""


def get_xml_scoring_variables(score):
    return group.get_scoring(score)


def _get_degrees_and_accidentals(key: str, notes: List[Note]) -> List[Tuple[str, str]]:
    if "major" in key.split():
        scl = MajorScale(key.split(" ")[0])
    else:
        scl = MinorScale(key.split(" ")[0])

    degrees = [scl.getScaleDegreeAndAccidentalFromPitch(
        note.pitches[0]) for note in notes]

    return [(degree[0], degree[1].fullName if degree[1] else "") for degree in degrees]


def _get_intervals(notes: List[Note]) -> List[Interval]:
    # TODO: this takes > 6% of the time
    return [Interval(notes[i].pitches[0], notes[i + 1].pitches[0]) for i in range(len(notes) - 1)]


def _contains_text(part: Part) -> bool:
    return assembleLyrics(part)


def _get_lyrics_in_notes(notes: List[Note]) -> List[str]:
    lyrics = []
    for note in notes:
        if note.lyrics is None or len(note.lyrics) == 0:
            continue
        note_lyrics = [
            syllable.text for syllable in note.lyrics if syllable.text is not None]
        lyrics.extend(note_lyrics)
    return lyrics
