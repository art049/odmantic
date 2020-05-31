from typing import get_type_hints
from unittest.mock import MagicMock

import pytest
from odmantic.session import AIOSession

from .zoo.tree import TreeModel

# @pytest.fixture
# def mocked_session():
#     motor_client = MagicMock()
#     db_name = MagicMock
#     return AIOSession(motor_client, db_name)


# def test_query_type(mocked_session: AIOSession):
#     print(get_type_hints(session.query))
#     assert False
