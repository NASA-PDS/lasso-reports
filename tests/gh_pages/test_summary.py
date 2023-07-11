import os
import unittest

from lasso.reports.gh_pages.summary import write_build_summary

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_GITHUB_TOKEN")


class MyTestCase(unittest.TestCase):
    """My test case."""

    # Disabled because it relies on GITHUB_TOKEN in the environment
    # def test_simple_rst(self):
    #     """Test simple reStructuredText."""
    #     current_dir = os.path.dirname(__file__)
    #     gitmodules = os.path.join(current_dir, '.gitmodules')
    #     write_build_summary(gitmodules=gitmodules, root_dir='./tmp',
    #                         token=GITHUB_TOKEN, dev=False, version='11.0', format='rst')

    def test_nothing(self):
        """Nil."""
        pass


if __name__ == "__main__":
    unittest.main()
