# Installation Guide

## Requirements

Before you begin, ensure you have the following installed:

* Python 3.11 or newer
   * Download from [Python's official website](https://www.python.org/downloads/)
   * For Windows users, refer to [Using Python on Windows](https://docs.python.org/3/using/windows.html)

* uv
    * Install from [uv's GitHub repository](https://github.com/astral-sh/uv)
    * Check the [documentation](https://docs.astral.sh/uv/) for more details

* qpdf
    * Download binaries from [qpdf's GitHub releases](https://github.com/qpdf/qpdf/releases)
   * Refer to the [documentation](https://qpdf.readthedocs.io/en/stable/) for setup instructions
* git
    * Install from [git-scm.com](https://git-scm.com/)
    * Windows users: [Installation guide](https://git-scm.com/install/windows)
    * macOS users: [Installation guide](https://git-scm.com/install/mac)
* jq (optional, but highly recommended)
    * Install from [Download jq](https://jqlang.org/download/) page

## Verifying Installation

After installing all the requirements, verify the installations by running the following commands:

```console
python --version
uv --version
qpdf --version
git --version
```

Each command should display the version number.

## Installing rokujo-collector-scrapy-generic

Clone the repository:

```console
git clone https://github.com/trombik/rokujo-collector-scrapy-generic.git
```

Navigate to the project directory:

```console
cd rokujo-collector-scrapy-generic
```

Install the dependencies:

```console
uv sync
```

Verify Scrapy installation:

```console
uv run scrapy --version
```

```{note}
If you encounter any issues during installation, please refer to the respective documentation links provided above.

For any further assistance, feel free to open an issue on the [GitHub repository Issues](https://github.com/trombik/rokujo-collector-scrapy-generic/issues).
```
