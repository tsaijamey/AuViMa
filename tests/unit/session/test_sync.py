"""Tests for frago.session.sync module.

Tests pure functions that handle path encoding/decoding and session file identification.
"""
import pytest

from frago.session.sync import (
    encode_project_path,
    is_backed_up_session_file,
    is_main_session_file,
    is_subagent_session_file,
)


class TestEncodeProjectPath:
    """Test encode_project_path() function."""

    @pytest.mark.parametrize(
        "path,expected",
        [
            # Unix paths
            ("/home/alice/project", "-home-alice-project"),
            ("/home/alice/.frago", "-home-alice--frago"),
            ("/Users/alice/Documents", "-Users-alice-Documents"),
            ("/", "-"),
            # Windows paths
            ("C:/Users/alice", "C--Users-alice"),
            ("D:/Projects/myproject", "D--Projects-myproject"),
            ("C:/Users/alice/.frago", "C--Users-alice--frago"),
            # Windows paths with backslashes (should be normalized)
            ("C:\\Users\\alice", "C--Users-alice"),
            ("D:\\Projects\\myproject", "D--Projects-myproject"),
        ],
        ids=[
            "unix-home",
            "unix-hidden-dir",
            "unix-users",
            "unix-root",
            "win-c-drive",
            "win-d-drive",
            "win-hidden-dir",
            "win-backslash-c",
            "win-backslash-d",
        ],
    )
    def test_encode_various_paths(self, path: str, expected: str):
        """Test encoding of various path formats."""
        assert encode_project_path(path) == expected

    def test_encode_path_with_dots(self):
        """Test that dots in paths are also converted to hyphens."""
        # .frago becomes -frago (dot replaced with hyphen)
        assert encode_project_path("/home/user/.config") == "-home-user--config"

    def test_encode_empty_path(self):
        """Test encoding empty path."""
        assert encode_project_path("") == ""


class TestEncodingIsOneWay:
    """Folder names cannot be decoded back into a path.

    Claude Code encodes both "/" and "." as "-", so two different working
    directories can produce the same folder name. The working directory is read
    from the transcript records instead of being guessed from the folder.
    """

    def test_hyphenated_and_nested_paths_collide(self):
        assert encode_project_path("/repos/master-agent") == encode_project_path(
            "/repos/master/agent"
        )

    def test_dotted_directory_collides_too(self):
        assert encode_project_path("/home/user/.config") == encode_project_path(
            "/home/user//config"
        )


class TestIsMainSessionFile:
    """Test is_main_session_file() function."""

    def test_valid_uuid_jsonl(self):
        """Test that valid UUID.jsonl files are identified as main sessions."""
        assert is_main_session_file("550e8400-e29b-41d4-a716-446655440000.jsonl")
        assert is_main_session_file("a1b2c3d4-e5f6-7890-abcd-ef1234567890.jsonl")

    def test_sidechain_files_rejected(self):
        """Test that agent-*.jsonl sidechain files are rejected."""
        assert not is_main_session_file("agent-abc123.jsonl")
        assert not is_main_session_file("agent-xyz789.jsonl")

    def test_non_jsonl_files_rejected(self):
        """Test that non-.jsonl files are rejected."""
        assert not is_main_session_file("550e8400-e29b-41d4-a716-446655440000.json")
        assert not is_main_session_file("550e8400-e29b-41d4-a716-446655440000.txt")
        assert not is_main_session_file("session.log")

    def test_non_uuid_jsonl_rejected(self):
        """Test that .jsonl files without valid UUID names are rejected."""
        assert not is_main_session_file("random-name.jsonl")
        assert not is_main_session_file("not-a-uuid.jsonl")
        assert not is_main_session_file("12345.jsonl")

    def test_empty_filename(self):
        """Test that empty filename is rejected."""
        assert not is_main_session_file("")

    def test_just_extension(self):
        """Test that just extension is rejected."""
        assert not is_main_session_file(".jsonl")


class TestIsSubagentSessionFile:
    """Subagent transcripts are recognised by prefix alone, never by id shape."""

    @pytest.mark.parametrize(
        "filename",
        [
            # 17-character ids, the shape Claude Code writes today.
            "agent-aa0687c23caa71f2b.jsonl",
            "agent-a516520d772f61231.jsonl",
            # 7-character ids, still sitting in this machine's backup.
            "agent-a013ea8.jsonl",
            # Ids carrying a purpose in the name.
            "agent-acompact-20dfdaa9dfa2aa54.jsonl",
            "agent-aprompt_suggestion-ffbcba.jsonl",
        ],
        ids=["17-hex", "17-hex-2", "7-hex", "compact", "prompt-suggestion"],
    )
    def test_every_id_generation_is_accepted(self, filename: str):
        """Pinning one generation's id shape is what lets the next one go missing."""
        assert is_subagent_session_file(filename)

    def test_main_sessions_are_not_subagents(self):
        assert not is_subagent_session_file("550e8400-e29b-41d4-a716-446655440000.jsonl")

    def test_non_jsonl_rejected(self):
        assert not is_subagent_session_file("agent-aa0687c23caa71f2b.json")
        assert not is_subagent_session_file("agent-aa0687c23caa71f2b")

    def test_prefix_without_an_id_rejected(self):
        assert not is_subagent_session_file("agent-.jsonl")

    def test_unrelated_name_rejected(self):
        assert not is_subagent_session_file("agents.jsonl")
        assert not is_subagent_session_file("")


class TestIsBackedUpSessionFile:
    """The one predicate that decides whether a transcript gets copied."""

    def test_both_kinds_are_copied(self):
        assert is_backed_up_session_file("550e8400-e29b-41d4-a716-446655440000.jsonl")
        assert is_backed_up_session_file("agent-aa0687c23caa71f2b.jsonl")

    def test_everything_else_is_not(self):
        assert not is_backed_up_session_file("random-name.jsonl")
        assert not is_backed_up_session_file("session.json")
        assert not is_backed_up_session_file(".jsonl")
