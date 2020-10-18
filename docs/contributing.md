# Contributing

## Sharing feedback

If you want to contribute (thanks a lot ! :smiley:), you can open an [issue](https://github.com/art049/odmantic/issues/new){:target=blank_}.

You can create issues for questions, feature request, bug report, ...

Before creating a non obvious (typo, documentation fix) Pull Request, make sure to open
an issue.

## Developing locally

### Installing the tools

- [Git LFS](https://git-lfs.github.com/): used to store documentation assets in the repository
- [Docker](https://docs.docker.com/get-docker/): used to run a local MongoDB instance
- [Task](https://taskfile.dev){:target=blank_}: task manager

!!! tip "Installing python based development tools"
    In order to install the devtools written in python, it's recommended to use [pipx](https://pipxproject.github.io/pipx/){:target=blank_}.

    ```shell
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    ```

- [Poetry](https://python-poetry.org/){:target=blank_}: packaging system and dependency
  manager
  ```shell
  pipx install poetry
  ```

- [tox](https://tox.readthedocs.io/en/latest/){:target=blank_}: multi-environment test runner
  ```shell
  pipx install tox
  ```

- [pre-commit](https://pre-commit.com/){:target=blank_}: pre commit hook manager
  ```shell
  pipx install pre-commit
  ```

!!! tip "Python versions"
    If you want to test the project with multiple python versions, you'll need to
    install them manually.

    You can use [pyenv](https://github.com/pyenv/pyenv){:target=blank_} to
     install them easily.

    ```shell
    pyenv install "3.6.12"
    pyenv install "3.7.9"
    pyenv install "3.8.9"
    ```

### Configuring the local project
  ```shell
  task setup
  ```

### Developing

Available tasks for the project:

* `task setup`:                Configure the development environment.

* `task lint`:                 Run the linting checks.

* `task format`:               Format the code (and imports).

* `task mongodb-docker`:       Start the local MongoDB server.

* `task test`:                 Run the tests with the current version.

* `task full-test`:            Run the tests against all supported versions.

* `task coverage`:             Get the test coverage (xml and html) with the current version.

* `task docs`:                 Start the local documentation server.
