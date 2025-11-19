# encoding: utf-8
"""PDS Reports."""
import importlib.resources

__version__ = VERSION = importlib.resources.files(__name__).joinpath("VERSION.txt").read_text().strip()
