"""Build summaries tests."""
import os
import unittest

from lasso.reports.gh_pages.build_summaries import build_summaries

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_GITHUB_TOKEN")


class MyTestCase(unittest.TestCase):
    """My test case."""

    # All tests disabled because they rely on GITHUB_TOKEN in the environment

    # def test_default_summaries(self):
    #     """Test build summaries."""
    #     build_summaries(GITHUB_TOKEN, path='tmp', format='md')

    # def test_rst_summaries(self):
    #     build_summaries(GITHUB_TOKEN, path='tmp', format='rst')

    # def test_rst_summaries_one_version(self):
    #     build_summaries(GITHUB_TOKEN, path='tmp', format='rst', version_pattern="11.1")

    def test_nothing(self):
        """Nihil."""
        pass


if __name__ == "__main__":
    unittest.main()
