import logging

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import database as db
import keyboards as kb
from config import QUESTIONS_PER_TEST, MIN_QUESTIONS_FOR_EXAM, EXAM_QUESTIONS_COUNT
from states import TestStates, AppealStates, AdminReplyStates
from subscription import get_not_subscribed_channels

router = Router()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  YORDAMCHI FUNKSIYA: obunani tekshirib, kerak bo'lsa xabar chiqarish
# ---------------------------------------------------------------------------

async def ensure_subscribed(message: Message, bot: Bot) -> bool:
    not_subscribed = await get_not_subscribed_channels(bot, message.from_user.id)
    if not_subscribed:
        await message.answer(
            "❗️ Botdan foydalanish uchun quyidagi kanal/guruhlarga a'zo bo'ling, "
            "so'ngra <b>✅ Tekshirish</b> tugmasini bosing:",
            reply_markup=kb.subscription_kb(not_subscribed),
        )
        return False
    return True


def _display_name(row) -> str:
    if row["username"]:
        return row["username"]
    return row["full_name"] or f"ID {row['user_id']}"


# ---------------------------------------------------------------------------
#  /start
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
    await state.clear()

    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    if not await ensure_subscribed(message, bot):
        return

    is_admin = await db.is_admin(message.from_user.id)
    await message.answer(
        "👋 Assalomu alaykum, <b>{}</b>!\n"
        "UstozBox botiga xush kelibsiz.\n\n"
        "Ushbu bot orqali attestatsiya imtihonlariga tayyorgarlik ko'rishingiz mumkin.\n"
        "Quyidagi menyudan kerakli bo'limni tanlang 👇".format(message.from_user.full_name),
        reply_markup=kb.main_menu_kb(is_admin=is_admin),
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot):
    not_subscribed = await get_not_subscribed_channels(bot, callback.from_user.id)
    if not_subscribed:
        await callback.answer(
            "❌ Siz hali barcha kanal/guruhlarga a'zo bo'lmadingiz!", show_alert=True
        )
        return

    is_admin = await db.is_admin(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer(
        "✅ Rahmat! Endi botdan to'liq foydalanishingiz mumkin.",
        reply_markup=kb.main_menu_kb(is_admin=is_admin),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
#  FAN TANLASH VA TEST BOSHLASH ("📚 Fanlar va Testlar")
# ---------------------------------------------------------------------------

@router.message(F.text == "📚 Fanlar va Testlar")
async def choose_subject(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    subjects = await db.get_subjects()
    if not subjects:
        await message.answer("Hozircha fanlar mavjud emas.")
        return
    await message.answer("Quyidagi fanlardan birini tanlang:", reply_markup=kb.subjects_kb(subjects))


@router.callback_query(F.data.startswith("subject:"))
async def start_subject_test(callback: CallbackQuery, state: FSMContext):
    subject_id = int(callback.data.split(":")[1])
    subject = await db.get_subject_by_id(subject_id)
    if not subject:
        await callback.answer("Fan topilmadi.", show_alert=True)
        return

    questions = await db.get_questions_by_subject(subject_id, limit=QUESTIONS_PER_TEST)
    if not questions:
        await callback.answer("Bu fan bo'yicha hozircha savollar mavjud emas.", show_alert=True)
        return

    await _start_test(callback.message, state, questions, subject_name=subject["name"],
                       subject_id=subject_id, test_type="practice")
    await callback.answer()


# ---------------------------------------------------------------------------
#  HAQIQIY IMTIHON
# ---------------------------------------------------------------------------

@router.message(F.text == "🎓 Haqiqiy Imtihon")
async def start_real_exam(message: Message, bot: Bot, state: FSMContext):
    if not await ensure_subscribed(message, bot):
        return

    total_questions = await db.get_total_questions_count()
    if total_questions < MIN_QUESTIONS_FOR_EXAM:
        await message.answer(
            f"❌ Imtihon boshlash uchun bazada yetarli savollar yo'q "
            f"(kamida {MIN_QUESTIONS_FOR_EXAM} ta bo'lishi kerak)."
        )
        return

    limit = min(EXAM_QUESTIONS_COUNT, total_questions)
    questions = await db.get_random_questions_all_subjects(limit)

    await _start_test(message, state, questions, subject_name="Haqiqiy Imtihon (aralash)",
                       subject_id=None, test_type="exam")


# ---------------------------------------------------------------------------
#  TEST OQIMI (umumiy)
# ---------------------------------------------------------------------------

async def _start_test(message: Message, state: FSMContext, questions, subject_name: str,
                       subject_id, test_type: str):
    questions_data = [
        {
            "question": q["question"],
            "options": {
                "A": q["option_a"],
                "B": q["option_b"],
                "C": q["option_c"],
                "D": q["option_d"],
            },
            "correct": q["correct_option"].strip().upper(),
        }
        for q in questions
    ]

    await state.set_state(TestStates.in_progress)
    await state.update_data(
        subject_id=subject_id,
        subject_name=subject_name,
        test_type=test_type,
        questions=questions_data,
        current_index=0,
        correct_count=0,
    )

    icon = "🎓" if test_type == "exam" else "📝"
    await message.answer(
        f"{icon} <b>{subject_name}</b> boshlandi!\n"
        f"Jami savollar: <b>{len(questions_data)}</b> ta\n"
        f"Har bir to'g'ri javob uchun 1 ball beriladi.\n\nOmad!"
    )
    await send_question(message, state)


async def send_question(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    index = data["current_index"]

    if index >= len(questions):
        await finish_test(message, state)
        return

    q = questions[index]
    text = f"❓ <b>{index + 1}-savol:</b>\n\n{q['question']}"
    await message.answer(text, reply_markup=kb.test_question_kb(index, q["options"]))


@router.callback_query(TestStates.in_progress, F.data.startswith("answer:"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    _, index_str, chosen_letter = callback.data.split(":")
    index = int(index_str)

    data = await state.get_data()
    questions = data["questions"]
    current_index = data["current_index"]

    if index != current_index:
        await callback.answer("Bu savol allaqachon javob berilgan.", show_alert=True)
        return

    correct_letter = questions[index]["correct"]
    correct_count = data["correct_count"]

    if chosen_letter == correct_letter:
        correct_count += 1
        await callback.answer("✅ To'g'ri javob! (+1 ball)")
    else:
        correct_option_text = questions[index]["options"].get(correct_letter, "")
        await callback.answer(
            f"❌ Noto'g'ri. To'g'ri javob: {correct_letter}) {correct_option_text}",
            show_alert=True,
        )

    await callback.message.edit_reply_markup(reply_markup=None)

    await state.update_data(current_index=current_index + 1, correct_count=correct_count)
    await send_question(callback.message, state)


async def finish_test(message: Message, state: FSMContext):
    data = await state.get_data()
    subject_id = data["subject_id"]
    subject_name = data["subject_name"]
    test_type = data["test_type"]
    correct_count = data["correct_count"]
    total = len(data["questions"])
    wrong_count = total - correct_count

    await db.save_test_result(message.chat.id, subject_id, correct_count, total, test_type)

    rank = await db.get_user_rank(message.chat.id)
    percent = round((correct_count / total) * 100) if total else 0

    icon = "🎓" if test_type == "exam" else "🏁"
    await message.answer(
        f"{icon} <b>Test yakunlandi!</b>\n\n"
        f"📘 Mavzu: <b>{subject_name}</b>\n"
        f"✅ To'g'ri javoblar: <b>{correct_count}/{total}</b>\n"
        f"❌ Noto'g'ri javoblar: <b>{wrong_count}</b>\n"
        f"⭐ Olingan ball: <b>+{correct_count}</b>\n"
        f"📊 Natija: <b>{percent}%</b>\n"
        f"🏆 Umumiy reytingdagi o'rningiz: <b>{rank}</b>\n\n"
        f"Yana test ishlash uchun menyudan tanlang."
    )
    await state.clear()


# ---------------------------------------------------------------------------
#  REYTING
# ---------------------------------------------------------------------------

@router.message(F.text == "🏆 Reyting")
async def show_leaderboard(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return

    leaders = await db.get_leaderboard(limit=10)
    my_rank = await db.get_user_rank(message.from_user.id)
    my_user = await db.get_user(message.from_user.id)
    my_score = my_user["score"] if my_user else 0

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Top 10 Reyting:</b>\n"]

    if not leaders:
        lines.append("Hozircha hech kim ball to'plamagan.")
    else:
        for i, u in enumerate(leaders):
            medal = medals[i] if i < 3 else f"{i + 1}."
            lines.append(f"{medal} {_display_name(u)} — {u['score']} ball")

    lines.append("-------------------")
    lines.append(f"👤 Sizning o'rningiz: {my_rank}-o'rin ({my_score} ball)")

    await message.answer("\n".join(lines))


# ---------------------------------------------------------------------------
#  MENING NATIJALARIM
# ---------------------------------------------------------------------------

@router.message(F.text == "📊 Mening natijalarim")
async def my_results(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return

    user = await db.get_user(message.from_user.id)
    rank = await db.get_user_rank(message.from_user.id)

    correct = user["correct_count"] if user else 0
    wrong = user["wrong_count"] if user else 0
    total_answered = user["total_answered"] if user else 0
    score = user["score"] if user else 0
    accuracy = round((correct / total_answered) * 100, 1) if total_answered else 0.0

    await message.answer(
        "📊 <b>Sizning statistikangiz:</b>\n\n"
        f"🏆 O'rin: <b>{rank}</b>\n"
        f"⭐ Ball: <b>{score}</b>\n"
        f"📝 Jami ishlangan: <b>{total_answered}</b>\n"
        f"✅ To'g'ri: <b>{correct}</b>\n"
        f"❌ Noto'g'ri: <b>{wrong}</b>\n"
        f"📈 O'rtacha aniqlik: <b>{accuracy}%</b>"
    )


# ---------------------------------------------------------------------------
#  ADMINGA MUROJAAT
# ---------------------------------------------------------------------------

@router.message(F.text == "✉️ Adminga murojaat")
async def start_appeal(message: Message, bot: Bot, state: FSMContext):
    if not await ensure_subscribed(message, bot):
        return
    await state.set_state(AppealStates.waiting_for_text)
    await message.answer(
        "✍️ Murojaatingizni matn ko'rinishida yozib yuboring.\n"
        "Bekor qilish uchun quyidagi tugmani bosing.",
        reply_markup=kb.cancel_kb(),
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_any_state(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    is_admin = await db.is_admin(message.from_user.id)
    await message.answer("Bekor qilindi.", reply_markup=kb.main_menu_kb(is_admin=is_admin))


@router.message(AppealStates.waiting_for_text)
async def receive_appeal(message: Message, bot: Bot, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, murojaatingizni matn ko'rinishida yuboring.")
        return

    appeal_id = await db.add_appeal(message.from_user.id, message.text)
    await state.clear()

    is_admin = await db.is_admin(message.from_user.id)
    await message.answer(
        "✅ Murojaatingiz qabul qilindi. Tez orada admin javob beradi.",
        reply_markup=kb.main_menu_kb(is_admin=is_admin),
    )

    admins = await db.get_all_admins()
    username_part = f"@{message.from_user.username}" if message.from_user.username else "—"
    text_for_admin = (
        f"📩 <b>Yangi murojaat</b> (ID: {appeal_id})\n\n"
        f"👤 Kimdan: {message.from_user.full_name} ({username_part})\n"
        f"🆔 User ID: <code>{message.from_user.id}</code>\n\n"
        f"💬 Matn:\n{message.text}"
    )
    for admin_id in admins:
        try:
            await bot.send_message(
                admin_id, text_for_admin, reply_markup=kb.appeal_answer_kb(appeal_id)
            )
        except Exception as e:
            logger.warning(f"Adminga ({admin_id}) murojaat yuborilmadi: {e}")


@router.callback_query(F.data.startswith("reply_appeal:"))
async def start_reply_appeal(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    appeal_id = int(callback.data.split(":")[1])
    appeal = await db.get_appeal(appeal_id)
    if not appeal:
        await callback.answer("Murojaat topilmadi.", show_alert=True)
        return

    await state.set_state(AdminReplyStates.waiting_for_reply)
    await state.update_data(appeal_id=appeal_id, appeal_user_id=appeal["user_id"])

    await callback.message.answer(
        f"✍️ #{appeal_id}-murojaatga javobingizni yozing:\n\n"
        f"<i>Murojaat matni:</i> {appeal['message_text']}",
        reply_markup=kb.cancel_kb(),
    )
    await callback.answer()


@router.message(AdminReplyStates.waiting_for_reply)
async def send_reply_to_user(message: Message, bot: Bot, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, javobni matn ko'rinishida yuboring.")
        return

    data = await state.get_data()
    appeal_id = data["appeal_id"]
    user_id = data["appeal_user_id"]

    await db.answer_appeal(appeal_id, message.from_user.id, message.text)
    await state.clear()

    is_admin = await db.is_admin(message.from_user.id)
    await message.answer("✅ Javobingiz foydalanuvchiga yuborildi.",
                          reply_markup=kb.main_menu_kb(is_admin=is_admin))

    try:
        await bot.send_message(
            user_id,
            f"📬 <b>Admindan javob keldi</b> (murojaat №{appeal_id}):\n\n{message.text}",
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga ({user_id}) javob yuborilmadi: {e}")
