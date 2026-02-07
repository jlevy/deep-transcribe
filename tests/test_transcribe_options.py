from __future__ import annotations

from deep_transcribe.transcribe_options import TranscribeOptions


def test_formatted_preset():
    opts = TranscribeOptions.formatted()
    assert opts.identify_speakers
    assert opts.format
    assert not opts.insert_section_headings
    assert not opts.research_paras


def test_annotated_preset():
    opts = TranscribeOptions.annotated()
    assert opts.identify_speakers
    assert opts.format
    assert opts.insert_section_headings
    assert opts.add_summary_bullets
    assert opts.add_description
    assert opts.insert_frame_captures
    assert not opts.research_paras


def test_deep_preset():
    opts = TranscribeOptions.deep()
    assert opts.research_paras
    assert opts.identify_speakers
    assert opts.format
    assert opts.insert_section_headings
    assert opts.add_summary_bullets
    assert opts.add_description
    assert opts.insert_frame_captures


def test_merge_with_or_logic():
    basic = TranscribeOptions.basic()
    formatted = TranscribeOptions.formatted()
    merged = basic.merge_with(formatted)
    assert merged.identify_speakers
    assert merged.format
    assert not merged.insert_section_headings


def test_merge_preserves_existing_flags():
    a = TranscribeOptions(research_paras=True)
    b = TranscribeOptions(add_description=True)
    merged = a.merge_with(b)
    assert merged.research_paras
    assert merged.add_description


def test_from_with_flags_single():
    opts = TranscribeOptions.from_with_flags("format")
    assert opts.format
    assert not opts.identify_speakers


def test_from_with_flags_multiple():
    opts = TranscribeOptions.from_with_flags("format,identify_speakers,research_paras")
    assert opts.format
    assert opts.identify_speakers
    assert opts.research_paras
    assert not opts.add_description


def test_from_with_flags_with_spaces():
    opts = TranscribeOptions.from_with_flags("format , identify_speakers")
    assert opts.format
    assert opts.identify_speakers


def test_from_with_flags_empty():
    opts = TranscribeOptions.from_with_flags("")
    assert opts.get_enabled_options() == []


def test_from_with_flags_invalid():
    try:
        TranscribeOptions.from_with_flags("nonexistent_flag")
        raise AssertionError("Expected ValueError for invalid flag")
    except ValueError as e:
        assert "nonexistent_flag" in str(e)
        assert "Valid options" in str(e)


def test_get_enabled_options_formatted():
    opts = TranscribeOptions.formatted()
    enabled = opts.get_enabled_options()
    assert "identify_speakers" in enabled
    assert "format" in enabled
    assert len(enabled) == 2


def test_get_enabled_options_deep():
    opts = TranscribeOptions.deep()
    enabled = opts.get_enabled_options()
    assert len(enabled) == 7
