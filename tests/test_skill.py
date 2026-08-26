import importlib.metadata
import tomllib
from pathlib import Path

import pytest

from deep_transcribe.skill_support import (
    AGENTS_BEGIN_PREFIX,
    AGENTS_END_MARKER,
    DISCOVERY_VERSION,
    SKILL_FORMAT,
    SURFACE_AGENTS_MD,
    SURFACE_PORTABLE,
    YTDLP_DISCOVERY_CUTOFF,
    agents_md_block,
    compose_skill,
    deep_transcribe_version,
    discovery_skill_bundle,
    get_docs_content,
    get_openai_metadata,
    get_skill_template,
    install_skill,
    is_pypi_release,
    render_skill_bundle,
    update_agents_md,
)


def test_built_in_docs_cover_iterative_reruns_and_skill_installation() -> None:
    docs = get_docs_content()

    assert docs.startswith("# Deep Transcribe Guide\n")
    assert "## Iterate Without Repeating Speech-to-Text" in docs
    assert "normal cache-aware rerun" in docs
    assert "--rerun-processing" in docs
    assert "--rerun" in docs
    assert "Deepgram request count" in docs
    assert "## Install the Agent Skill" in docs
    assert "deep-transcribe --install-skill" in docs
    assert "MCP" not in docs


def test_skill_template_is_concise_and_routes_to_built_in_docs() -> None:
    template = get_skill_template()

    assert template.startswith("---\nname: deep-transcribe\n")
    assert "__DEEP_TRANSCRIBE_VERSION__" in template
    assert "__YTDLP_CUTOFF__" in template
    assert "deep-transcribe --docs" in template
    assert "deep-transcribe --install-skill" in template
    assert "MCP" not in template


def test_skill_runner_selection_handles_source_checkouts_and_stale_path_commands() -> None:
    template = get_skill_template()

    assert "uv run deep-transcribe --docs" in template
    assert "A command merely existing on `PATH` is not sufficient" in template
    assert "missing or rejects `--docs`" in template


def test_compose_skill_substitutes_an_exact_release_pin() -> None:
    rendered = compose_skill("1.2.3")

    assert "deep-transcribe==1.2.3" in rendered
    assert "__DEEP_TRANSCRIBE_VERSION__" not in rendered
    assert "__YTDLP_CUTOFF__" not in rendered
    assert f"--exclude-newer-package yt-dlp={YTDLP_DISCOVERY_CUTOFF}" in rendered
    assert rendered == compose_skill("1.2.3")


def test_runner_cutoff_matches_the_reviewed_project_policy() -> None:
    pyproject = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())

    assert pyproject["tool"]["uv"]["exclude-newer-package"]["yt-dlp"] == (YTDLP_DISCOVERY_CUTOFF)


@pytest.mark.parametrize("version_string", ["0.1.10", "1.2.3", "1.2.3.post1"])
def test_pypi_release_versions_are_accepted(version_string: str) -> None:
    assert is_pypi_release(version_string)


@pytest.mark.parametrize(
    "version_string",
    ["", "latest", "0.1.11.dev2+abc", "1.0.0a1", "1.0.0b1", "1.0.0rc1", "1.0+local"],
)
def test_non_release_versions_are_rejected(version_string: str) -> None:
    assert not is_pypi_release(version_string)


def test_development_install_uses_the_reviewed_discovery_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def development_version(_name: str) -> str:
        return "0.1.11.dev2+abc"

    monkeypatch.setattr(importlib.metadata, "version", development_version)

    assert deep_transcribe_version() == DISCOVERY_VERSION
    assert f"deep-transcribe=={DISCOVERY_VERSION}" in compose_skill()


def test_release_install_uses_its_own_version(monkeypatch: pytest.MonkeyPatch) -> None:
    def release_version(_name: str) -> str:
        return "2.3.4"

    monkeypatch.setattr(importlib.metadata, "version", release_version)

    assert deep_transcribe_version() == "2.3.4"
    assert "deep-transcribe==2.3.4" in compose_skill()


def test_rendered_bundle_is_complete_and_stamped() -> None:
    bundle = render_skill_bundle("1.2.3")

    assert set(bundle) == {Path("SKILL.md"), Path("agents/openai.yaml")}
    assert bundle[Path("SKILL.md")].startswith("---\nname: deep-transcribe\n")
    assert f"format={SKILL_FORMAT} surface=skill-md" in bundle[Path("SKILL.md")]
    assert "deep-transcribe==1.2.3" in bundle[Path("SKILL.md")]
    assert f"format={SKILL_FORMAT} surface=openai-yaml" in bundle[Path("agents/openai.yaml")]
    assert "display_name" in get_openai_metadata()


def test_default_install_writes_all_project_local_surfaces(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    results = install_skill(project_root=tmp_path)

    assert {result.action for result in results} == {"installed"}
    for parent in (tmp_path / ".agents/skills", tmp_path / ".claude/skills"):
        skill_dir = parent / "deep-transcribe"
        assert (skill_dir / "SKILL.md").is_file()
        assert (skill_dir / "agents/openai.yaml").is_file()
    assert AGENTS_BEGIN_PREFIX in (tmp_path / "AGENTS.md").read_text()


def test_install_is_idempotent(tmp_path: Path) -> None:
    first = install_skill(project_root=tmp_path)
    second = install_skill(project_root=tmp_path)

    assert {result.action for result in first} == {"installed"}
    assert {result.action for result in second} == {"unchanged"}


def test_install_selects_only_requested_surfaces(tmp_path: Path) -> None:
    results = install_skill(
        project_root=tmp_path,
        surfaces=frozenset({SURFACE_PORTABLE, SURFACE_AGENTS_MD}),
    )

    assert {result.surface for result in results} == {SURFACE_PORTABLE, SURFACE_AGENTS_MD}
    assert (tmp_path / ".agents/skills/deep-transcribe/SKILL.md").is_file()
    assert not (tmp_path / ".claude").exists()
    assert (tmp_path / "AGENTS.md").is_file()


def test_explicit_agent_base_installs_one_complete_bundle(tmp_path: Path) -> None:
    agent_base = tmp_path / "agent-home"
    results = install_skill(agent_base=agent_base)

    assert len(results) == 1
    assert results[0].action == "installed"
    skill_dir = agent_base / "skills/deep-transcribe"
    assert (skill_dir / "SKILL.md").is_file()
    assert (skill_dir / "agents/openai.yaml").is_file()
    assert not (tmp_path / "AGENTS.md").exists()


def test_forward_guard_refuses_a_newer_bundle_format(tmp_path: Path) -> None:
    skill_path = tmp_path / ".agents/skills/deep-transcribe/SKILL.md"
    skill_path.parent.mkdir(parents=True)
    newer = "---\nname: deep-transcribe\n---\n<!-- format=f99 surface=skill-md -->\n"
    skill_path.write_text(newer, encoding="utf-8")

    results = install_skill(
        project_root=tmp_path,
        surfaces=frozenset({SURFACE_PORTABLE}),
    )

    assert results[0].action == "blocked-newer"
    assert skill_path.read_text() == newer
    assert not (skill_path.parent / "agents/openai.yaml").exists()


def test_install_does_not_publish_skill_before_complete_bundle(tmp_path: Path) -> None:
    skill_dir = tmp_path / ".agents/skills/deep-transcribe"
    skill_dir.mkdir(parents=True)
    (skill_dir / "agents").write_text("not a directory", encoding="utf-8")

    with pytest.raises(FileExistsError):
        install_skill(
            project_root=tmp_path,
            surfaces=frozenset({SURFACE_PORTABLE}),
        )

    assert not (skill_dir / "SKILL.md").exists()


def test_agents_md_update_preserves_unmarked_content_and_is_idempotent(tmp_path: Path) -> None:
    agents_path = tmp_path / "AGENTS.md"
    agents_path.write_text("# Project\n\nKeep this guidance.\n", encoding="utf-8")

    first = update_agents_md(agents_path, version="1.2.3")
    second = update_agents_md(agents_path, version="1.2.3")
    content = agents_path.read_text()

    assert first.action == "updated"
    assert second.action == "unchanged"
    assert "Keep this guidance." in content
    assert content.count(AGENTS_BEGIN_PREFIX) == 1
    assert content.count(AGENTS_END_MARKER) == 1
    assert "deep-transcribe==1.2.3" in content


def test_agents_md_forward_guard_preserves_a_newer_block(tmp_path: Path) -> None:
    agents_path = tmp_path / "AGENTS.md"
    newer = (
        f"{AGENTS_BEGIN_PREFIX} format=f99 surface=agents-md -->\n"
        "Future instructions.\n"
        f"{AGENTS_END_MARKER}\n"
    )
    agents_path.write_text(newer, encoding="utf-8")

    result = update_agents_md(agents_path, version="1.2.3")

    assert result.action == "blocked-newer"
    assert agents_path.read_text() == newer


def test_agents_md_block_routes_agents_to_executable_documentation() -> None:
    block = agents_md_block("1.2.3")

    assert block.startswith(AGENTS_BEGIN_PREFIX)
    assert block.rstrip().endswith(AGENTS_END_MARKER)
    assert "deep-transcribe --docs" in block
    assert "same verified runner with `--skill`" in block
    assert "- Run `deep-transcribe --skill`" not in block
    assert "uv run deep-transcribe --docs" in block
    assert "only if `deep-transcribe --docs` succeeds" in block
    assert "deep-transcribe==1.2.3" in block
    assert f"--exclude-newer-package yt-dlp={YTDLP_DISCOVERY_CUTOFF}" in block


def test_checked_in_skill_copies_match_the_canonical_package_source() -> None:
    repo_root = Path(__file__).parents[1]
    expected = discovery_skill_bundle()

    for base in (
        repo_root / "skills/deep-transcribe",
        repo_root / ".agents/skills/deep-transcribe",
        repo_root / ".claude/skills/deep-transcribe",
    ):
        for relative_path, expected_content in expected.items():
            assert (base / relative_path).read_text() == expected_content
