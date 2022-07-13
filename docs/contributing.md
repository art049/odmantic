# Contributing

## Sharing feedback

This project is still quite new and therefore having your feedback will really help to
prioritize relevant feature developments :rocket:.

The easiest way to share feedback and discuss about the project is to join the [Gitter
chatroom](https://gitter.im/odmantic/community?utm_source=share-link&utm_medium=link&utm_campaign=share-link){:target=blank_}.

If you want to contribute (thanks a lot ! :smiley:), you can open an
[issue](https://github.com/art049/odmantic/issues/new){:target=blank_} on Github.

Before creating a non obvious (typo, documentation fix) Pull Request, please make sure
to open an issue.

## Developing locally

<div align="center">
  <a href="https://codecov.io/gh/art049/odmantic" target="_blank">
      <img src="https://codecov.io/gh/art049/odmantic/branch/master/graph/badge.svg?token=3NYZK14STZ"    alt="coverage">
  </a>
  <a href="https://github.com/pre-commit/pre-commit" target="_blank">
      <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white"
      alt="pre-commit">
  </a>
  <a href="http://mypy-lang.org/" target="_blank">
      <img src="https://img.shields.io/badge/mypy-checked-informational.svg" alt="mypy: checked">
  </a>
  <a href="https://github.com/python/black" target="_blank">
      <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
  </a>
  <a href="https://gitter.im/odmantic/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge"    target="_blank">
      <img src="https://badges.gitter.im/odmantic/community.svg" alt="Gitter">
  </a>
</div>

### With the VSCode's [devcontainer](https://code.visualstudio.com/docs/remote/containers){:target=blank_} feature

This feature will make the tools/environment installation very simple as you will develop
in a container that has already been configured to run this project.

Here are the steps:

1. Clone the repository and open it with [Visual Studio
   Code](https://code.visualstudio.com/){:target=blank_}.
2. Make sure that the [Remote -
    Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers){:target=blank_}
    (`ms-vscode-remote.remote-containers`) extension is installed.
3. Run the `Remote-Container: Reopen in Container` command (press `Ctrl`+`Shift`+`P` and
   then type the command).
4. After the setup script completes, the environment is ready. You can start the local
   development :fire:.

   You can go to the [development tasks](#running-development-tasks) section to see the
   available `task` commands.

!!! note "MongoDB container"
    In this containerized development environment, a MongoDB instance should already be
    running as a part of the development `docker-compose.yml` file internally used by
    VSCode.

### Regular environment setup

#### Installing the tools

- [Git LFS](https://git-lfs.github.com/){:target=blank_}: used to store documentation assets in the repository
- [Docker](https://docs.docker.com/get-docker/){:target=blank_}: used to run a local MongoDB instance
- [Docker Compose](https://docs.docker.com/compose/install/){:target=blank_} (Optional): used to run a local MongoDB cluster (replica set or shards)
- [Task](https://taskfile.dev){:target=blank_}: task manager

!!! tip "Installing python based development tools"
    In order to install the devtools written in python, it's recommended to use [pipx](https://pipxproject.github.io/pipx/){:target=blank_}.

    ```shell
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    ```

- [flit](https://flit.pypa.io/en/latest/){:target=blank_}: packaging system and dependency
  manager
  ```shell
  pipx install flit
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
    # Install the versions
    pyenv install "3.7.9"
    pyenv install "3.8.9"
    pyenv install "3.9.0"
    # Make the versions available locally in the project
    pyenv local 3.8.6 3.7.9 3.9.0
    ```

#### Configuring the local environment
  ```shell
  task setup
  ```

### Running development tasks

The following tasks are available for the project:

* `task setup`: Configure the development environment.

* `task lint`: Run the linting checks.

* `task format`: Format the code (and imports).

* `mongodb:standalone-docker`: Start a standalone MongoDB instance using a docker container

* `mongodb:standalone-docker:down`: Stop the standalone instance

* `mongodb:replica-compose`: Start a replica set MongoDB cluster using docker-compose

* `mongodb:replica-compose:down`: Stop the replica set cluster

* `mongodb:sharded-compose`: Start a sharded MongoDB cluster using docker-compose

* `mongodb:sharded-compose:down`: Stop the sharded MongoDB cluster

* `task test`: Run the tests with the current version.

* `task full-test`: Run the tests against all supported versions.

* `task coverage`: Get the test coverage (xml and html) with the current version.

* `task docs`: Start the local documentation server.
