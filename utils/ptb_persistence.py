import json
from telegram.ext import BasePersistence
from redis.asyncio import Redis

class RedisPersistence(BasePersistence):
    def __init__(self, redis: Redis):
        super().__init__()
        self.redis = redis

    async def get_chat_data(self):
        data = await self.redis.get('chat_data')
        return json.loads(data) if data else {}

    async def update_chat_data(self, chat_id, data):
        chat_data = await self.get_chat_data()
        chat_data[str(chat_id)] = data
        await self.redis.set('chat_data', json.dumps(chat_data))

    async def get_user_data(self):
        data = await self.redis.get('user_data')
        return json.loads(data) if data else {}

    async def update_user_data(self, user_id, data):
        user_data = await self.get_user_data()
        user_data[str(user_id)] = data
        await self.redis.set('user_data', json.dumps(user_data))

    async def get_bot_data(self):
        data = await self.redis.get('bot_data')
        return json.loads(data) if data else {}

    async def update_bot_data(self, data):
        await self.redis.set('bot_data', json.dumps(data))

    async def get_conversations(self, name):
        data = await self.redis.get(f'conversations:{name}')
        return json.loads(data) if data else {}

    async def update_conversation(self, name, key, new_state):
        conversations = await self.get_conversations(name)
        conversations[str(key)] = new_state
        await self.redis.set(f'conversations:{name}', json.dumps(conversations))

    # --- Реализация абстрактных методов-заглушек ---
    async def drop_chat_data(self, chat_id):
        chat_data = await self.get_chat_data()
        chat_data.pop(str(chat_id), None)
        await self.redis.set('chat_data', json.dumps(chat_data))

    async def drop_user_data(self, user_id):
        user_data = await self.get_user_data()
        user_data.pop(str(user_id), None)
        await self.redis.set('user_data', json.dumps(user_data))

    async def flush(self):
        # Можно реализовать удаление всех ключей, но оставим пустым
        pass

    async def get_callback_data(self):
        data = await self.redis.get('callback_data')
        return json.loads(data) if data else {}

    async def update_callback_data(self, data):
        await self.redis.set('callback_data', json.dumps(data))

    async def refresh_bot_data(self, bot_data):
        await self.update_bot_data(bot_data)

    async def refresh_chat_data(self, chat_id, chat_data):
        await self.update_chat_data(chat_id, chat_data)

    async def refresh_user_data(self, user_id, user_data):
        await self.update_user_data(user_id, user_data)
