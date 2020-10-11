import pytest

from odmantic import AIOEngine
from tests.zoo.player import Player
from tests.zoo.twitter_user import TwitterUser

pytestmark = pytest.mark.asyncio


async def test_twitter_user(engine: AIOEngine):
    main = TwitterUser()
    await engine.save(main)
    friends = [TwitterUser() for _ in range(25)]
    await engine.save_all(friends)
    friend_ids = [f.id for f in friends]
    main.following = friend_ids
    await engine.save(main)

    fetched_main = await engine.find_one(TwitterUser, TwitterUser.id == main.id)
    assert fetched_main is not None
    assert fetched_main == main
    assert set(friend_ids) == set(fetched_main.following)


async def test_player(engine: AIOEngine):
    leeroy = Player(name="Leeroy Jenkins")
    await engine.save(leeroy)
    fetched = await engine.find_one(Player)
    assert fetched == leeroy
