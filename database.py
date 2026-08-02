"""
SQLite (aiosqlite orqali async) bilan ishlash uchun barcha funksiyalar
shu faylda joylashgan.
"""

import datetime
import aiosqlite

from config import DB_PATH, SUBJECTS, SUPER_ADMINS, DEFAULT_CHANNEL_ID


# ---------------------------------------------------------------------------
#  BAZANI ISHGA TUSHIRISH
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Barcha jadvallarni yaratadi (agar mavjud bo'lmasa) va boshlang'ich
    ma'lumotlarni (fanlar, majburiy kanal) bazaga yozadi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id         INTEGER PRIMARY KEY,
                username        TEXT,
                full_name       TEXT,
                joined_at       TEXT NOT NULL,
                is_blocked      INTEGER NOT NULL DEFAULT 0,
                score           INTEGER NOT NULL DEFAULT 0,
                correct_count   INTEGER NOT NULL DEFAULT 0,
                wrong_count     INTEGER NOT NULL DEFAULT 0,
                total_answered  INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id     INTEGER PRIMARY KEY,
                added_by    INTEGER,
                added_at    TEXT NOT NULL
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id      TEXT UNIQUE NOT NULL,
                title        TEXT,
                chat_type    TEXT NOT NULL DEFAULT 'channel',
                invite_link  TEXT
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT UNIQUE NOT NULL
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id      INTEGER NOT NULL,
                question        TEXT NOT NULL,
                option_a        TEXT NOT NULL,
                option_b        TEXT NOT NULL,
                option_c        TEXT NOT NULL,
                option_d        TEXT NOT NULL,
                correct_option  TEXT NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS test_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                subject_id      INTEGER,
                test_type       TEXT NOT NULL DEFAULT 'practice',
                correct_count   INTEGER NOT NULL,
                total_count     INTEGER NOT NULL,
                date            TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS appeals (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                message_text    TEXT NOT NULL,
                date            TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'pending',
                admin_id        INTEGER,
                reply_text      TEXT,
                reply_date      TEXT
            )
            """
        )

        await db.commit()

        # Fanlarni bazaga yozib qo'yish (dastlabki to'ldirish)
        for subject_name in SUBJECTS:
            await db.execute(
                "INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject_name,)
            )

        # Standart majburiy obuna kanalini qo'shib qo'yish
        if DEFAULT_CHANNEL_ID:
            await db.execute(
                "INSERT OR IGNORE INTO channels (chat_id, title, chat_type) VALUES (?, ?, ?)",
                (str(DEFAULT_CHANNEL_ID), "Majburiy kanal", "channel"),
            )

        await db.commit()


# ---------------------------------------------------------------------------
#  FOYDALANUVCHILAR
# ---------------------------------------------------------------------------

async def add_user(user_id: int, username, full_name: str) -> bool:
    """Yangi foydalanuvchini bazaga qo'shadi. Agar allaqachon mavjud bo'lsa False qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                (username, full_name, user_id),
            )
            await db.commit()
            return False

        await db.execute(
            "INSERT INTO users (user_id, username, full_name, joined_at) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, datetime.datetime.now().isoformat()),
        )
        await db.commit()
        return True


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()


async def get_all_users(limit: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM users ORDER BY joined_at DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor = await db.execute(query)
        return await cursor.fetchall()


async def get_all_user_ids() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE is_blocked = 0")
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


async def get_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def set_user_blocked(user_id: int, blocked: bool = True) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked = ? WHERE user_id = ?", (int(blocked), user_id)
        )
        await db.commit()


async def update_user_score(user_id: int, correct: int, wrong: int) -> None:
    """Test tugagach foydalanuvchining ball va statistikasini yangilaydi.
    Har bir to'g'ri javob uchun 1 ball qo'shiladi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE users
            SET score = score + ?,
                correct_count = correct_count + ?,
                wrong_count = wrong_count + ?,
                total_answered = total_answered + ?
            WHERE user_id = ?
            """,
            (correct, correct, wrong, correct + wrong, user_id),
        )
        await db.commit()


async def reset_all_scores() -> int:
    """Barcha foydalanuvchilarning ball va statistikasini nolga tushiradi.
    Nechta foydalanuvchi yangilanganini qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE users
            SET score = 0, correct_count = 0, wrong_count = 0, total_answered = 0
            """
        )
        await db.commit()
        return cursor.rowcount


async def get_leaderboard(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE score > 0 ORDER BY score DESC, total_answered DESC LIMIT ?",
            (limit,),
        )
        return await cursor.fetchall()


async def get_user_rank(user_id: int) -> int:
    """Foydalanuvchining reytingdagi o'rnini (1 dan boshlab) qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        my_score = row[0] if row else 0

        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE score > ?", (my_score,)
        )
        higher = (await cursor.fetchone())[0]
        return higher + 1


# ---------------------------------------------------------------------------
#  ADMINLAR
# ---------------------------------------------------------------------------

async def add_admin(user_id: int, added_by: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
        if await cursor.fetchone():
            return False
        await db.execute(
            "INSERT INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (user_id, added_by, datetime.datetime.now().isoformat()),
        )
        await db.commit()
        return True


async def remove_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
        if not await cursor.fetchone():
            return False
        await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()
        return True


async def get_db_admins() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM admins")
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


async def get_all_admins() -> list:
    """SUPER_ADMINS (config) + bazadagi adminlar birlashtirilgan ro'yxati."""
    db_admins = await get_db_admins()
    return list(set(SUPER_ADMINS) | set(db_admins))


async def is_admin(user_id: int) -> bool:
    if user_id in SUPER_ADMINS:
        return True
    db_admins = await get_db_admins()
    return user_id in db_admins


def is_super_admin(user_id: int) -> bool:
    return user_id in SUPER_ADMINS


# ---------------------------------------------------------------------------
#  MAJBURIY OBUNA KANALLARI
# ---------------------------------------------------------------------------

async def add_channel(chat_id: str, title: str, chat_type: str = "channel",
                       invite_link=None) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM channels WHERE chat_id = ?", (chat_id,))
        if await cursor.fetchone():
            return False
        await db.execute(
            "INSERT INTO channels (chat_id, title, chat_type, invite_link) VALUES (?, ?, ?, ?)",
            (chat_id, title, chat_type, invite_link),
        )
        await db.commit()
        return True


async def remove_channel(chat_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM channels WHERE chat_id = ?", (chat_id,))
        if not await cursor.fetchone():
            return False
        await db.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
        await db.commit()
        return True


async def get_all_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM channels")
        return await cursor.fetchall()


# ---------------------------------------------------------------------------
#  FANLAR
# ---------------------------------------------------------------------------

async def add_subject(name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM subjects WHERE name = ?", (name,))
        if await cursor.fetchone():
            return False
        await db.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
        await db.commit()
        return True


async def remove_subject(subject_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM subjects WHERE id = ?", (subject_id,))
        if not await cursor.fetchone():
            return False
        await db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        await db.commit()
        return True


async def get_subjects():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM subjects ORDER BY id")
        return await cursor.fetchall()


async def get_subject_by_id(subject_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
        return await cursor.fetchone()


# ---------------------------------------------------------------------------
#  SAVOLLAR
# ---------------------------------------------------------------------------

async def add_question(subject_id: int, question: str, option_a: str, option_b: str,
                        option_c: str, option_d: str, correct_option: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO questions
               (subject_id, question, option_a, option_b, option_c, option_d, correct_option)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (subject_id, question, option_a, option_b, option_c, option_d, correct_option),
        )
        await db.commit()
        return cursor.lastrowid


async def get_questions_by_subject(subject_id: int, limit=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM questions WHERE subject_id = ? ORDER BY RANDOM()"
        params = [subject_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        cursor = await db.execute(query, params)
        return await cursor.fetchall()


async def get_random_questions_all_subjects(limit: int):
    """'Haqiqiy Imtihon' uchun barcha fanlardan aralash savollar tanlab beradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM questions ORDER BY RANDOM() LIMIT ?", (limit,)
        )
        return await cursor.fetchall()


async def get_questions_count(subject_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM questions WHERE subject_id = ?", (subject_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_total_questions_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM questions")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def delete_question(question_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
        if not await cursor.fetchone():
            return False
        await db.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        await db.commit()
        return True


# ---------------------------------------------------------------------------
#  TEST NATIJALARI
# ---------------------------------------------------------------------------

async def save_test_result(user_id: int, subject_id, correct_count: int,
                            total_count: int, test_type: str = "practice") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO test_results
               (user_id, subject_id, test_type, correct_count, total_count, date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, subject_id, test_type, correct_count, total_count,
             datetime.datetime.now().isoformat()),
        )
        await db.commit()
    await update_user_score(user_id, correct_count, total_count - correct_count)


async def get_user_results(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT tr.*, s.name AS subject_name
               FROM test_results tr
               LEFT JOIN subjects s ON tr.subject_id = s.id
               WHERE tr.user_id = ?
               ORDER BY tr.date DESC""",
            (user_id,),
        )
        return await cursor.fetchall()


async def get_total_tests_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM test_results")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_stats_since(iso_date: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE joined_at >= ?", (iso_date,)
        )
        new_users = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM test_results WHERE date >= ?", (iso_date,)
        )
        tests_taken = (await cursor.fetchone())[0]

        return {"new_users": new_users, "tests_taken": tests_taken}


# ---------------------------------------------------------------------------
#  MUROJAATLAR (Adminga murojaat va javob tizimi)
# ---------------------------------------------------------------------------

async def add_appeal(user_id: int, message_text: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO appeals (user_id, message_text, date, status) VALUES (?, ?, ?, ?)",
            (user_id, message_text, datetime.datetime.now().isoformat(), "pending"),
        )
        await db.commit()
        return cursor.lastrowid


async def get_appeal(appeal_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM appeals WHERE id = ?", (appeal_id,))
        return await cursor.fetchone()


async def answer_appeal(appeal_id: int, admin_id: int, reply_text: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE appeals
               SET status = 'answered', admin_id = ?, reply_text = ?, reply_date = ?
               WHERE id = ?""",
            (admin_id, reply_text, datetime.datetime.now().isoformat(), appeal_id),
        )
        await db.commit()


async def get_pending_appeals():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM appeals WHERE status = 'pending' ORDER BY date DESC"
        )
        return await cursor.fetchall()


async def get_pending_appeals_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM appeals WHERE status = 'pending'")
        row = await cursor.fetchone()
        return row[0] if row else 0
