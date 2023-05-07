# Contributing

Thank you for wanting to contribute to and improve this project!


## Contents

* [Getting Started](#getting-started)
  * [Issues](#issues)
  * [Pull Requests](#pull-requests)
* [Running Tests](#running-tests)
* [Linting and Formatting](#linting-and-formatting)
* [Attribution](#attribution)


## Getting Started

Contributions are made via Issues and Pull Request (PRs).

Before creating Issues or Pull Requests, it is useful to do a quick search to ensure others are not facing the same
issues or doing the same work as you.


### Issues

Issues can be used to report problems, bugs, request features and discuss potential changes and improvements.

When reporting issues and bugs please try include the following:

* Describe the steps you took.
* Describe what actually happened. Include a traceback if there was an exception.
* Describe what you expected to happen.
* List your version. If possible, check if the issue is already fixed in any of the later releases or in the latest
  snapshot.


### Pull Requests

Pull request (PRs) are always welcome and are the fastest way to get any issue fix, improvement or
feature added to a release. In general, PRs should:

* Address a single concern/feature rather than a number of features/bugs.
* Clearly indicate any known breaking changes.
* For new features, always include documentation.
* Write unit tests.
* Add changelog entries, see ``CHANGELOG.md`` for instructions.


In general, PRs should **not**:

* Address white-space/style issues.
* Refactor code that is working or does not need to be refactored in order to apply a fix.
* Introduce comments to unrelated code.


For changes that may violate the above, or introduce breaking changes, it's best to open an Issue
to discuss your proposal first, while not required, it can save time creating and reviewing changes.

In general, we follow the ["fork-and-pull" Git workflow](https://github.com/susam/gitpr):

1. Fork the repository to your own GitHub account or organisation
2. Clone the project to your local machine
3. Create a branch locally with a succinct but descriptive name
4. Commit changes to the branch
5. Follow any formatting and testing guidelines specified
6. Push changes to your fork
7. Open a PR in our repository and follow the PR template so we can efficiently review and merge
   changes.


Before opening your PR, you should:

* Lint and format your code according to the project standard, see [Linting and formatting](#linting-and-formatting).
* You should run all tests and ensure they pass, see [Running Tests](#running-tests). You should also try ensure that
  coverage remains roughly the same.


## Running Tests

* Tests are run with [tox](https://tox.wiki/en/latest/), you can simply run ``tox`` to run all the tests.
  - To run only unit tests, run ``tox -e <your python version>``, see ``tox.ini`` for all supported versions.
  - To run documentation tests, run ``tox -e docs``
  - To run spelling checks on the documentation, run ``tox -e spelling``
  - To run linting and formatting checks, run ``tox -e lint``
  - To run typing checks, run ``tox -e typing``
* Only Python versions 3.8 and newer are supported. Tests should not target earlier versions.


## Linting and Formatting

* The easiest way to lint and format the code is with [pre-commit](https://pre-commit.com/). Simply install, and run
  ``pre-commit run --all-files`` to automatically lint and format your code. Run ``pre-commit install`` to automatically
  run checks and formatting when you commit your code.
* For Visual Studio Code, a ``.vscode/settings.json`` configuration is included for formatting.
* Alternatively, you ensure the following linting and formatting plugins are installed in your IDE/environment and you
  follow the rules within:
  - [black](https://black.readthedocs.io/)
  - [flake8](https://flake8.pycqa.org/)
  - [isort](https://pycqa.github.io/isort/)
* Some linting and formatting rules are excluded, as well as some files being ignored, please check ``pyproject.toml``.
* pre-commit also applies a number of quality-of-life checks, see ``.pre-commit-config.yaml``.


## Attribution

Parts of the contributing guidelines have been adapted from and inspired by:

* [Auth0: Contributing to Auth0 projects](https://github.com/auth0/open-source-template/blob/master/GENERAL-CONTRIBUTING.md)
* [Contributing to Open Source Projects](https://www.contribution-guide.org/)
* [opensource.com: A template for creating open source contributor guidelines](https://opensource.com/life/16/3/contributor-guidelines-template-and-tips)
* [Mozilla: Wrangling Web Contributions: How to Build a CONTRIBUTING.md](https://mozillascience.github.io/working-open-workshop/contributing/)
