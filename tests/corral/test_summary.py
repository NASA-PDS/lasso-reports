"""Summary tests."""
import logging
import os
import unittest

from lasso.reports.corral.herd import Herd
from lasso.reports.gh_pages.summary import write_build_summary

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_GITHUB_TOKEN")


logger = logging.getLogger(__name__)


class MyTestCase(unittest.TestCase):
    """My test case."""

    gitmodules = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gitmodules")

    # All tests disabled because they rely on GITHUB_TOKEN in the environment

    # def test_gather_the_herd(self):
    #     herd = Herd(gitmodules=self.gitmodules,
    #                 token=GITHUB_TOKEN)
    #     cattle_heads = herd.get_cattle_heads()
    #     version = herd.get_shepard_version()

    # def test_summary_dev(self):
    #     write_build_summary(gitmodules=self.gitmodules,
    #                         output_file_name='output/dev_summary.md',
    #                         token=GITHUB_TOKEN, dev=True,
    #                         version='10.0-SNAPSHOT')

    # def test_summary_release(self):
    #     write_build_summary(gitmodules=self.gitmodules,
    #                         output_file_name='output/rel_summary.md',
    #                         token=GITHUB_TOKEN, dev=False,
    #                         version='10.0')

    def test_nothing(self):
        """Nope."""
        pass


if __name__ == "__main__":
    unittest.main()
