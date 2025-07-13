from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from db.models import Base
from redis.asyncio import Redis
from config import RedisConfig

engine = create_async_engine(DB_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

_redis = None

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session():
    async with async_session() as session:
        yield session

async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis(
            host=RedisConfig.HOST,
            port=RedisConfig.PORT,
            db=RedisConfig.DB,
            decode_responses=False
        )
    return _redis