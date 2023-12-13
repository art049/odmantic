import datetime
import importlib.metadata
import os
from enum import Enum

import typer
from click.types import Choice
from semver import VersionInfo


class BumpType(str, Enum):
    major = "major"
    minor = "minor"
    patch = "patch"


def get_current_version() -> VersionInfo:
    version = importlib.metadata.version("odmantic")
    return VersionInfo.parse(version)


def get_new_version(current_version: VersionInfo, bump_type: BumpType) -> VersionInfo:
    if bump_type == BumpType.major:
        return current_version.bump_major()
    if bump_type == BumpType.minor:
        return current_version.bump_minor()
    if bump_type == BumpType.patch:
        return current_version.bump_patch()
    raise NotImplementedError("Unhandled bump type")


PYPROJECT_PATH = "./pyproject.toml"


def update_pyproject(current_version: VersionInfo, new_version: VersionInfo) -> None:
    with open(PYPROJECT_PATH) as f:
        content = f.read()
    new_content = content.replace(
        f'version = "{current_version}"', f'version = "{new_version}"'
    )
    if content == new_content:
        typer.secho("Couldn't bump version in pyproject.toml", fg=typer.colors.RED)
        raise typer.Exit(1)
    with open(PYPROJECT_PATH, "w") as f:
        f.write(new_content)
    typer.secho("Version updated with success", fg=typer.colors.GREEN)


RELEASE_NOTE_PATH = "./__release_notes__.md"


def get_release_notes() -> str:
    with open("./CHANGELOG.md", "r") as f:
        while not f.readline().strip() == "## [Unreleased]":
            pass
        content = ""
        while not (line := f.readline().strip()).startswith("## "):
            content = content + line + "\n"
    return content


def save_release_notes(release_notes: str) -> None:
    if os.path.exists(RELEASE_NOTE_PATH):
        typer.secho(
            f"Release note file {RELEASE_NOTE_PATH} already exists", fg=typer.colors.RED
        )
        raise typer.Exit(1)
    with open(RELEASE_NOTE_PATH, "w") as f:
        f.write(release_notes)
    typer.secho("Release note file generated with success", fg=typer.colors.GREEN)


CHANGELOG_PATH = "./CHANGELOG.md"


def update_changelog(current_version: VersionInfo, new_version: VersionInfo) -> None:
    today = datetime.date.today()
    date_str = f"{today.year}-{today.month:02d}-{today.day:02d}"
    with open(CHANGELOG_PATH, "r") as f:
        content = f.read()
    # Add version header
    content = content.replace(
        "## [Unreleased]", ("## [Unreleased]\n\n" f"## [{new_version}] - {date_str}")
    )
    # Add version links
    content = content.replace(
        f"[unreleased]: https://github.com/art049/odmantic/compare/v{current_version}...HEAD",
        (
            f"[{new_version}]: https://github.com/art049/odmantic/compare/v{current_version}...v{new_version}\n"
            f"[unreleased]: https://github.com/art049/odmantic/compare/v{new_version}...HEAD"
        ),
    )
    with open(CHANGELOG_PATH, "w") as f:
        f.write(content)
    typer.secho("Changelog updated with success", fg=typer.colors.GREEN)


VERSION_FILE_PATH = "__version__.txt"


def create_version_file(new_version: VersionInfo) -> None:
    if os.path.exists(VERSION_FILE_PATH):
        typer.secho(
            f"Version file {VERSION_FILE_PATH} already exists", fg=typer.colors.RED
        )
        raise typer.Exit(1)
    with open(VERSION_FILE_PATH, "w") as f:
        f.write(str(new_version))


def summarize(
    current_version: VersionInfo,
    new_version: VersionInfo,
    bump_type: BumpType,
    release_notes: str,
) -> None:
    typer.secho("Release summary:", fg=typer.colors.BLUE, bold=True)
    typer.secho(f"    Version bump: {bump_type.upper()}", bold=True)
    typer.secho(f"    Version change: {current_version} -> {new_version}", bold=True)
    typer.confirm("Continue to release notes preview ?", abort=True, default=True)

    release_header = typer.style(
        f"RELEASE NOTE {new_version}\n\n", fg=typer.colors.BLUE, bold=True
    )
    typer.echo_via_pager(release_header + release_notes)
    typer.confirm("Continue ?", abort=True, default=True)


def main() -> None:
    current_version = get_current_version()
    typer.secho(f"Current version: {current_version}", bold=True)
    bump_type: BumpType = typer.prompt(
        typer.style("Release type ?", fg=typer.colors.BLUE, bold=True),
        type=Choice(list(BumpType.__members__)),
        default=BumpType.patch,
        show_choices=True,
    )
    new_version = get_new_version(current_version, bump_type)
    release_notes = get_release_notes()
    summarize(current_version, new_version, bump_type, release_notes)
    save_release_notes(release_notes)
    update_pyproject(current_version, new_version)
    update_changelog(current_version, new_version)
    create_version_file(new_version)
    typer.confirm("Additionnal release commit files staged ?", abort=True, default=True)


if __name__ == "__main__":
    typer.run(main)
