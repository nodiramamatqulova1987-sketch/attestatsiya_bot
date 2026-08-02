from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ---------------------------------------------------------------------------
#  FOYDALANUVCHI KLAVIATURALARI
# ---------------------------------------------------------------------------

def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📚 Fanlar va Testlar"),
        KeyboardButton(text="🎓 Haqiqiy Imtihon"),
    )
    builder.row(
        KeyboardButton(text="🏆 Reyting"),
        KeyboardButton(text="📊 Mening natijalarim"),
    )
    builder.row(KeyboardButton(text="✉️ Adminga murojaat"))
    if is_admin:
        builder.row(KeyboardButton(text="⚙️ Admin panel"))
    return builder.as_markup(resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


def subjects_kb(subjects) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for subject in subjects:
        builder.button(text=subject["name"], callback_data=f"subject:{subject['id']}")
    builder.adjust(2)
    return builder.as_markup()


def test_question_kb(question_index: int, options: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for letter, text in options.items():
        builder.button(
            text=f"{letter}) {text}",
            callback_data=f"answer:{question_index}:{letter}",
        )
    builder.adjust(1)
    return builder.as_markup()


def subscription_kb(channels) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        link = ch["invite_link"] or f"https://t.me/{str(ch['chat_id']).lstrip('@')}"
        builder.row(InlineKeyboardButton(text=f"➕ {ch['title']}", url=link))
    builder.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
    return builder.as_markup()


def appeal_answer_kb(appeal_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ Javob berish", callback_data=f"reply_appeal:{appeal_id}")
    return builder.as_markup()


# ---------------------------------------------------------------------------
#  ADMIN PANEL KLAVIATURALARI
# ---------------------------------------------------------------------------

def admin_panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Fanlarni boshqarish", callback_data="adm:subjects")
    builder.button(text="❓ Savollarni boshqarish", callback_data="adm:questions")
    builder.button(text="👥 Adminlarni boshqarish", callback_data="adm:admins")
    builder.button(text="📣 Kanallarni boshqarish", callback_data="adm:channels")
    builder.button(text="📊 Statistika", callback_data="adm:stats")
    builder.button(text="👤 Foydalanuvchilar", callback_data="adm:users")
    builder.button(text="📢 Xabar yuborish", callback_data="adm:broadcast")
    builder.button(text="📩 Murojaatlar", callback_data="adm:appeals")
    builder.button(text="🔄 Ballarni nollash", callback_data="adm:reset_scores")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Admin panelga qaytish", callback_data="adm:back")
    return builder.as_markup()


# ---- Fanlarni boshqarish ----

def subjects_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Fan qo'shish", callback_data="adm:add_subject")
    builder.button(text="➖ Fan o'chirish", callback_data="adm:remove_subject")
    builder.button(text="📋 Fanlar ro'yxati", callback_data="adm:list_subjects")
    builder.button(text="⬅️ Orqaga", callback_data="adm:back")
    builder.adjust(1)
    return builder.as_markup()


def subjects_remove_kb(subjects) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in subjects:
        builder.button(text=f"❌ {s['name']}", callback_data=f"adm:del_subject:{s['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="adm:subjects")
    builder.adjust(1)
    return builder.as_markup()


# ---- Savollarni boshqarish ----

def questions_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Savol qo'shish", callback_data="adm:add_question")
    builder.button(text="📋 Savollar soni", callback_data="adm:questions_count")
    builder.button(text="➖ Savol o'chirish (ID orqali)", callback_data="adm:remove_question")
    builder.button(text="⬅️ Orqaga", callback_data="adm:back")
    builder.adjust(1)
    return builder.as_markup()


def add_question_subjects_kb(subjects) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for subject in subjects:
        builder.button(text=subject["name"], callback_data=f"adm:qsubject:{subject['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="adm:questions")
    builder.adjust(2)
    return builder.as_markup()


# ---- Kanallarni boshqarish ----

def channels_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Kanal/guruh qo'shish", callback_data="adm:add_channel")
    builder.button(text="➖ Kanal/guruh o'chirish", callback_data="adm:remove_channel")
    builder.button(text="📋 Ro'yxatni ko'rish", callback_data="adm:list_channels")
    builder.button(text="⬅️ Orqaga", callback_data="adm:back")
    builder.adjust(1)
    return builder.as_markup()


def channels_remove_kb(channels) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(
            text=f"❌ {ch['title'] or ch['chat_id']}",
            callback_data=f"adm:del_channel:{ch['chat_id']}",
        )
    builder.button(text="⬅️ Orqaga", callback_data="adm:channels")
    builder.adjust(1)
    return builder.as_markup()


# ---- Adminlarni boshqarish ----

def admins_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Admin qo'shish", callback_data="adm:add_admin")
    builder.button(text="➖ Admin o'chirish", callback_data="adm:remove_admin")
    builder.button(text="📋 Adminlar ro'yxati", callback_data="adm:list_admins")
    builder.button(text="⬅️ Orqaga", callback_data="adm:back")
    builder.adjust(1)
    return builder.as_markup()


# ---- Xabar yuborish (rassilka) ----

def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yuborish", callback_data="adm:confirm_broadcast")
    builder.button(text="❌ Bekor qilish", callback_data="adm:cancel_broadcast")
    builder.adjust(2)
    return builder.as_markup()


# ---- Foydalanuvchilar / ballarni nollash ----

def confirm_reset_scores_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, hammasini nollash", callback_data="adm:confirm_reset")
    builder.button(text="❌ Bekor qilish", callback_data="adm:back")
    builder.adjust(1)
    return builder.as_markup()


def appeals_list_kb(appeals) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for a in appeals:
        preview = a["message_text"][:25] + ("..." if len(a["message_text"]) > 25 else "")
        builder.button(text=f"#{a['id']} — {preview}", callback_data=f"reply_appeal:{a['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="adm:back")
    builder.adjust(1)
    return builder.as_markup()
