from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from database import User, db

class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        
        if user:
            db.connect(reuse_if_open=True)
            try:
                db_user = User.get(User.telegram_id == user.id)
            except User.DoesNotExist:
                db_user = User.create(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name
                )
            
            data['db_user'] = db_user
            db.close()
        
        return await handler(event, data)
