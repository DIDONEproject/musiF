import glob
from os import path
from pathlib import Path
from typing import Dict, List, Tuple

from music21.converter import parse
from music21.stream import Part, Score
from pandas import DataFrame
from tqdm import tqdm

from musif.common.cache import Cache
from musif.common.constants import GENERAL_FAMILY
from musif.common.sort import sort
from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.features import ambitus, custom, density, harmony, interval, key, lyrics, metadata, scale, scoring, \
    tempo, text, texture
from musif.extract.features.density import get_notes_and_measures
from musif.extract.features.key import get_key_and_mode
from musif.extract.features.scoring import ROMAN_NUMERALS_FROM_1_TO_20, extract_abbreviated_part, extract_sound, \
    to_abbreviation
from musif.musicxml import (MUSESCORE_FILE_EXTENSION, MUSICXML_FILE_EXTENSION, analysis, expand_part,
                            expand_score_repetitions, extract_numeric_tempo, get_intervals, get_notes_lyrics,
                            get_repetition_elements,
                            split_layers)

_cache = Cache(10000)  # To cache scanned scores


def parse_file(file_path: str, split_keywords) -> Score:
    score = _cache.get(file_path)
    if score is None:
        score = parse(file_path)
        split_layers(score, split_keywords)
        _cache.put(file_path, score)
    return score


class FilesExtractor:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)

    def extract(self, obj) -> List[str]:
        if not (isinstance(obj, list) or isinstance(obj, str)):
            raise ValueError(f"Unexpected argument {obj} should be a directory, a file path or a list of files paths")
        musicxml_files = []
        if isinstance(obj, list):
            musicxml_files = list(obj)
        if isinstance(obj, str):
            musicxml_files = glob.glob(path.join(obj, f"*.{MUSICXML_FILE_EXTENSION}")) if path.isdir(obj) else [obj]
        return musicxml_files


class PartsExtractor:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)
        self._files_extractor = FilesExtractor(*args, **kwargs)

    def extract(self, obj) -> List[str]:
        musicxml_files = self._files_extractor.extract(obj)
        parts = list({part for musicxml_file in musicxml_files for part in self._process_score(musicxml_file)})
        abbreviated_parts_scoring_order = [instr + num
                                           for instr in self._cfg.scoring_order
                                           for num in [''] + ROMAN_NUMERALS_FROM_1_TO_20]
        return sort(parts, abbreviated_parts_scoring_order)

    def _process_score(self, musicxml_file: str) -> List[str]:
        score = parse_file(musicxml_file, self._cfg.split_keywords)
        parts = list(score.parts)
        parts_abbreviations = [self._get_part(part, parts) for part in parts]
        return parts_abbreviations

    def _get_part(self, part: Part, parts: List[Part]) -> str:
        sound = extract_sound(part, self._cfg)
        part_abbreviation, _, _ = extract_abbreviated_part(sound, part, parts, self._cfg)
        return part_abbreviation


class FilesValidator:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)
        self._files_extractor = FilesExtractor(*args, **kwargs)

    def validate(self, obj) -> None:
        musicxml_files = self._files_extractor.extract(obj)
        for musicxml_file in tqdm(musicxml_files):
            print(f"Validating file: {musicxml_file}")
            parse_file(musicxml_file, self._cfg.split_keywords)


class FeaturesExtractor:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)
        self._files_extractor = FilesExtractor(*args, **kwargs)
        self._logger = self._cfg.read_logger

    def extract(self, obj, parts_filter: List[str] = None) -> DataFrame:
        musicxml_files = self._files_extractor.extract(obj)
        parts_df, score_df, corpus_df = self._process_corpora(musicxml_files, parts_filter)
        return score_df

    def _process_corpora(self, musicxml_files: List[str], parts_filter: List[str] = None) -> Tuple[DataFrame, DataFrame, DataFrame]:
        corpus_by_dir = self._group_by_dir(musicxml_files)
        all_corpus_features = []
        all_scores_features = []
        all_parts_features = []
        for corpus_dir, files in corpus_by_dir.items():
            scores_data, parts_data, scores_features, parts_features = self._process_corpus(files, parts_filter)
            corpus_features = self._extract_corpus_features(corpus_dir, scores_data, parts_data, scores_features)
            all_corpus_features.append(corpus_features)
            all_scores_features.extend(scores_features)
            all_parts_features.extend(parts_features)
        df_corpus = DataFrame(all_corpus_features)
        df_corpus = df_corpus.reindex(sorted(df_corpus.columns), axis=1)
        df_scores = DataFrame(all_scores_features)
        df_scores = df_scores.reindex(sorted(df_scores.columns), axis=1)
        df_parts = DataFrame(all_parts_features)
        df_parts = df_parts.reindex(sorted(df_parts.columns), axis=1)
        return df_corpus, df_scores, df_parts

    @staticmethod
    def _group_by_dir(files: List[str]) -> Dict[str, List[str]]:
        corpus_by_dir = {}
        for file in files:
            corpus_dir = path.dirname(file)
            if corpus_dir not in corpus_by_dir:
                corpus_by_dir[corpus_dir] = []
            corpus_by_dir[corpus_dir].append(file)
        return corpus_by_dir

    def _process_corpus(self, musicxml_files: List[str], parts_filter: List[str] = None) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
        if self._cfg.parallel:
            return self._process_corpus_in_parallel(musicxml_files, parts_filter)
        return self._process_corpus_sequentially(musicxml_files, parts_filter)

    def _process_corpus_sequentially(
        self,
        musicxml_files: List[str],
        parts_filter: List[str] = None
    ) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
        corpus_scores_data = []
        corpus_parts_data = []
        scores_features = []
        parts_features = []
        for musicxml_file in tqdm(musicxml_files):
            score_data, parts_data, score_features, score_parts_features = self._process_score(musicxml_file, parts_filter)
            corpus_scores_data.append(score_data)
            corpus_parts_data.extend(parts_data)
            scores_features.append(score_features)
            parts_features.extend(score_parts_features)
        return corpus_scores_data, corpus_parts_data, scores_features, parts_features

    def _process_corpus_in_parallel(
        self,
        musicxml_files: List[str],
        parts_filter: List[str] = None
    ) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
        corpus_scores_data = []
        corpus_parts_data = []
        scores_features = []
        parts_features = []

        # with ProcessPoolExecutor(max_workers=self._cfg.max_processes) as executor:
        #     futures = [executor.submit(process_score, (self, musicxml_file, parts_filter)) for musicxml_file in musicxml_files]
        #     for _ in tqdm(as_completed(futures), total=len(futures)):
        #         pass
        #     for future in futures:
        # score_data, parts_data, score_features, score_parts_features = future.result()
        # corpus_scores_data.append(score_data)
        # corpus_parts_data.extend(parts_data)
        # scores_features.append(score_features)
        # parts_features.extend(score_parts_features)
        return corpus_scores_data, corpus_parts_data, scores_features, parts_features

    def _process_score(self, musicxml_file: str, parts_filter: List[str] = None) -> Tuple[dict, List[dict], dict, List[dict]]:
        self._logger.info(f"Processing score {musicxml_file}")
        score_data = self._get_score_data(musicxml_file, parts_filter)
        parts_data = [self._get_part_data(score_data, part) for part in score_data["score"].parts]
        parts_features = [self._extract_part_features(score_data, part_data)
                          for part_data in filter_parts_data(parts_data, score_data["parts_filter"])]
        score_features = self._extract_score_features(score_data, parts_data, parts_features)
        return score_data, parts_data, score_features, parts_features

    def _get_score_data(self, musicxml_file: str, parts_filter: List[str] = None) -> dict:
        score = parse_file(musicxml_file, self._cfg.split_keywords)
        repetition_elements = get_repetition_elements(score)
        score_expanded = expand_score_repetitions(score, repetition_elements)
        tempo = extract_numeric_tempo(musicxml_file)
        if self._cfg.require_harmonic_analysis:
            mscx_name = self._find_mscx_file(musicxml_file)
        score_key, tonality, mode = get_key_and_mode(score)
        ambitus = analysis.discrete.Ambitus()
        parts = self._filter_parts(score, parts_filter)
        if len(parts) == 0:
            self._cfg.read_logger.warning(f"No parts were found for file {musicxml_file} and filter: {','.join(parts_filter)}")
        data = {
            "score": score,
            "file": musicxml_file,
            "numeric_tempo": tempo,
            "repetition_elements": repetition_elements,
            "score_expanded": score_expanded, ## es util??
            "key": score_key,
            "tonality": tonality,
            "mode": mode,
            "ambitus": ambitus,
            "parts": parts,
            "parts_filter": parts_filter,
        }
        if self._cfg.require_harmonic_analysis:
            data["mscx_path"] = mscx_name
        return data

    def _find_mscx_file(self, musicxml_file: str) -> Path:
        try:
            mscx_path=musicxml_file.replace(MUSICXML_FILE_EXTENSION, MUSESCORE_FILE_EXTENSION)
        except FileNotFoundError:
            self._cfg.read_logger.info("Musescore file was not found for {} file!".format(musicxml_file))
            mscx_path=None
        return mscx_path

    def _filter_parts(self, score: Score, parts_filter: List[str] = None) -> List[Part]:
        if parts_filter is None:
            return list(score.parts)
        filter = set(parts_filter)
        parts = list(score.parts)
        return [part for part in parts if to_abbreviation(part, parts, self._cfg) in filter]

    def _get_part_data(self, score_data: dict, part: Part) -> dict:
        expanded_part = expand_part(part, score_data["repetition_elements"])
        notes, sounding_measures, measures = get_notes_and_measures(expanded_part)
        lyrics = get_notes_lyrics(notes)
        numeric_intervals, text_intervals = get_intervals(notes)
        ambitus_solution = score_data["ambitus"].getSolution(part)
        ambitus_pitch_span = score_data["ambitus"].getPitchSpan(part)
        sound = extract_sound(part, self._cfg)
        part_abbreviation, sound_abbreviation, part_number = extract_abbreviated_part(sound, part, score_data["parts"], self._cfg)
        family = self._cfg.sound_to_family.get(sound, GENERAL_FAMILY)
        family_abbreviation = self._cfg.family_to_abbreviation[family]
        data = {
            "part": part,
            "part_number": part_number,
            "abbreviation": part_abbreviation,
            "sound": sound,
            "sound_abbreviation": sound_abbreviation,
            "family": family,
            "family_abbreviation": family_abbreviation,
            "expanded_part": expanded_part,
            "notes": notes,
            "lyrics": lyrics,
            "sounding_measures": sounding_measures,
            "measures": measures,
            "numeric_intervals": numeric_intervals,
            "text_intervals": text_intervals,
            "ambitus_solution": ambitus_solution,
            "ambitus_pitch_span": ambitus_pitch_span,
        }
        return data

    def _extract_part_features(self, score_data: dict, part_data: dict) -> dict:
        self._logger.debug(f"Extracting all part \"{part_data['abbreviation']}\" features.")
        part_features = {}
        part_features.update(self._extract_part_module_features(scoring, score_data, part_data, part_features))
        part_features.update(self._extract_part_module_features(tempo, score_data, part_data, part_features))
        part_features.update(self._extract_part_module_features(lyrics, score_data, part_data, part_features))
        part_features.update(self._extract_part_module_features(interval, score_data, part_data, part_features))
        part_features.update(self._extract_part_module_features(ambitus, score_data, part_data, part_features))
        part_features.update(self._extract_part_module_features(scale, score_data, part_data, part_features))
        part_features.update(self._extract_part_module_features(density, score_data, part_data, part_features))
        self._logger.debug(f"Finished extraction of all part \"{part_data['abbreviation']}\" features.")
        return part_features

    def _extract_part_module_features(self, module, score_data: dict, part_data: dict, part_features: dict) -> dict:
        self._logger.debug(f"Extracting part \"{part_data['abbreviation']}\" {module.__name__} features.")
        return module.get_part_features(score_data, part_data, self._cfg, part_features)

    def _extract_score_features(self, score_data: dict, parts_data: List[dict], parts_features: List[dict]) -> dict:
        self._logger.debug(f"Extracting all score \"{score_data['file']}\" features.")
        score_features = {"FileName": path.basename(score_data["file"])}
        score_features.update(self._extract_score_module_features(custom, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(text, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(metadata, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(key, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(tempo, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(scoring, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(lyrics, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(interval, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(ambitus, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(scale, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(density, score_data, parts_data, parts_features, score_features))
        score_features.update(self._extract_score_module_features(texture, score_data, parts_data, parts_features, score_features))
        # score_features.update(self._extract_score_module_features(harmony,  score_data, parts_data, parts_features, score_features))
        self._logger.debug(f"Finished extraction of all score \"{score_data['file']}\" features.")
        return score_features

    def _extract_score_module_features(self, module, score_data: dict, parts_data: List[dict], parts_features: List[dict], score_features: dict) -> dict:
        self._logger.debug(f"Extracting score \"{score_data['file']}\" {module.__name__} features.")
        return module.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features)

    def _extract_corpus_features(self, corpus_dir: str, scores_data: List[dict], parts_data: List[dict], scores_features: List[dict]) -> dict:
        self._logger.debug(f"Extracting all corpus \"{corpus_dir}\" features.")
        corpus_features = {"Corpus": corpus_dir}
        corpus_features.update(self._extract_corpus_module_features(corpus_dir, custom, scores_data, parts_data, scores_features, corpus_features))
        corpus_features.update(self._extract_corpus_module_features(corpus_dir, key, scores_data, parts_data, scores_features, corpus_features))
        corpus_features.update(self._extract_corpus_module_features(corpus_dir, tempo, scores_data, parts_data, scores_features, corpus_features))
        corpus_features.update(self._extract_corpus_module_features(corpus_dir, scoring, scores_data, parts_data, scores_features, corpus_features))
        corpus_features.update(self._extract_corpus_module_features(corpus_dir, lyrics, scores_data, parts_data, scores_features, corpus_features))
        corpus_features.update(self._extract_corpus_module_features(corpus_dir, interval, scores_data, parts_data, scores_features, corpus_features))
        corpus_features.update(self._extract_corpus_module_features(corpus_dir, density, scores_data, parts_data, scores_features, corpus_features))
        self._logger.debug(f"Finished extraction of all corpus \"{corpus_dir}\" features.")
        return corpus_features

    def _extract_corpus_module_features(self, corpus_dir: str, module, scores_data: List[dict], parts_data: List[dict], scores_features: List[dict], corpus_features: dict) -> dict:
        self._logger.debug(f"Extracting corpus \"{corpus_dir}\" {module.__name__} features.")
        return module.get_corpus_features(scores_data, parts_data, self._cfg, scores_features, corpus_features)

