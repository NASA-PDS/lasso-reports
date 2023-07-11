"""herds of stuff."""
import logging
import os
import re
from configparser import ConfigParser
from datetime import datetime

from lasso.reports.corral import CattleHead

logger = logging.getLogger(__name__)


class Herd:
    """A herd."""

    def __init__(self, gitmodules=None, dev=False, token=False):
        """Initializer."""
        self._dev = dev
        self._token = token
        self._config = ConfigParser()
        if gitmodules:
            self._config.read(gitmodules)
        else:
            self._config.read(os.path.join(os.getcwd(), ".gitmodules"))

        self._gather_the_herd()

    def number_of_heads(self):
        """Get the number of heads in the herd."""
        return len(self._herd)

    def get_cattle_heads(self):
        """Get the heads o'cattle."""
        return self._herd

    def _gather_the_herd(self):
        """Gather the herd."""
        logger.info("gather the herd of submodules listed in .gitmodules")

        self._herd = {}
        self._shepard_version = None
        self._update_date = None
        for section in self._config.sections():
            if 'submodule "."' not in section:
                module_name_search = re.search('submodule "(.*)"', section, re.IGNORECASE)
                if module_name_search:
                    module_name = module_name_search.group(1)

                # Please do not comment-out code without providing an explanation as to why:
                # module_array = section.split(" ")
                # if len(module_array) >= 2:
                #     module_name = module_array[1].strip('"')
                else:
                    logger.error(f'section {section} is malformed, expected format is: [submodule "<module name>"]')

                optional_module_options = {
                    k: self._config.get(section, k).strip("/")
                    for k in ["version", "type"]
                    if self._config.has_option(section, k)
                }
                cattle_head = CattleHead(
                    module_name,
                    self._config.get(section, "url").strip("/"),
                    dev=self._dev,
                    token=self._token,
                    **optional_module_options,
                )

                pub_date = cattle_head.get_published_date()
                if pub_date:
                    self._update_date = max(self._update_date, pub_date) if self._update_date else pub_date
                self._herd[module_name] = cattle_head
            else:
                self._shepard_version = self._config.get(section, "version")
                self._release_date = datetime.fromisoformat(self._config.get(section, "release"))

        return 0

    def set_shepard_version(self, version):
        """Set the shephard version to ``version``.

        For unit test purpose
        :param version:
        :return:
        """
        self._config['submodule "."']["version"] = version

    def get_shepard_version(self):
        """Get the shepard version as a str."""
        return self._config.get('submodule "."', "version").strip(" ")

    def get_release_datetime(self):
        """Get the date and time of the release."""
        return self._release_date

    def get_update_datetime(self):
        """Get the date and time of the update."""
        return self._update_date
