import logging
import os
from typing import List

from cachetools import TTLCache
from telegram import Bot, ChatMember
from telegram.error import TelegramError

MEMBER_LIST_CACHE_TIME_SECONDS = 300  # 5 minutes


class TelegramPermissionChecker:
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.always_allowed_chat_ids: List[int] = self.get_always_allowed_chat_ids()
        self.temporary_allowed_user_ids: TTLCache = TTLCache(
            maxsize=10000, ttl=MEMBER_LIST_CACHE_TIME_SECONDS
        )

    @staticmethod
    def get_always_allowed_chat_ids() -> List[int]:
        allowed_ids_string = os.environ.get("TELEGRAM_ALLOWED_IDS")
        if not allowed_ids_string:
            raise RuntimeError("TELEGRAM_ALLOWED_IDS is not set")

        return [int(x) for x in allowed_ids_string.split(",")]

    async def is_user_or_group_allowed(self, user_id: int, chat_id: int) -> bool:
        if user_id == chat_id:
            return await self.is_user_allowed(user_id)
        else:
            return await self.is_group_allowed(chat_id)

    async def is_group_allowed(self, group_id: int) -> bool:
        return group_id in self.always_allowed_chat_ids

    async def is_user_allowed(self, user_id: int) -> bool:
        if user_id in self.temporary_allowed_user_ids:
            return True

        for chat_id in self.always_allowed_chat_ids:
            if await self.is_user_in_group(user_id, chat_id):
                self.temporary_allowed_user_ids[user_id] = True
                return True

        return False

    async def is_user_in_group(self, user_id: int, group_id: int) -> bool:
        try:
            chat_member: ChatMember = await self.bot.get_chat_member(group_id, user_id)
        except TelegramError as e:
            logging.exception(
                f"Failed to get chat member for user {user_id} in group {group_id}:\n{e}"
            )
            return False

        return chat_member.status in ["creator", "administrator", "member"]
