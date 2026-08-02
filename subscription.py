"""
Foydalanuvchining barcha majburiy kanal/guruhlarga a'zo bo'lganini tekshirish.
"""

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

import database as db

# Bot a'zolikni ko'ra oladigan holatlar (a'zo hisoblanadigan statuslar)
ALLOWED_STATUSES = {"member", "administrator", "creator"}


async def get_not_subscribed_channels(bot: Bot, user_id: int):
    """
    Foydalanuvchi a'zo bo'lmagan kanal/guruhlar ro'yxatini qaytaradi.
    Agar ro'yxat bo'sh bo'lsa — foydalanuvchi hamma joyga a'zo demakdir.
    """
    channels = await db.get_all_channels()
    not_subscribed = []

    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            if member.status not in ALLOWED_STATUSES:
                not_subscribed.append(channel)
        except TelegramBadRequest:
            # Bot kanalga admin qilib qo'shilmagan yoki chat_id noto'g'ri bo'lsa,
            # foydalanuvchini bloklamaslik uchun bu kanalni tekshiruvdan o'tkazib yuboramiz,
            # lekin log ko'rinishida ro'yxatga qo'shamiz (ixtiyoriy).
            continue
        except Exception:
            continue

    return not_subscribed
