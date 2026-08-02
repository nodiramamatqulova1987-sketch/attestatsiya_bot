# config.py
"""
Bot konfiguratsiyasi.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- BOT TOKEN ---
# Avval .env fayldan o'qiydi, topilmasa quyidagi standart qiymatni ishlatadi.
BOT_TOKEN = os.getenv("BOT_TOKEN", "8970302684:AAH0wwJug0Bd4x5JQ0bvDZ2DeHOHVsx2CR0")

# --- BOSH (SUPER) ADMINLAR ---
# Bazadan o'chirib bo'lmaydigan asosiy adminlar ID lari.
SUPER_ADMINS = [
    8968539545,
]

# --- MAJBURIY OBUNA UCHUN BOSHLANG'ICH KANAL/GURUH ---
# Bot birinchi marta ishga tushganda shu kanal/guruh avtomatik ravishda
# majburiy obuna ro'yxatiga qo'shiladi. Keyinchalik admin panel orqali
# istalgancha kanal/guruh qo'shish yoki o'chirish mumkin.
DEFAULT_CHANNEL_ID = "-1004370130434"

# Ma'lumotlar bazasi fayli manzili
DB_PATH = "database.db"

# "Fanlar va Testlar" bo'limida bitta testda nechta savol berilishi
QUESTIONS_PER_TEST = 10

# "Haqiqiy Imtihon" uchun kamida nechta savol bo'lishi shart va nechta savol beriladi
MIN_QUESTIONS_FOR_EXAM = 5
EXAM_QUESTIONS_COUNT = 10

# Bot birinchi marta ishga tushganda bazaga yoziladigan standart fanlar ro'yxati
SUBJECTS = [
    "Matematika",
    "Fizika",
    "Ona tili va adabiyot",
    "Tarix",
    "Biologiya",
    "Kimyo",
    "Ingliz tili",
    "Informatika",
    "Geografiya",
]
