# PDS Lasso Reports

The PDS Lasso Reports package provides utilities to generates various kinds of reports. It provides four commands:

- `git-ping` which "pings" a branch by making an empty commit+push to it
- `summaries` which generates build summary tables in various formats
- `pds-plan` which creates planning board reports
- `pds-sloc` which analyzes and visualizes source lines of code (SLOC) across GitHub repositories

Please visit our website at: https://nasa-pds.github.io/lasso-reports

It may have useful information for developers and end-users.


## Prerequisites

Installing this software requires:
- `git` to be present on the target system
- `cloc` for SLOC analysis (install via your system's package manager)
- A GitHub personal access token (for accessing private repositories)


## User Quickstart

Install with:

    pip install lasso-reports


### PDS SLOC

To execute pds-sloc, run:

    # Basic usage - analyze NASA-PDS organization
    pds-sloc --update --visualize

    # Analyze a specific repository
    pds-sloc --update --visualize --repo validate

    # Initialize historical data from a specific date
    pds-sloc --init-history 2023-01-01

    # Generate visualizations from existing data
    pds-sloc --visualize

    # Use a specific GitHub token
    pds-sloc --update --token YOUR_GITHUB_TOKEN

    # Analyze a different organization
    pds-sloc --update --visualize --org OTHER-ORG

The tool will generate:
- A CSV report with SLOC counts by repository and language
- Visualizations showing:
  - Total SLOC by repository
  - Language distribution
  - Historical SLOC trends
  - Most active repositories

For more options, run:
    pds-sloc --help


## Code of Conduct

All users and developers of the NASA-PDS software are expected to abide by our [Code of Conduct](https://github.com/NASA-PDS/.github/blob/main/CODE_OF_CONDUCT.md). Please read this to ensure you understand the expectations of our community.


## Development

To develop this project, use your favorite text editor, or an integrated development environment with Python support, such as [PyCharm](https://www.jetbrains.com/pycharm/).


### Contributing

For information on how to contribute to NASA-PDS codebases please take a look at our [Contributing guidelines](https://github.com/NASA-PDS/.github/blob/main/CONTRIBUTING.md).


### Installation

Install in editable mode and with extra developer dependencies into your virtual environment of choice:

    pip install --editable '.[dev]'

Configure the `pre-commit` hooks:

    pre-commit install
    pre-commit install -t pre-push
    pre-commit install -t prepare-commit-msg
    pre-commit install -t commit-msg

These hooks check code formatting and also aborts commits that contain secrets such as passwords or API keys. However, a one time setup is required in your global Git configuration. See [the wiki entry on Git Secrets](https://github.com/NASA-PDS/nasa-pds.github.io/wiki/Git-and-Github-Guide#git-secrets) to learn how.


### Packaging

To isolate and be able to re-produce the environment for this package, you should use a [Python Virtual Environment](https://docs.python.org/3/tutorial/venv.html). To do so, run:

    python3 -m venv venv

Then exclusively use `venv/bin/python`, `venv/bin/pip`, etc. Or, "activate" the virtual environment by sourcing the appropriate script in the `venv/bin` directory.

If you have `tox` installed and would like it to create your environment and install dependencies for you run:

    tox --devenv <name you'd like for env> -e dev

Dependencies for development are specified as the `dev` `extras_require` in `setup.cfg`; they are installed into the virtual environment as follows:

    pip install --editable '.[dev]'

All the source code is in a sub-directory under `src`.


### Tooling

The `dev` `extras_require` included in the template repo installs `black`, `flake8` (plus some plugins), and `mypy` along with default configuration for all of them. You can run all of these (and more!) with:

    tox -e lint
