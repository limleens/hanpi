"""Dictionary tests: long phrases, exact matches and honest partial glosses."""
from hanpi_core import gloss

class FakeDictionary:
    def get_entry(self, word):
        samples = {"北京": ["Beijing"], "大学": ["university"],
                   "图书馆": ["library"], "咖啡": ["coffee"],
                   "天气": ["weather"]}
        return {"definitions": samples[word]} if word in samples else None

def test_curated_example():
    m = gloss.lookup_meaning("你好")
    assert m.exact and m.text == "Hello"

def test_external_dictionary_word(monkeypatch):
    monkeypatch.setattr(gloss, "_cedict", lambda: FakeDictionary())
    gloss._entry.cache_clear()
    try:
        m = gloss.lookup_meaning("咖啡")
        assert m.exact and "coffee" in m.text
    finally:
        gloss._entry.cache_clear()

def test_longer_phrase_gloss_is_labelled(monkeypatch):
    monkeypatch.setattr(gloss, "_cedict", lambda: FakeDictionary())
    gloss._entry.cache_clear()
    try:
        m = gloss.lookup_meaning("北京大学")
        assert not m.exact and "Beijing" in m.text and "university" in m.text
        assert "not a fluent" in m.note
    finally:
        gloss._entry.cache_clear()

def test_unknown_is_not_hallucinated(monkeypatch):
    monkeypatch.setattr(gloss, "_cedict", lambda: FakeDictionary())
    gloss._entry.cache_clear()
    try:
        m = gloss.lookup_meaning("很")
        assert not m.exact and "?" in m.text
    finally:
        gloss._entry.cache_clear()

def test_lookup_never_automatically_calls_translation():
    assert gloss.lookup_meaning("你好").source == "curated"

def test_live_dictionary_if_installed():
    import pytest
    pytest.importorskip("pycccedict")
    gloss._entry.cache_clear()
    gloss._cedict.cache_clear()
    m = gloss.lookup_meaning("咖啡")
    assert m.exact and "coffee" in m.text.lower()
