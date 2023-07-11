"""Version grab tests."""
import os
import unittest

from lasso.reports.corral.cattle_head import CattleHead


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_GITHUB_TOKEN")


class MyTestCase(unittest.TestCase):
    """My test case."""

    # Test disabled because it relies on GITHUB_TOKEN
    # def test_get_changelog_signet(self):
    #     cattle_head = CattleHead(
    #         "validate", "https://github.com/nasa-pds/validate", "validate PDS formats", token=GITHUB_TOKEN
    #     )
    #     changelog_signet = cattle_head._get_changelog_signet()

    def test_nothing(self):
        """Nada."""
        pass


if __name__ == "__main__":
    unittest.main()
