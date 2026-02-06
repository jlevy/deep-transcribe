from __future__ import annotations

from deep_transcribe.cli_main import build_parser, get_app_version


def test_build_parser_creates_parser():
    parser = build_parser()
    assert parser is not None
    assert parser.prog is not None


def test_parse_url_argument():
    parser = build_parser()
    args = parser.parse_args(["https://youtube.com/watch?v=test"])
    assert args.url == "https://youtube.com/watch?v=test"


def test_parse_basic_preset():
    parser = build_parser()
    args = parser.parse_args(["--basic", "https://example.com/video"])
    assert args.basic
    assert not args.formatted
    assert not args.annotated
    assert not args.deep


def test_parse_formatted_preset():
    parser = build_parser()
    args = parser.parse_args(["--formatted", "https://example.com/video"])
    assert args.formatted


def test_parse_annotated_preset():
    parser = build_parser()
    args = parser.parse_args(["--annotated", "https://example.com/video"])
    assert args.annotated


def test_parse_deep_preset():
    parser = build_parser()
    args = parser.parse_args(["--deep", "https://example.com/video"])
    assert args.deep


def test_parse_with_flags():
    parser = build_parser()
    args = parser.parse_args(["--with", "format,research_paras", "https://example.com/video"])
    assert args.with_flags == "format,research_paras"


def test_parse_mcp_mode():
    parser = build_parser()
    args = parser.parse_args(["--mcp"])
    assert args.mcp
    assert args.url is None


def test_parse_sse_mode():
    parser = build_parser()
    args = parser.parse_args(["--sse"])
    assert args.sse


def test_parse_logs_mode():
    parser = build_parser()
    args = parser.parse_args(["--logs"])
    assert args.logs


def test_parse_workspace():
    parser = build_parser()
    args = parser.parse_args(["--workspace", "/tmp/test", "https://example.com/video"])
    assert args.workspace == "/tmp/test"


def test_parse_language():
    parser = build_parser()
    args = parser.parse_args(["--language", "es", "https://example.com/video"])
    assert args.language == "es"


def test_default_workspace():
    parser = build_parser()
    args = parser.parse_args(["https://example.com/video"])
    assert args.workspace == "./transcriptions"


def test_default_language():
    parser = build_parser()
    args = parser.parse_args(["https://example.com/video"])
    assert args.language == "en"


def test_get_app_version_returns_string():
    v = get_app_version()
    assert isinstance(v, str)
    # Either "vX.Y.Z" or "unknown" depending on install state
    assert v.startswith("v") or v == "unknown"


def test_no_minify_flag():
    parser = build_parser()
    args = parser.parse_args(["--no_minify", "https://example.com/video"])
    assert args.no_minify


def test_rerun_flag():
    parser = build_parser()
    args = parser.parse_args(["--rerun", "https://example.com/video"])
    assert args.rerun
