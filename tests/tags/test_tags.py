"""Tags tests."""
import os
import unittest
from datetime import datetime

from lasso.reports.tags.tags import Tags

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_GITHUB_TOKEN")


class MyTestCase(unittest.TestCase):
    """My test case."""

    # Disabled test because it expects GITHUB_TOKEN to be set
    # def test_get_earliest_tag_after(self):
    #     """Test getting the earliest tag after something."""
    #     tags = Tags('NASA-PDS', 'validate', token=GITHUB_TOKEN)
    #     tags.get_earliest_tag_after(datetime(2020, 1, 1).isoformat().replace('+00:00', 'Z'))
    def test_nothing(self):
        """I got nothin', pal."""
        pass


if __name__ == "__main__":
    unittest.main()
