# seed_questions.py
"""
Botni birinchi marta ishga tushirgandan so'ng har bir fan bo'yicha
bir nechta namuna savol qo'shish uchun skript.

Ishlatish:
    python seed_questions.py

Bu skript faqat DEMO uchun. Admin panel orqali ("Savol qo'shish" bo'limi)
istalgan qadar yangi savol qo'shishingiz mumkin. Fanlarni ko'proq savollar
bilan to'ldirish uchun ushbu fayldagi SAMPLE_QUESTIONS ro'yxatiga
o'z savollaringizni qo'shishingiz ham mumkin.
"""

import asyncio
import database as db

# Format: (fan_nomi, savol, A, B, C, D, to'g'ri_javob)
SAMPLE_QUESTIONS = [
    # ---------------- MATEMATIKA ----------------
    ("Matematika", "2x + 5 = 15 tenglamada x nimaga teng?", "5", "10", "3", "7", "A"),
    ("Matematika", "To'g'ri to'rtburchakning yuzi qanday topiladi?", "a+b", "a*b", "2(a+b)", "a/b", "B"),
    ("Matematika", "5! (5 faktorial) nechaga teng?", "20", "60", "120", "100", "C"),
    ("Matematika", "Pifagor teoremasida gipotenuza qanday belgilanadi?", "a", "b", "c", "h", "C"),
    ("Matematika", "log(100) (o'nlik logarifm) nechaga teng?", "1", "2", "10", "100", "B"),

    # ---------------- FIZIKA ----------------
    ("Fizika", "Nyutonning ikkinchi qonuni formulasi qaysi?", "F=ma", "E=mc²", "P=mv", "F=qE", "A"),
    ("Fizika", "Suvning qaynash harorati (normal bosimda) necha darajа?", "0°C", "50°C", "100°C", "150°C", "C"),
    ("Fizika", "Yorug'lik tezligi vakuumda taxminan necha km/s?", "150 000", "300 000", "3 000", "30 000", "B"),
    ("Fizika", "Kuch birligi SI tizimida qanday nomlanadi?", "Joul", "Vatt", "Nyuton", "Paskal", "C"),
    ("Fizika", "Elektr toki birligi qaysi?", "Volt", "Amper", "Om", "Vatt", "B"),

    # ---------------- ONA TILI VA ADABIYOT ----------------
    ("Ona tili va adabiyot", "\"Alisher Navoiy\" taxallusi qaysi shoirga tegishli?", "Nizomiy Ganjaviy", "Mir Alisher", "Zahiriddin Bobur", "Muqimiy", "B"),
    ("Ona tili va adabiyot", "Ot, sifat, son, olmosh — bularning umumiy nomi nima?", "Yordamchi so'z turkumi", "Mustaqil so'z turkumi", "Undov", "Bog'lovchi", "B"),
    ("Ona tili va adabiyot", "\"Xamsa\" asarining muallifi kim?", "Alisher Navoiy", "Bobur", "Furqat", "Ogahiy", "A"),
    ("Ona tili va adabiyot", "Gapning bosh bo'laklari nechta?", "1", "2", "3", "4", "B"),
    ("Ona tili va adabiyot", "\"Boburnoma\" asari qaysi janrga mansub?", "She'riy", "Nasriy-tarixiy", "Dramatik", "Afsona", "B"),

    # ---------------- TARIX ----------------
    ("Tarix", "Amir Temur qachon tug'ilgan?", "1336-yil", "1370-yil", "1405-yil", "1290-yil", "A"),
    ("Tarix", "O'zbekiston qachon mustaqillikka erishdi?", "1989-yil", "1990-yil", "1991-yil", "1992-yil", "C"),
    ("Tarix", "Sohibqiron laqabi kimga berilgan?", "Ulug'bek", "Amir Temur", "Bobur", "Shayboniyxon", "B"),
    ("Tarix", "Mirzo Ulug'bek nima bilan mashhur bo'lgan?", "Harbiy yurishlari", "Astronomiya va fanlar", "Savdo ishlari", "Diniy va'zlar", "B"),
    ("Tarix", "Ipak yo'li nimani anglatadi?", "Harbiy yo'l", "Savdo yo'li", "Diniy marosim", "Bayram nomi", "B"),

    # ---------------- BIOLOGIYA ----------------
    ("Biologiya", "Odam yurak nechta kamerdan iborat?", "2", "3", "4", "5", "C"),
    ("Biologiya", "Fotosintez jarayoni qayerda sodir bo'ladi?", "Ildizda", "Barglarda", "Poyada", "Gulda", "B"),
    ("Biologiya", "DNK nimaning qisqartmasi?", "Dezoksiribonuklein kislota", "Ribonuklein kislota", "Aminokislota", "Fermentativ kislota", "A"),
    ("Biologiya", "Inson tanasidagi eng katta organ qaysi?", "Jigar", "Teri", "O'pka", "Miya", "B"),
    ("Biologiya", "Hujayraning \"energiya stansiyasi\" deb ataluvchi organoidi?", "Yadro", "Mitoxondriya", "Ribosoma", "Golji apparati", "B"),

    # ---------------- KIMYO ----------------
    ("Kimyo", "Suvning kimyoviy formulasi qanday?", "CO2", "H2O", "O2", "NaCl", "B"),
    ("Kimyo", "Davriy sistemada eng birinchi element qaysi?", "Geliy", "Kislorod", "Vodorod", "Uglerod", "C"),
    ("Kimyo", "Osh tuzining kimyoviy formulasi?", "NaCl", "KCl", "CaCl2", "NaOH", "A"),
    ("Kimyo", "pH shkalasi nimani ko'rsatadi?", "Haroratni", "Muhitning kislotaliligini", "Zichlikni", "Bosimni", "B"),
    ("Kimyo", "Kislorodning kimyoviy belgisi qanday?", "O", "Ox", "K", "Q", "A"),

    # ---------------- INGLIZ TILI ----------------
    ("Ingliz tili", "Choose the correct form: 'She ___ to school every day.'", "go", "goes", "going", "gone", "B"),
    ("Ingliz tili", "What is the past tense of 'go'?", "goed", "gone", "went", "going", "C"),
    ("Ingliz tili", "'Book' so'zining o'zbekcha tarjimasi?", "Qalam", "Kitob", "Stol", "Deraza", "B"),
    ("Ingliz tili", "Choose the correct article: '___ apple a day keeps the doctor away.'", "A", "An", "The", "-", "B"),
    ("Ingliz tili", "What is the plural form of 'child'?", "childs", "childes", "children", "child's", "C"),

    # ---------------- INFORMATIKA ----------------
    ("Informatika", "CPU nimaning qisqartmasi?", "Central Processing Unit", "Computer Personal Unit", "Central Program Utility", "Core Process Unit", "A"),
    ("Informatika", "1 bayt nechta bitdan iborat?", "4", "8", "16", "32", "B"),
    ("Informatika", "HTML nima uchun ishlatiladi?", "Dasturlash tili", "Veb-sahifa tuzish tili", "Operatsion tizim", "Ma'lumotlar bazasi", "B"),
    ("Informatika", "RAM nimaning qisqartmasi?", "Random Access Memory", "Read Access Memory", "Run Active Memory", "Real Access Module", "A"),
    ("Informatika", "Python qanday til turi hisoblanadi?", "Belgilash tili", "Dasturlash tili", "So'rovlar tili", "Stil tili", "B"),

    # ---------------- GEOGRAFIYA ----------------
    ("Geografiya", "Dunyodagi eng katta okean qaysi?", "Atlantika", "Hind okeani", "Tinch okean", "Shimoliy Muz okeani", "C"),
    ("Geografiya", "O'zbekistonning poytaxti qaysi shahar?", "Samarqand", "Buxoro", "Toshkent", "Andijon", "C"),
    ("Geografiya", "Dunyodagi eng baland tog' cho'qqisi?", "Elbrus", "Everest", "Kilimanjaro", "Mont Blan", "B"),
    ("Geografiya", "Orol dengizi qaysi davlatlar chegarasida joylashgan?", "O'zbekiston-Qozog'iston", "Rossiya-Xitoy", "Eron-Turkiya", "Hindiston-Pokiston", "A"),
    ("Geografiya", "Yer sharida nechta materik bor?", "5", "6", "7", "8", "C"),
]


async def main():
    await db.init_db()
    subjects = await db.get_subjects()
    name_to_id = {s["name"]: s["id"] for s in subjects}

    added, skipped = 0, 0
    for subject_name, question, a, b, c, d, correct in SAMPLE_QUESTIONS:
        subject_id = name_to_id.get(subject_name)
        if subject_id is None:
            print(f"⚠️  Fan topilmadi: {subject_name} — o'tkazib yuborildi")
            skipped += 1
            continue
        await db.add_question(subject_id, question, a, b, c, d, correct)
        added += 1

    print(f"\n✅ Jami {added} ta savol bazaga qo'shildi ({skipped} tasi o'tkazib yuborildi).")
    print("Admin panel orqali ('➕ Savol qo'shish') istalgancha yangi savol qo'shishingiz mumkin.")


if __name__ == "__main__":
    asyncio.run(main())
