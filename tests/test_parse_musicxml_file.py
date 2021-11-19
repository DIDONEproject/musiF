from os import path
import pytest

from musif.extract.exceptions import ParseFileError
from musif.extract.extract import parse_musicxml_file, _cache

test_file = path.join("data", "static", "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
test_file_content = path.join("data", "arias_test", "Dem01M-O_piu-1735-Leo[1.01][0430].xml")
test_file_content1 = path.join("data", "arias_tests1", "Dem01M-O_piu-1735-Leo[1.01][0430].xml")
incomplete_file = path.join("data", "arias_test", "incomplete.xml")
malformed_file = path.join("data", "arias_test", "malformed.xml")


class TestParseMusicXMLFile:

    def test_parse_musicxml_basic(self):
        # GIVEN
        split_keywords = []

        # WHEN
        score = parse_musicxml_file(test_file, split_keywords)

        # THEN
        assert score is not None

    def test_parse_musicxml_with_keywords(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN
        score = parse_musicxml_file(test_file, split_keywords)

        # THEN
        assert score is not None

    def test_parse_musicxml_with_repeats(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN
        score = parse_musicxml_file(test_file, split_keywords, expand_repeats=True)

        # THEN
        assert score is not None

    def test_parse_musicxml_incomplete_file(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file(incomplete_file, split_keywords)

    def test_parse_musicxml_incomplete_file_not_saved_cache(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]
        try:
            parse_musicxml_file(incomplete_file, split_keywords)
        except ParseFileError:
            pass

        # WHEN/THEN
        assert _cache.get(incomplete_file) is None

    def test_parse_musicxml_wrong_path(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file("wrong_path", split_keywords)

    def test_parse_musicxml_wrong_path_not_saved_cache(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]
        try:
            parse_musicxml_file("wrong_path", split_keywords)
        except ParseFileError:
            pass

        # WHEN/THEN
        assert _cache.get("wrong_path") is None

    def test_parse_musicxml_malformed_file(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file(malformed_file, split_keywords)

    def test_parse_musicxml_malformed_file_not_saved_cache(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]
        try:
            parse_musicxml_file(malformed_file, split_keywords)
        except ParseFileError:
            pass

        # WHEN/THEN
        assert _cache.get(malformed_file) is None

    def test_parse_musicxml_score_in_cache(self):
        # GIVEN
        split_keywords = []

        # WHEN
        score = parse_musicxml_file(test_file, split_keywords)

        # THEN
        assert _cache.get(test_file) is not None

    def test_parse_musicxml_score_in_cache_same_content(self):
        # GIVEN
        split_keywords = []

        # WHEN
        score = parse_musicxml_file(test_file_content, split_keywords)
        score1 = parse_musicxml_file(test_file_content1, split_keywords)

        # THEN
        assert _cache.get(test_file) != _cache.get(test_file_content1)

