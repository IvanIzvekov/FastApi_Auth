from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

engine = create_async_engine(settings.POSTGRES_URL, future=True, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

import inspect

async def get_db():
    async with AsyncSessionLocal() as session:
        print("DB called from:", inspect.stack()[1].function)
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            print("Session rollback due to:", e)
            raise
        finally:
            await session.close()