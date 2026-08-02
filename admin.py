import asyncio
import datetime
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import database as db
import keyboards as kb
from config import SUPER_ADMINS
from states import (
    BroadcastStates,
    AddAdminStates,
    RemoveAdminStates,
    AddChannelStates,
    AddSubjectStates,
    UserStatsStates,
    RemoveQuestionStates,
    AddQuestionStates,
)

router = Router()
logger = logging.getLogger(__name__)


async def _is_admin_guard(user_id: int) -> bool:
    return await db.is_admin(user_id)


def _display_name(row) -> str:
    if row["username"]:
        return f"@{row['username']}"
    return row["full_name"] or f"ID {row['user_id']}"


# ---------------------------------------------------------------------------
#  ADMIN PANELGA KIRISH
# ---------------------------------------------------------------------------

@router.message(F.text == "⚙️ Admin panel")
@router.message(Command("admin"))
async def open_admin_panel(message: Message, state: FSMContext):
    await state.clear()
    if not await _is_admin_guard(message.from_user.id):
        await message.answer("⛔️ Sizda admin panelga kirish huquqi yo'q.")
        return
    await message.answer("⚙️ <b>Admin boshqaruv paneli:</b>\n\nKerakli bo'limni tanlang:",
                          reply_markup=kb.admin_panel_kb())


@router.callback_query(F.data == "adm:back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await callback.message.edit_text("⚙️ <b>Admin boshqaruv paneli:</b>\n\nKerakli bo'limni tanlang:",
                                      reply_markup=kb.admin_panel_kb())
    await callback.answer()


# ---------------------------------------------------------------------------
#  STATISTIKA (umumiy + vaqt bo'yicha)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:stats")
async def show_stats(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    users_count = await db.get_users_count()
    tests_count = await db.get_total_tests_count()
    channels_count = len(await db.get_all_channels())
    admins_count = len(await db.get_all_admins())
    subjects_count = len(await db.get_subjects())
    questions_count = await db.get_total_questions_count()
    pending_appeals = await db.get_pending_appeals_count()

    now = datetime.datetime.now()
    day_stats = await db.get_stats_since((now - datetime.timedelta(days=1)).isoformat())
    week_stats = await db.get_stats_since((now - datetime.timedelta(days=7)).isoformat())
    month_stats = await db.get_stats_since((now - datetime.timedelta(days=30)).isoformat())

    text = (
        "📊 <b>Umumiy statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{users_count}</b>\n"
        f"📝 Jami yechilgan testlar: <b>{tests_count}</b>\n"
        f"📚 Jami fanlar: <b>{subjects_count}</b>\n"
        f"❓ Jami savollar: <b>{questions_count}</b>\n"
        f"🔗 Majburiy obuna kanallari: <b>{channels_count}</b>\n"
        f"👮 Jami adminlar: <b>{admins_count}</b>\n"
        f"📩 Javob kutayotgan murojaatlar: <b>{pending_appeals}</b>\n\n"
        "🕒 <b>Vaqt bo'yicha:</b>\n"
        f"📅 Bugun — yangi: <b>{day_stats['new_users']}</b> ta, testlar: <b>{day_stats['tests_taken']}</b> ta\n"
        f"📅 So'nggi 7 kun — yangi: <b>{week_stats['new_users']}</b> ta, testlar: <b>{week_stats['tests_taken']}</b> ta\n"
        f"📅 So'nggi 30 kun — yangi: <b>{month_stats['new_users']}</b> ta, testlar: <b>{month_stats['tests_taken']}</b> ta"
    )
    await callback.message.edit_text(text, reply_markup=kb.back_to_admin_kb())
    await callback.answer()


# ---------------------------------------------------------------------------
#  FOYDALANUVCHILAR (ro'yxat + alohida statistika)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:users")
async def users_overview(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    await state.set_state(UserStatsStates.waiting_for_id)

    total = await db.get_users_count()
    last_users = await db.get_all_users(limit=10)

    lines = [
        f"👤 <b>Foydalanuvchilar</b> (jami: {total} ta)\n",
        "🆕 Oxirgi qo'shilganlar:",
    ]
    for u in last_users:
        lines.append(f"• {_display_name(u)} — <code>{u['user_id']}</code> — {u['score']} ball")

    lines.append("\n🔎 Muayyan foydalanuvchi statistikasini ko'rish uchun uning "
                  "Telegram ID raqamini yuboring:")

    await callback.message.edit_text("\n".join(lines), reply_markup=kb.back_to_admin_kb())
    await callback.answer()


@router.message(UserStatsStates.waiting_for_id)
async def show_user_stats(message: Message, state: FSMContext):
    if not await _is_admin_guard(message.from_user.id):
        return

    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer("❗️ Iltimos, faqat raqamlardan iborat ID yuboring.")
        return

    user_id = int(message.text.strip())
    await state.clear()

    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Bunday foydalanuvchi bazada topilmadi.",
                              reply_markup=kb.back_to_admin_kb())
        return

    results = await db.get_user_results(user_id)
    rank = await db.get_user_rank(user_id)
    username_part = f"@{user['username']}" if user["username"] else "—"
    accuracy = round((user["correct_count"] / user["total_answered"]) * 100, 1) if user["total_answered"] else 0.0

    lines = [
        "👤 <b>Foydalanuvchi ma'lumotlari</b>\n",
        f"Ism: {user['full_name']}",
        f"Username: {username_part}",
        f"ID: <code>{user['user_id']}</code>",
        f"Ro'yxatdan o'tgan sana: {user['joined_at'].split('T')[0]}",
        f"Holati: {'🚫 Bloklangan' if user['is_blocked'] else '✅ Faol'}\n",
        f"🏆 O'rin: <b>{rank}</b>",
        f"⭐ Ball: <b>{user['score']}</b>",
        f"📝 Jami ishlangan: <b>{user['total_answered']}</b>",
        f"✅ To'g'ri: <b>{user['correct_count']}</b>",
        f"❌ Noto'g'ri: <b>{user['wrong_count']}</b>",
        f"📈 O'rtacha aniqlik: <b>{accuracy}%</b>",
        f"📝 Jami yechilgan testlar soni: <b>{len(results)}</b>\n",
    ]

    if results:
        lines.append("📋 <b>So'nggi natijalar:</b>")
        for r in results[:10]:
            percent = round((r["correct_count"] / r["total_count"]) * 100) if r["total_count"] else 0
            date_str = r["date"].split("T")[0]
            subj = r["subject_name"] or "Aralash (imtihon)"
            lines.append(f"• {date_str} — {subj}: {r['correct_count']}/{r['total_count']} ({percent}%)")

    await message.answer("\n".join(lines), reply_markup=kb.back_to_admin_kb())


# ---------------------------------------------------------------------------
#  BALLARNI NOLLASH
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:reset_scores")
async def ask_reset_scores(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await callback.message.edit_text(
        "🔄 <b>Diqqat!</b>\n\n"
        "Ushbu amal barcha foydalanuvchilarning ballari, to'g'ri/noto'g'ri javoblari "
        "va reytingini <b>0 ga tushiradi</b>. Bu amalni ortga qaytarib bo'lmaydi.\n\n"
        "Rostdan ham davom etasizmi?",
        reply_markup=kb.confirm_reset_scores_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "adm:confirm_reset")
async def confirm_reset_scores(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    count = await db.reset_all_scores()
    await callback.message.edit_text(
        f"✅ {count} ta foydalanuvchining ballari muvaffaqiyatli 0 ga tushirildi.",
        reply_markup=kb.back_to_admin_kb(),
    )
    await callback.answer("Ballar nollandi!")


# ---------------------------------------------------------------------------
#  XABAR YUBORISH (RASSILKA)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.edit_text(
        "📢 Foydalanuvchilarga yubormoqchi bo'lgan xabarni (matn, rasm, video yoki "
        "boshqa media, sarlavha bilan ham bo'lishi mumkin) yuboring:",
        reply_markup=kb.back_to_admin_kb(),
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def preview_broadcast(message: Message, state: FSMContext):
    if not await _is_admin_guard(message.from_user.id):
        return

    await state.update_data(broadcast_chat_id=message.chat.id, broadcast_message_id=message.message_id)
    await state.set_state(BroadcastStates.waiting_for_confirm)

    await message.answer(
        "⬆️ Ushbu xabar barcha foydalanuvchilarga yuborilsinmi?",
        reply_markup=kb.confirm_broadcast_kb(),
    )


@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "adm:cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Xabar yuborish bekor qilindi.",
                                      reply_markup=kb.back_to_admin_kb())
    await callback.answer()


@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "adm:confirm_broadcast")
async def confirm_broadcast(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    src_chat_id = data["broadcast_chat_id"]
    src_message_id = data["broadcast_message_id"]
    await state.clear()

    await callback.message.edit_text("⏳ Xabar yuborilmoqda, iltimos kuting...")

    user_ids = await db.get_all_user_ids()
    success, failed = 0, 0

    for user_id in user_ids:
        try:
            await bot.copy_message(chat_id=user_id, from_chat_id=src_chat_id, message_id=src_message_id)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # Telegram limitlariga tushib qolmaslik uchun kichik pauza

    await callback.message.answer(
        f"✅ Xabar yuborish yakunlandi!\n\n"
        f"Yuborildi: <b>{success}</b>\nYuborilmadi: <b>{failed}</b>",
        reply_markup=kb.back_to_admin_kb(),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
#  MUROJAATLAR
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:appeals")
async def list_pending_appeals(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    appeals = await db.get_pending_appeals()
    if not appeals:
        await callback.message.edit_text("📩 Hozircha javobsiz murojaatlar yo'q.",
                                          reply_markup=kb.back_to_admin_kb())
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📩 <b>Javob kutayotgan murojaatlar</b> ({len(appeals)} ta):\n\n"
        "Javob berish uchun murojaatni tanlang:",
        reply_markup=kb.appeals_list_kb(appeals),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
#  FANLARNI BOSHQARISH
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:subjects")
async def subjects_menu(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("📚 <b>Fanlarni boshqarish:</b>",
                                      reply_markup=kb.subjects_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "adm:add_subject")
async def ask_subject_name(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.set_state(AddSubjectStates.waiting_for_name)
    await callback.message.edit_text(
        "➕ Yangi fan nomini kiriting (masalan: <i>Chizmachilik</i>):",
        reply_markup=kb.back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AddSubjectStates.waiting_for_name)
async def add_subject_handler(message: Message, state: FSMContext):
    if not await _is_admin_guard(message.from_user.id):
        return
    if not message.text:
        await message.answer("❗️ Iltimos, fan nomini matn ko'rinishida yuboring.")
        return

    name = message.text.strip()
    await state.clear()

    added = await db.add_subject(name)
    if added:
        await message.answer(f"✅ \"{name}\" fani muvaffaqiyatli qo'shildi.",
                              reply_markup=kb.back_to_admin_kb())
    else:
        await message.answer("ℹ️ Bu fan allaqachon ro'yxatda mavjud.",
                              reply_markup=kb.back_to_admin_kb())


@router.callback_query(F.data == "adm:remove_subject")
async def ask_subject_to_remove(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    subjects = await db.get_subjects()
    if not subjects:
        await callback.answer("Ro'yxat bo'sh.", show_alert=True)
        return

    await callback.message.edit_text(
        "➖ O'chirmoqchi bo'lgan fanni tanlang:\n"
        "⚠️ Fan o'chirilsa, unga tegishli barcha savollar ham o'chib ketadi.",
        reply_markup=kb.subjects_remove_kb(subjects),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:del_subject:"))
async def remove_subject_handler(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    subject_id = int(callback.data.split(":")[2])
    removed = await db.remove_subject(subject_id)

    if removed:
        await callback.answer("✅ O'chirildi.")
    else:
        await callback.answer("❌ Topilmadi.", show_alert=True)

    subjects = await db.get_subjects()
    if subjects:
        await callback.message.edit_text("➖ O'chirmoqchi bo'lgan fanni tanlang:",
                                          reply_markup=kb.subjects_remove_kb(subjects))
    else:
        await callback.message.edit_text("📚 <b>Fanlarni boshqarish:</b>\n\nRo'yxat bo'sh.",
                                          reply_markup=kb.subjects_menu_kb())


@router.callback_query(F.data == "adm:list_subjects")
async def list_subjects(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    subjects = await db.get_subjects()
    if not subjects:
        text = "📚 <b>Fanlar ro'yxati</b>\n\nHozircha fanlar mavjud emas."
    else:
        lines = ["📚 <b>Fanlar ro'yxati</b>\n"]
        for s in subjects:
            count = await db.get_questions_count(s["id"])
            lines.append(f"• {s['name']} — {count} ta savol")
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=kb.subjects_menu_kb())
    await callback.answer()


# ---------------------------------------------------------------------------
#  SAVOLLARNI BOSHQARISH
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:questions")
async def questions_menu(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.clear()

    subjects = await db.get_subjects()
    if not subjects:
        await callback.message.edit_text("Avval fan qo'shing!", reply_markup=kb.back_to_admin_kb())
        await callback.answer()
        return

    await callback.message.edit_text("❓ <b>Savollarni boshqarish:</b>",
                                      reply_markup=kb.questions_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "adm:questions_count")
async def questions_count(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    subjects = await db.get_subjects()
    lines = ["📋 <b>Fanlar bo'yicha savollar soni:</b>\n"]
    total = 0
    for s in subjects:
        count = await db.get_questions_count(s["id"])
        total += count
        lines.append(f"• {s['name']}: <b>{count}</b> ta")
    lines.append(f"\nJami: <b>{total}</b> ta savol")

    await callback.message.edit_text("\n".join(lines), reply_markup=kb.questions_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "adm:remove_question")
async def ask_question_id_to_remove(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.set_state(RemoveQuestionStates.waiting_for_id)
    await callback.message.edit_text(
        "➖ O'chirmoqchi bo'lgan savolning ID raqamini kiriting.\n"
        "(ID ni bilmasangiz, \"📋 Savollar soni\" orqali fanlarni tekshiring "
        "yoki bazani to'g'ridan-to'g'ri ko'ring.)",
        reply_markup=kb.back_to_admin_kb(),
    )
    await callback.answer()


@router.message(RemoveQuestionStates.waiting_for_id)
async def remove_question_handler(message: Message, state: FSMContext):
    if not await _is_admin_guard(message.from_user.id):
        return
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❗️ Iltimos, faqat raqamlardan iborat savol ID sini yuboring.")
        return

    question_id = int(message.text.strip())
    await state.clear()

    removed = await db.delete_question(question_id)
    if removed:
        await message.answer(f"✅ #{question_id}-savol o'chirildi.", reply_markup=kb.back_to_admin_kb())
    else:
        await message.answer("❌ Bunday ID li savol topilmadi.", reply_markup=kb.back_to_admin_kb())


@router.callback_query(F.data == "adm:add_question")
async def choose_subject_for_question(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    subjects = await db.get_subjects()
    if not subjects:
        await callback.answer("Avval fan qo'shing!", show_alert=True)
        return

    await state.set_state(AddQuestionStates.choosing_subject)
    await callback.message.edit_text(
        "➕ Savol qo'shmoqchi bo'lgan fanni tanlang:",
        reply_markup=kb.add_question_subjects_kb(subjects),
    )
    await callback.answer()


@router.callback_query(AddQuestionStates.choosing_subject, F.data.startswith("adm:qsubject:"))
async def ask_question_text(callback: CallbackQuery, state: FSMContext):
    subject_id = int(callback.data.split(":")[2])
    subject = await db.get_subject_by_id(subject_id)

    await state.update_data(subject_id=subject_id, subject_name=subject["name"])
    await state.set_state(AddQuestionStates.waiting_question)

    await callback.message.edit_text(
        f"📘 Fan: <b>{subject['name']}</b>\n\n❓ Savol matnini kiriting:"
    )
    await callback.answer()


@router.message(AddQuestionStates.waiting_question)
async def ask_option_a(message: Message, state: FSMContext):
    await state.update_data(question_text=message.text)
    await state.set_state(AddQuestionStates.waiting_option_a)
    await message.answer("🅰️ A) variantini kiriting:")


@router.message(AddQuestionStates.waiting_option_a)
async def ask_option_b(message: Message, state: FSMContext):
    await state.update_data(option_a=message.text)
    await state.set_state(AddQuestionStates.waiting_option_b)
    await message.answer("🅱️ B) variantini kiriting:")


@router.message(AddQuestionStates.waiting_option_b)
async def ask_option_c(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text)
    await state.set_state(AddQuestionStates.waiting_option_c)
    await message.answer("C) variantini kiriting:")


@router.message(AddQuestionStates.waiting_option_c)
async def ask_option_d(message: Message, state: FSMContext):
    await state.update_data(option_c=message.text)
    await state.set_state(AddQuestionStates.waiting_option_d)
    await message.answer("D) variantini kiriting:")


@router.message(AddQuestionStates.waiting_option_d)
async def ask_correct_option(message: Message, state: FSMContext):
    await state.update_data(option_d=message.text)
    await state.set_state(AddQuestionStates.waiting_correct)
    await message.answer("✅ To'g'ri javob qaysi harf? (A, B, C yoki D) kiriting:")


@router.message(AddQuestionStates.waiting_correct)
async def save_new_question(message: Message, state: FSMContext):
    correct = message.text.strip().upper() if message.text else ""
    if correct not in ("A", "B", "C", "D"):
        await message.answer("❗️ Iltimos, faqat A, B, C yoki D harflaridan birini yuboring.")
        return

    data = await state.get_data()
    await db.add_question(
        subject_id=data["subject_id"],
        question=data["question_text"],
        option_a=data["option_a"],
        option_b=data["option_b"],
        option_c=data["option_c"],
        option_d=data["option_d"],
        correct_option=correct,
    )
    await state.clear()

    await message.answer(
        f"✅ Savol muvaffaqiyatli <b>{data['subject_name']}</b> faniga qo'shildi!",
        reply_markup=kb.back_to_admin_kb(),
    )


# ---------------------------------------------------------------------------
#  KANALLARNI BOSHQARISH (majburiy obuna)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:channels")
async def channels_menu(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("📣 <b>Majburiy kanallar:</b>",
                                      reply_markup=kb.channels_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "adm:add_channel")
async def ask_channel_to_add(callback: CallbackQuery, state: FSMContext):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.set_state(AddChannelStates.waiting_for_chat_id)
    await callback.message.edit_text(
        "➕ Kanal/guruhni qo'shish uchun:\n"
        "1. Botni o'sha kanal/guruhga <b>admin</b> qilib qo'shing.\n"
        "2. Kanal/guruhning username'ini (masalan <code>@mychannel</code>) "
        "yoki chat ID raqamini (masalan <code>-1001234567890</code>) yuboring.",
        reply_markup=kb.back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AddChannelStates.waiting_for_chat_id)
async def add_channel_handler(message: Message, bot: Bot, state: FSMContext):
    if not await _is_admin_guard(message.from_user.id):
        return

    chat_id_input = message.text.strip()
    await state.clear()

    try:
        chat = await bot.get_chat(chat_id_input)
    except Exception as e:
        await message.answer(
            f"❌ Chatni topib bo'lmadi. Bot o'sha kanal/guruhga admin qilib qo'shilganiga "
            f"ishonch hosil qiling.\n\nXatolik: {e}",
            reply_markup=kb.back_to_admin_kb(),
        )
        return

    chat_type = "group" if chat.type in ("group", "supergroup") else "channel"
    invite_link = chat.invite_link

    added = await db.add_channel(
        chat_id=str(chat.id), title=chat.title or chat.full_name or chat_id_input,
        chat_type=chat_type, invite_link=invite_link,
    )

    if added:
        await message.answer(f"✅ \"{chat.title}\" muvaffaqiyatli qo'shildi.",
                              reply_markup=kb.back_to_admin_kb())
    else:
        await message.answer("ℹ️ Bu kanal/guruh allaqachon ro'yxatda mavjud.",
                              reply_markup=kb.back_to_admin_kb())


@router.callback_query(F.data == "adm:remove_channel")
async def ask_channel_to_remove(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    channels = await db.get_all_channels()
    if not channels:
        await callback.answer("Ro'yxat bo'sh.", show_alert=True)
        return

    await callback.message.edit_text("➖ O'chirmoqchi bo'lgan kanal/guruhni tanlang:",
                                      reply_markup=kb.channels_remove_kb(channels))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:del_channel:"))
async def remove_channel_handler(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    chat_id = callback.data.split(":", 2)[2]
    removed = await db.remove_channel(chat_id)

    if removed:
        await callback.answer("✅ O'chirildi.")
    else:
        await callback.answer("❌ Topilmadi.", show_alert=True)

    channels = await db.get_all_channels()
    if channels:
        await callback.message.edit_text("➖ O'chirmoqchi bo'lgan kanal/guruhni tanlang:",
                                          reply_markup=kb.channels_remove_kb(channels))
    else:
        await callback.message.edit_text("📣 <b>Majburiy kanallar:</b>\n\nRo'yxat bo'sh.",
                                          reply_markup=kb.channels_menu_kb())


@router.callback_query(F.data == "adm:list_channels")
async def list_channels(callback: CallbackQuery):
    if not await _is_admin_guard(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    channels = await db.get_all_channels()
    if not channels:
        text = "📣 <b>Majburiy kanallar</b>\n\nRo'yxat bo'sh."
    else:
        lines = ["📣 <b>Majburiy kanallar</b>\n"]
        for ch in channels:
            lines.append(f"• {ch['title']} (<code>{ch['chat_id']}</code>) — {ch['chat_type']}")
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=kb.channels_menu_kb())
    await callback.answer()


# ---------------------------------------------------------------------------
#  ADMINLARNI BOSHQARISH
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "adm:admins")
async def admins_menu(callback: CallbackQuery, state: FSMContext):
    if not db.is_super_admin(callback.from_user.id):
        await callback.answer("⛔️ Faqat bosh adminlar bu bo'limga kira oladi.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("👥 <b>Adminlarni boshqarish</b>",
                                      reply_markup=kb.admins_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "adm:add_admin")
async def ask_admin_to_add(callback: CallbackQuery, state: FSMContext):
    if not db.is_super_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.set_state(AddAdminStates.waiting_for_id)
    await callback.message.edit_text(
        "➕ Yangi adminning Telegram ID raqamini yuboring:",
        reply_markup=kb.back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AddAdminStates.waiting_for_id)
async def add_admin_handler(message: Message, bot: Bot, state: FSMContext):
    if not db.is_super_admin(message.from_user.id):
        return

    if not message.text or not message.text.strip().isdigit():
        await message.answer("❗️ Iltimos, faqat raqamlardan iborat ID yuboring.")
        return

    new_admin_id = int(message.text.strip())
    await state.clear()

    added = await db.add_admin(new_admin_id, added_by=message.from_user.id)
    if added:
        await message.answer(f"✅ <code>{new_admin_id}</code> admin sifatida qo'shildi.",
                              reply_markup=kb.back_to_admin_kb())
        try:
            await bot.send_message(new_admin_id, "🎉 Tabriklaymiz! Siz botga admin etib tayinlandingiz.")
        except Exception:
            pass
    else:
        await message.answer("ℹ️ Bu foydalanuvchi allaqachon admin.",
                              reply_markup=kb.back_to_admin_kb())


@router.callback_query(F.data == "adm:remove_admin")
async def ask_admin_to_remove(callback: CallbackQuery, state: FSMContext):
    if not db.is_super_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return
    await state.set_state(RemoveAdminStates.waiting_for_id)
    await callback.message.edit_text(
        "➖ O'chirmoqchi bo'lgan adminning Telegram ID raqamini yuboring:",
        reply_markup=kb.back_to_admin_kb(),
    )
    await callback.answer()


@router.message(RemoveAdminStates.waiting_for_id)
async def remove_admin_handler(message: Message, state: FSMContext):
    if not db.is_super_admin(message.from_user.id):
        return

    if not message.text or not message.text.strip().isdigit():
        await message.answer("❗️ Iltimos, faqat raqamlardan iborat ID yuboring.")
        return

    admin_id = int(message.text.strip())
    await state.clear()

    if admin_id in SUPER_ADMINS:
        await message.answer("⛔️ Bosh adminni o'chirib bo'lmaydi.",
                              reply_markup=kb.back_to_admin_kb())
        return

    removed = await db.remove_admin(admin_id)
    if removed:
        await message.answer(f"✅ <code>{admin_id}</code> adminlikdan olib tashlandi.",
                              reply_markup=kb.back_to_admin_kb())
    else:
        await message.answer("❌ Bu foydalanuvchi (bazadagi) adminlar ro'yxatida topilmadi.",
                              reply_markup=kb.back_to_admin_kb())


@router.callback_query(F.data == "adm:list_admins")
async def list_admins(callback: CallbackQuery):
    if not db.is_super_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q.", show_alert=True)
        return

    all_admins = await db.get_all_admins()
    lines = ["👥 <b>Adminlar ro'yxati</b>\n"]
    for admin_id in all_admins:
        tag = " (bosh admin)" if db.is_super_admin(admin_id) else ""
        lines.append(f"• <code>{admin_id}</code>{tag}")

    await callback.message.edit_text("\n".join(lines), reply_markup=kb.admins_menu_kb())
    await callback.answer()
