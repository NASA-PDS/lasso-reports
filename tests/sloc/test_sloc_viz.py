import unittest
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pandas as pd
from lasso.reports.sloc.sloc import count_sloc
from lasso.reports.sloc.sloc import get_historical_sloc


class TestSLOCVisualizationTool(unittest.TestCase):
    @patch("subprocess.run")
    def test_get_historical_sloc(self, mock_subprocess):
        """Test historical SLOC counting functionality."""
        # Mock git commands
        mock_subprocess.side_effect = [
            # git clone
            MagicMock(returncode=0),
            # git rev-list --max-parents=0
            MagicMock(returncode=0, stdout="abc123\n"),
            # git show -s --format=%ai for first commit
            MagicMock(returncode=0, stdout="2020-01-01 00:00:00 +0000\n"),
            # git rev-list -1 --before
            MagicMock(returncode=0, stdout="def456\n"),
            # git show -s --format=%ai for target commit
            MagicMock(returncode=0, stdout="2023-12-31 00:00:00 +0000\n"),
            # git checkout
            MagicMock(returncode=0),
            # cloc command
            MagicMock(returncode=0, stdout='{"Python": {"code": 1000}, "Java": {"code": 2000}, "SUM": {"code": 3000}}'),
            # rm -rf
            MagicMock(returncode=0),
        ]

        total_sloc, language_sloc = get_historical_sloc(
            "https://github.com/NASA-PDS/validate", "validate", "2024-01-01"
        )

        self.assertEqual(total_sloc, 3000)
        self.assertEqual(language_sloc["Python"], 1000)
        self.assertEqual(language_sloc["Java"], 2000)

        # Verify git commands were called correctly
        calls = mock_subprocess.call_args_list
        self.assertEqual(calls[0][0][0], ["git", "clone", "https://github.com/NASA-PDS/validate", "./repos/validate"])
        self.assertEqual(calls[1][0][0], ["git", "-C", "./repos/validate", "rev-list", "--max-parents=0", "HEAD"])
        self.assertEqual(calls[2][0][0], ["git", "-C", "./repos/validate", "show", "-s", "--format=%ai", "abc123"])
        self.assertEqual(
            calls[3][0][0],
            ["git", "-C", "./repos/validate", "rev-list", "-1", "--before", "2024-01-01 23:59:59", "HEAD"],
        )
        self.assertEqual(calls[4][0][0], ["git", "-C", "./repos/validate", "show", "-s", "--format=%ai", "def456"])
        self.assertEqual(calls[5][0][0], ["git", "-C", "./repos/validate", "checkout", "def456"])
        self.assertEqual(calls[6][0][0], ["cloc", "./repos/validate", "--json"])
        self.assertEqual(calls[7][0][0], ["rm", "-rf", "./repos/validate"])
