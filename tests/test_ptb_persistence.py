import pytest
import asyncio
from fakeredis.aioredis import FakeRedis as Redis
from utils.ptb_persistence import RedisPersistence

@pytest.mark.asyncio
async def test_redis_persistence():
    redis = Redis()
    persistence = RedisPersistence(redis)
    await persistence.update_chat_data(123, {"state": "active"})
    data = await persistence.get_chat_data()
    assert data.get(123) == {"state": "active"}
