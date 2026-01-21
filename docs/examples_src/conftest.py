import pathlib

import pytest


def pytest_generate_tests(metafunc) -> None:
    example_src_path = pathlib.Path(__file__).parent
    print(example_src_path.relative_to(example_src_path))

    params = []
    for file in example_src_path.glob("*/*.py"):
        package_name = file.parent.relative_to(example_src_path)
        module_name = file.name[:-3]
        params.append(pytest.param(file, id=f"{package_name}.{module_name}"))
    metafunc.parametrize("example", list(params))
