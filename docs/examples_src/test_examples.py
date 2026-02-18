import re
from pathlib import Path

import pytest

import odmantic
from tests.integration.conftest import *


def normalize_output(output: str) -> str:
    # Remove whitespaces
    output = output.strip().replace(", ", ",")
    # Remove comma formating
    output = (
        output.replace("(\n", "(")
        .replace("[\n", "[")
        .replace(",\n", ",")
        .replace("\n)", ")")
        .replace("\n]", "]")
    )
    output = re.sub(r"\(\s*", "(", output)
    output = re.sub(r"\[\s*", "[", output)
    output = re.sub(r",\s*", ",", output)
    # Remove trailing commas
    output = output.replace(",)", ")").replace(",]", "]").replace(",}", "}")
    # Only use single quotes
    output = output.replace('"', "'")

    # Ignore pattern related to tests
    # Ignore ObjectId value
    output = re.sub(r"[a-f0-9]{24}", "...", output)
    # Ignore datetimes
    output = re.sub(r"datetime.datetime\(.*?\)", "<ignored_datetime_value>", output)
    # Motor version
    output = re.sub(r"name='Motor',version='.*'", "<motor_version_tag>", output)
    # Query expression
    output = re.sub(r"QueryExpression\(.*\)", "", output, flags=re.MULTILINE)

    return output.strip()


@pytest.mark.asyncio
async def test_documentation_example(
    example: Path, engine, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(odmantic, "AIOEngine", lambda: engine)
    with example.open() as f:
        lines = f.readlines()
    content = "async def __test_function__():\n"
    expected_output = ""
    for line_no, line in enumerate(lines):
        content += f"    {line}"
        if line.strip().startswith("#> "):
            expected_output += "\n"
            expected_output += line.strip()[3:]
        elif line.startswith(("#>", "# >")):
            raise RuntimeError(f"{example}:{line_no+1}: Invalid stdout decoration")

    locals_ = {}
    globals_ = {}
    exec(content, globals_, locals_)
    await locals_["__test_function__"]()
    out, _ = capsys.readouterr()
    assert normalize_output(out) == normalize_output(expected_output)
