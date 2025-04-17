from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from typing import Optional
from models import UserModel, SessionModel

class UserRepository:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def save(self, user: UserModel):
        async with AsyncSession(self.engine) as session:
            session.add(user)
            await session.commit()

    async def update(self, user: UserModel):
        async with AsyncSession(self.engine) as session:
            session.add(user)
            await session.commit()

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        async with AsyncSession(self.engine) as session:
            result = await session.exec(select(UserModel).where(UserModel.email == email))
            return result.first()

    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        async with AsyncSession(self.engine) as session:
            result = await session.exec(select(UserModel).where(UserModel.username == username))
            return result.first()

    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        async with AsyncSession(self.engine) as session:
            result = await session.exec(select(UserModel).where(UserModel.id == user_id))
            return result.first()

    async def save_session(self, session_obj: SessionModel):
        async with AsyncSession(self.engine) as session:
            session.add(session_obj)
            await session.commit()

    async def get_user_by_session_token(self, token: str) -> Optional[UserModel]:
        async with AsyncSession(self.engine) as session:
            result = await session.exec(select(SessionModel).where(SessionModel.session_token == token))
            session_entry = result.first()
            if session_entry:
                return await self.get_user_by_id(session_entry.user_id)
        return None

    async def delete_session(self, token: str):
        async with AsyncSession(self.engine) as session:
            result = await session.exec(select(SessionModel).where(SessionModel.session_token == token))
            session_entry = result.first()
            if session_entry:
                await session.delete(session_entry)
                await session.commit()
