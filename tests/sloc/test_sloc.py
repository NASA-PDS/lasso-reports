import os
import subprocess
import unittest
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

from lasso.reports.sloc.sloc import clone_repo
from lasso.reports.sloc.sloc import count_sloc
from lasso.reports.sloc.sloc import get_org_repos
from lasso.reports.sloc.sloc import HEADERS
from lasso.reports.sloc.sloc import HISTORICAL_LOG_FILE
from lasso.reports.sloc.sloc import write_historical_log


class TestSLOCReportTool(unittest.TestCase):
    @patch("lasso.reports.sloc.sloc.requests.get")
    def test_get_org_repos(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"name": "test-repo", "clone_url": "https://github.com/NASA-PDS/test-repo.git"}
        ]
        mock_response.links = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        HEADERS["Authorization"] = "token fake-token"
        repos = get_org_repos("NASA-PDS")
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["name"], "test-repo")

    @patch("lasso.reports.sloc.sloc.subprocess.run")
    def test_clone_repo(self, mock_run):
        mock_run.return_value = None
        result = clone_repo("https://github.com/NASA-PDS/test-repo.git", "test-repo")
        self.assertEqual(result, "./repos/test-repo")
        mock_run.assert_called_with(
            ["git", "clone", "--depth", "1", "https://github.com/NASA-PDS/test-repo.git", "./repos/test-repo"],
            check=True,
        )

    @patch("lasso.reports.sloc.sloc.subprocess.run")
    def test_count_sloc_success(self, mock_run):
        cloc_output = '{"SUM": {"code": 123}, "Python": {"code": 100}}'
        mock_run.return_value = MagicMock(stdout=cloc_output)
        total, languages = count_sloc("./repos/test-repo")
        self.assertEqual(total, 123)
        self.assertEqual(languages, {"Python": 100})

    @patch(
        "lasso.reports.sloc.sloc.subprocess.run", side_effect=subprocess.CalledProcessError(1, "cloc", stderr="error")
    )
    def test_count_sloc_failure(self, mock_run):
        total, languages = count_sloc("./repos/test-repo")
        self.assertIsNone(total)
        self.assertEqual(languages, {})

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.isfile", return_value=False)
    @patch("os.path.join", return_value="data/history/sloc_history.csv")
    def test_write_historical_log(self, mock_join, mock_isfile, mock_file):
        write_historical_log("2025-04-25 10:00:00", "test-repo", 100, {"Python": 100})
        mock_file.assert_called_once_with("data/history/sloc_history.csv", mode="a", newline="")


if __name__ == "__main__":
    unittest.main()
