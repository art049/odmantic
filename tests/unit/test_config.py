import pytest
from inline_snapshot import snapshot

from odmantic import Model


def test_config_enforced_pydantic_option():
    with pytest.raises(ValueError) as exc_info:

        class M(Model):
            a: int

            model_config = {"validate_assignment": True}

    assert str(exc_info.value) == snapshot(
        "'M': configuration attribute 'validate_assignment' is enforced to True by ODMantic and cannot be changed"  # noqa: E501
    )


def test_config_unsupported_pydantic_option():
    with pytest.raises(ValueError) as exc_info:

        class M(Model):
            a: int

            model_config = {"frozen": True}

    assert str(exc_info.value) == snapshot(
        "'M': configuration attribute 'frozen' from Pydantic is not supported"
    )


def test_config_unknown_option():
    with pytest.raises(ValueError) as exc_info:

        class M(Model):
            a: int

            model_config = {"this_config_doesnt_exist": True}

    assert str(exc_info.value) == snapshot(
        "'M': unknown configuration attribute 'this_config_doesnt_exist'"
    )
