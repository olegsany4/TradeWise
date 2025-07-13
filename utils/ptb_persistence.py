import pickle
from redis.asyncio import Redis
from telegram.ext import BasePersistence, PersistenceInput
from typing import Dict, Any, Optional, Tuple

class RedisPersistence(BasePersistence):
    def __init__(self, redis: Redis):
        super().__init__(
            store_data=PersistenceInput(
                user_data=True,
                chat_data=True,
                bot_data=True,
                callback_data=True
            )
        )
        self.redis = redis

    async def get_chat_data(self) -> Dict[int, Any]:
        data = await self.redis.get("chat_data")
        return pickle.loads(data) if data else {}

    async def update_chat_data(self, chat_id: int, data: Dict) -> None:
        chat_data = await self.get_chat_data()
        chat_data[chat_id] = data
        await self.redis.set("chat_data", pickle.dumps(chat_data))

    async def get_user_data(self) -> Dict[int, Any]:
        data = await self.redis.get("user_data")
        return pickle.loads(data) if data else {}

    async def update_user_data(self, user_id: int, data: Dict) -> None:
        user_data = await self.get_user_data()
        user_data[user_id] = data
        await self.redis.set("user_data", pickle.dumps(user_data))

    async def get_bot_data(self) -> Dict[str, Any]:
        data = await self.redis.get("bot_data")
        return pickle.loads(data) if data else {}

    async def update_bot_data(self, data: Dict) -> None:
        await self.redis.set("bot_data", pickle.dumps(data))

    async def get_callback_data(self) -> Optional[Dict]:
        data = await self.redis.get("callback_data")
        return pickle.loads(data) if data else None

    async def update_callback_data(self, data: Dict) -> None:
        await self.redis.set("callback_data", pickle.dumps(data))

    async def get_conversations(self, name: str) -> Dict[Tuple[int, ...], Any]:
        pattern = f"conversation:{name}:*"
        keys = await self.redis.keys(pattern)
        conversations = {}
        for key in keys:
            key_str = key.decode()
            parts = key_str.split(':')
            if len(parts) < 3:
                continue
            key_tuple = tuple(map(int, parts[2].split('_')))
            state = await self.redis.get(key)
            if state:
                conversations[key_tuple] = pickle.loads(state)
        return conversations

    async def update_conversation(
        self, 
        name: str, 
        key: Tuple[int, ...], 
        new_state: Optional[object]
    ) -> None:
        redis_key = f"conversation:{name}:{'_'.join(map(str, key))}"
        if new_state is None:
            await self.redis.delete(redis_key)
        else:
            await self.redis.set(redis_key, pickle.dumps(new_state))

    async def drop_chat_data(self, chat_id: int) -> None:
        chat_data = await self.get_chat_data()
        chat_data.pop(chat_id, None)
        await self.redis.set("chat_data", pickle.dumps(chat_data))

    async def drop_user_data(self, user_id: int) -> None:
        user_data = await self.get_user_data()
        user_data.pop(user_id, None)
        await self.redis.set("user_data", pickle.dumps(user_data))

    async def refresh_bot_data(self, bot_data: Dict) -> None:
        await self.update_bot_data(bot_data)

    async def refresh_chat_data(self, chat_id: int, chat_data: Dict) -> None:
        await self.update_chat_data(chat_id, chat_data)

    async def refresh_user_data(self, user_id: int, user_data: Dict) -> None:
        await self.update_user_data(user_id, user_data)

    async def flush(self) -> None:
        pass