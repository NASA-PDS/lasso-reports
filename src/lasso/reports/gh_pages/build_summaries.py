"""Summary building."""
import argparse
import logging
import os
import re
import sys
from functools import partial
from importlib.resources import files
from shutil import copy
from shutil import copytree
from shutil import rmtree

from lasso.reports.argparse import add_standard_arguments
from lasso.reports.branches.git_actions import loop_checkout_on_branch

from .root_index import update_index
from .summary import write_build_summary


_logger, _path = logging.getLogger(__name__), os.getcwd()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_GITHUB_TOKEN")


def get_current_release_from_conf(conf_path="docs/source/conf.py"):
    """Get the current release version from nasa-pds.github.io conf.py.

    Extracts the release version from lines like:
        release = 'B17'
        release = "B17.0"
        release = '17'

    :param conf_path: Path to conf.py file
    :return: Current release version string (e.g., "17" from "B17"), or None if not found
    """
    try:
        with open(conf_path, 'r') as f:
            content = f.read()
            # Look for: release = 'B17' or release = "B17.0" etc.
            # Capture everything after = until the closing quote
            match = re.search(r"release\s*=\s*['\"]([^'\"]+)['\"]", content)
            if match:
                release_string = match.group(1)
                _logger.info(f"Found release in conf.py: {release_string}")
                # Extract just the numeric version (e.g., "17" from "B17" or "B17.0")
                version_match = re.search(r'B?(\d+(?:\.\d+)*)', release_string)
                if version_match:
                    version = version_match.group(1).split('.')[0]  # Get base version
                    _logger.info(f"Parsed current release version: {version}")
                    return version
                else:
                    _logger.warning(f"Could not extract version number from: {release_string}")
                    return None
            else:
                _logger.warning(f"Could not find 'release' variable in {conf_path}")
                return None
    except FileNotFoundError:
        _logger.warning(f"conf.py not found at {conf_path}")
        return None
    except IOError as e:
        _logger.error(f"Error reading conf.py: {e}")
        return None


def copy_resources():
    """Copies static resources into the expected place."""
    _logger.info("write static resources (img, config)...")
    resources = files(__name__).joinpath("resources")
    for f in os.listdir(resources):
        i_p = os.path.join(resources, f)
        o_p = os.path.join(os.getcwd(), f)
        if os.path.isdir(i_p):
            if os.path.exists(o_p):
                rmtree(o_p, ignore_errors=True)
            copytree(i_p, o_p)
        else:
            if os.path.exists(o_p):
                os.remove(o_p)
            copy(i_p, os.getcwd())


def build_summaries(token, path=_path, format="md", version_pattern=None):
    """Build summaries."""
    copy_resources()

    herds = []

    # Get the current release version from conf.py
    # path is typically "./docs/source/releases/", so conf.py is one level up
    conf_path = os.path.join(os.path.dirname(path.rstrip('/')), "conf.py")
    current_release = get_current_release_from_conf(conf_path)
    if current_release:
        _logger.info(f"Current release from conf.py: Build {current_release}")
    else:
        _logger.warning(f"Could not determine current release from conf.py at {conf_path}")

    if not version_pattern:
        # dev release on main
        herd = next(
            loop_checkout_on_branch(
                "NASA-PDS/pdsen-corral",
                "main",
                partial(
                    write_build_summary,
                    root_dir=path,
                    gitmodules="/tmp/pdsen-corral/.gitmodules",
                    token=token,
                    dev=True,
                    format=format,
                    current_release=current_release,  # Pass current release for checking
                ),
                token=token,
                local_git_tmp_dir="/tmp",
            )
        )
        herds.append(herd)
        version_pattern = r"[0-9]+\.[0-9]+"

    # loop on selected version patterns
    for herd in loop_checkout_on_branch(
        "NASA-PDS/pdsen-corral",
        version_pattern,
        partial(
            write_build_summary,
            root_dir=path,
            gitmodules="/tmp/pdsen-corral/.gitmodules",
            token=token,
            dev=False,
            format=format,
            current_release=current_release,  # Pass current release for checking
        ),
        token=token,
        local_git_tmp_dir="/tmp",
    ):
        herds.append(herd)

    update_index(path, herds)


def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(description="Create new snapshot release")
    add_standard_arguments(parser)
    parser.add_argument("--token", dest="token", help="github personal access token")
    parser.add_argument("--path", dest="path", default="./output/", help="directory where the summary will be created")
    parser.add_argument(
        "--format", dest="format", default="rst", help="format of the summary, accepted formats are md and rst"
    )
    parser.add_argument(
        "--add-int-reports", dest="add_int_reports", action="store_true",
        help="Force add I&T reports in current build regardless of time window"
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format="%(levelname)s %(message)s")

    token = args.token or GITHUB_TOKEN
    if not token:
        _logger.error("Github token must be provided or set as environment variable (GITHUB_TOKEN).")
        sys.exit(1)

    # Set environment variable if flag is provided
    if args.add_int_reports:
        os.environ["ADD_INT_REPORTS"] = "true"
        _logger.info("ADD_INT_REPORTS flag enabled: I&T reports will be added to current build")

    build_summaries(token, args.path, args.format)


if __name__ == "__main__":
    main()
