from __future__ import annotations

from deep_transcribe.cli_main import build_parser


def test_parser_accepts_transcription_contract():
    args = build_parser().parse_args(
        [
            "--deep",
            "--no-minify",
            "--workspace",
            "./custom-workspace",
            "--language",
            "multi",
            "--rerun",
            "https://example.com/video",
        ]
    )

    assert args.deep
    assert args.no_minify
    assert args.workspace == "./custom-workspace"
    assert args.language == "multi"
    assert args.rerun
    assert args.url == "https://example.com/video"


def test_parser_allows_mcp_without_url():
    args = build_parser().parse_args(["--mcp"])

    assert args.mcp
    assert args.url is None

    legacy_spelling = build_parser().parse_args(["--no_minify", "https://example.com/video"])
    assert legacy_spelling.no_minify
