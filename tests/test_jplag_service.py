"""Tests for JPlag service."""

import os
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.jplag_models import PlagiarismAnalysisRequest, ProgrammingLanguage
from src.services.jplag_service import JPlagService


class TestJPlagService:
    """Test cases for JPlag service."""

    def test_init_with_valid_jar_path(self, tmp_path):
        """Test service initialization with valid JAR path."""
        jar_path = tmp_path / "jplag.jar"
        jar_path.touch()

        service = JPlagService(str(jar_path))
        assert service.jplag_jar_path == str(jar_path)

    def test_init_with_invalid_jar_path(self):
        """Test service initialization with invalid JAR path."""
        with pytest.raises(FileNotFoundError):
            JPlagService("/invalid/path/jplag.jar")

    @pytest.mark.asyncio
    async def test_save_uploads(self, tmp_path):
        """Test saving uploaded files."""
        jar_path = tmp_path / "jplag.jar"
        jar_path.touch()
        service = JPlagService(str(jar_path))

        # Mock upload files
        mock_files = [
            MagicMock(filename="test1.java"),
            MagicMock(filename="test2.java"),
        ]

        # Mock file content
        mock_files[0].read = AsyncMock(return_value=b"public class Test1 {}")
        mock_files[1].read = AsyncMock(return_value=b"public class Test2 {}")

        base_dir = str(tmp_path / "test_base")
        submission_dir = await service._save_uploads(mock_files, base_dir)

        # Verify directory structure
        assert os.path.exists(submission_dir)
        assert os.path.exists(
            os.path.join(submission_dir, "submission_1", "test1.java")
        )
        assert os.path.exists(
            os.path.join(submission_dir, "submission_2", "test2.java")
        )

    @pytest.mark.asyncio
    async def test_run_jplag_success(self, tmp_path):
        """Test successful JPlag execution."""
        jar_path = tmp_path / "jplag.jar"
        jar_path.touch()
        service = JPlagService(str(jar_path))

        # Create mock submission directory
        submission_dir = tmp_path / "submissions"
        submission_dir.mkdir()

        # Create mock result file
        result_file = tmp_path / "result_test.jplag"
        result_file.touch()

        request = PlagiarismAnalysisRequest(
            language=ProgrammingLanguage.JAVA,
            min_tokens=9,
        )

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock successful process
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            # Mock os.path.exists to return True for result file
            with patch("os.path.exists", return_value=True):
                result_path = await service._run_jplag(
                    str(submission_dir), request, str(tmp_path), "test"
                )

            assert result_path.endswith("result_test.jplag")

    @pytest.mark.asyncio
    async def test_run_jplag_failure(self, tmp_path):
        """Test JPlag execution failure."""
        jar_path = tmp_path / "jplag.jar"
        jar_path.touch()
        service = JPlagService(str(jar_path))

        submission_dir = tmp_path / "submissions"
        submission_dir.mkdir()

        request = PlagiarismAnalysisRequest(language=ProgrammingLanguage.JAVA)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock failed process
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"Error occurred"))
            mock_subprocess.return_value = mock_process

            with pytest.raises(RuntimeError, match="JPlag execution failed"):
                await service._run_jplag(
                    str(submission_dir), request, str(tmp_path), "test"
                )

    @pytest.mark.asyncio
    async def test_parse_zip_contents(self, tmp_path):
        """Test parsing ZIP contents."""
        jar_path = tmp_path / "jplag.jar"
        jar_path.touch()
        service = JPlagService(str(jar_path))

        # Create mock ZIP file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            # Add mock JSON files
            zf.writestr("topComparisons.json", "[]")
            zf.writestr("runInformation.json", '{"duration": 1000}')
            zf.writestr("comparisons/test1-test2.json", '{"similarities": {}}')

        with zipfile.ZipFile(zip_path, "r") as zf:
            data = await service._parse_zip_contents(zf)

        assert "topComparisons" in data
        assert "runInformation" in data
        assert "detailed_comparisons" in data
        assert data["runInformation"]["duration"] == 1000

    def test_parse_code_position(self, tmp_path):
        """Test parsing code position."""
        jar_path = tmp_path / "jplag.jar"
        jar_path.touch()
        service = JPlagService(str(jar_path))

        pos_data = {"line": 10, "column": 5, "tokenListIndex": 25}

        position = service._parse_code_position(pos_data)
        assert position.line == 10
        assert position.column == 5
        assert position.token_index == 25

    def test_parse_match(self, tmp_path):
        """Test parsing match data."""
        jar_path = tmp_path / "jplag.jar"
        jar_path.touch()
        service = JPlagService(str(jar_path))

        match_data = {
            "firstFileName": "Test1.java",
            "secondFileName": "Test2.java",
            "startInFirst": {"line": 1, "column": 0, "tokenListIndex": 0},
            "endInFirst": {"line": 5, "column": 1, "tokenListIndex": 10},
            "startInSecond": {"line": 2, "column": 0, "tokenListIndex": 5},
            "endInSecond": {"line": 6, "column": 1, "tokenListIndex": 15},
            "lengthOfFirst": 10,
            "lengthOfSecond": 10,
        }

        match = service._parse_match(match_data)
        assert match.first_file_name == "Test1.java"
        assert match.second_file_name == "Test2.java"
        assert match.start_in_first.line == 1
        assert match.end_in_first.line == 5
        assert match.length_of_first == 10

    @pytest.mark.asyncio
    async def test_get_detailed_comparison_not_implemented(self, tmp_path):
        """Test getting detailed comparison (not implemented)."""
        jar_path = tmp_path / "jplag.jar"
        jar_path.touch()
        service = JPlagService(str(jar_path))

        result = await service.get_detailed_comparison("test", "sub1", "sub2")
        assert result is None
