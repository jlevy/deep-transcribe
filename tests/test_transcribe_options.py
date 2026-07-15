from __future__ import annotations

from deep_transcribe.transcribe_options import TranscribeOptions


def test_presets_enable_expected_pipeline_stages():
    formatted = TranscribeOptions.formatted()
    annotated = TranscribeOptions.annotated()
    deep = TranscribeOptions.deep()

    assert formatted.get_enabled_options() == ["identify_speakers", "format"]
    assert not formatted.insert_section_headings
    assert annotated.insert_section_headings
    assert annotated.add_summary_bullets
    assert annotated.add_description
    assert annotated.insert_frame_captures
    assert not annotated.research_paras
    assert deep.research_paras


def test_with_flags_parse_whitespace_and_reject_unknown_names():
    options = TranscribeOptions.from_with_flags("format , identify_speakers,research_paras")

    assert options.format
    assert options.identify_speakers
    assert options.research_paras
    assert not options.add_description

    try:
        TranscribeOptions.from_with_flags("unknown")
        raise AssertionError("Expected ValueError for unknown option")
    except ValueError as error:
        assert "unknown" in str(error)
        assert "Valid options" in str(error)


def test_merge_preserves_enabled_options_from_both_inputs():
    merged = TranscribeOptions(research_paras=True).merge_with(
        TranscribeOptions(add_description=True)
    )

    assert merged.research_paras
    assert merged.add_description
    assert len(merged.get_enabled_options()) == 2
