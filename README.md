# UstozBox — Attestatsiya Bot

O'qituvchilar va foydalanuvchilar uchun attestatsiya imtihonlariga tayyorgarlik
ko'rish Telegram boti. Aiogram 3.x + SQLite (aiosqlite) asosida yozilgan.

## ✅ Sizning ma'lumotlaringiz allaqachon `config.py` ga kiritilgan

| Parametr | Qiymat |
|---|---|
| Bot tokeni | `.env` faylida saqlangan |
| Bosh admin ID | `8968539545` |
| Majburiy kanal/guruh ID | `-1004370130434` |

Botni ishga tushirishdan oldin faqat 1 ta shart bor: **botni admin ID
raqamiga tegishli akkauntdan `-1004370130434` kanal/guruhga administrator
qilib qo'shing**, aks holda majburiy obuna ishlamaydi.

## Imkoniyatlar

- **📚 Fanlar va Testlar** — fan tanlab, o'sha fan bo'yicha mashq testi ishlash
- **🎓 Haqiqiy Imtihon** — barcha fanlardan aralashtirilgan savollar bilan haqiqiy
  imtihon simulyatsiyasi (bazada kamida 5 ta savol bo'lishi shart)
- **🏆 Reyting** — barcha foydalanuvchilar orasida TOP-10 reyting jadvali
- **📊 Mening natijalarim** — shaxsiy ball, o'rin, to'g'ri/noto'g'ri javoblar statistikasi
- **✉️ Adminga murojaat** — foydalanuvchi to'g'ridan-to'g'ri adminga murojaat yozadi,
  admin bot orqali unga javob qaytaradi
- **Majburiy obuna tizimi** — kanal/guruhlarni admin panel orqali qo'shish/o'chirish
- **To'liq admin panel:**
  - 📚 Fanlarni boshqarish (qo'shish/o'chirish/ro'yxat)
  - ❓ Savollarni boshqarish (qo'shish/o'chirish/soni)
  - 👥 Adminlarni boshqarish (faqat bosh adminlar uchun)
  - 📣 Kanallarni boshqarish (majburiy obuna)
  - 📊 Umumiy va vaqt bo'yicha (kunlik/haftalik/oylik) statistika
  - 👤 Foydalanuvchilar ro'yxati va har biri bo'yicha alohida statistika
  - 📢 Ommaviy xabar yuborish — rassilka (matn, rasm, video — istalgan turdagi xabar)
  - 📩 Murojaatlarni ko'rish va javob berish
  - 🔄 Barcha foydalanuvchilar ballarini bir zumda 0 ga tushirish

## Loyihaning tuzilishi

```
attestatsiya_bot/
├── main.py                # Botni ishga tushiruvchi asosiy fayl
├── config.py               # Sozlamalar (token, super adminlar, kanal, fanlar)
├── database.py              # SQLite bilan ishlovchi barcha funksiyalar
├── keyboards.py             # Barcha klaviaturalar
├── states.py                # FSM holatlari
├── subscription.py          # Majburiy obunani tekshirish
├── handlers/
│   ├── user.py                # Foydalanuvchi funksiyalari (test, reyting, murojaat)
│   └── admin.py               # Admin panel funksiyalari
├── seed_questions.py         # (ixtiyoriy) namuna test savollarini bazaga qo'shadi
├── requirements.txt
├── .env                      # Bot tokeni shu yerda (allaqachon to'ldirilgan)
├── .env.example
└── database.db               # (avtomatik yaratiladi, birinchi ishga tushganda)
```

---

## TERMUXDA ISHGA TUSHIRISH (bosqichma-bosqich)

Quyidagi buyruqlarni Termux ilovasida ketma-ket, birma-bir kiriting.

### 1-qadam. Termuxni yangilash

```bash
pkg update -y && pkg upgrade -y
```

### 2-qadam. Python va git o'rnatish

```bash
pkg install python -y
pkg install git -y
```

O'rnatilganini tekshiring:

```bash
python --version
```

(Python 3.11 yoki undan yuqori versiya bo'lishi kerak)

### 3-qadam. Loyiha fayllarini Termux xotirasiga joylash

Fayllarni telefoningizga (masalan, `Yuklab olingan fayllar` papkasiga) yuklab
olgan bo'lsangiz, avval Termuxga telefon xotirasiga kirish huquqini bering:

```bash
termux-setup-storage
```

(so'ralganda "Ruxsat berish" tugmasini bosing)

So'ngra loyiha papkasini Termux ichiga ko'chiring:

```bash
cp -r /sdcard/Download/attestatsiya_bot ~/attestatsiya_bot
cd ~/attestatsiya_bot
```

### 4-qadam. Virtual muhit yaratish (tavsiya etiladi)

```bash
python -m venv venv
source venv/bin/activate
```

*(Har safar Termuxni yopib qayta ochganingizda, botni ishga tushirishdan oldin
`source venv/bin/activate` buyrug'ini qayta kiritishingiz kerak bo'ladi)*

### 5-qadam. Kerakli kutubxonalarni o'rnatish

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6-qadam. Bot tokeni va admin ID — TEKSHIRISH (odatda ishlagan holda keladi)

`.env` fayl allaqachon to'ldirilgan holda keladi. Tekshirib ko'ring:

```bash
cat .env
```

Agar boshqa token bilan almashtirmoqchi bo'lsangiz:

```bash
nano .env
```

`Ctrl+O` (saqlash), `Enter`, `Ctrl+X` (chiqish).

Yangi bosh admin qo'shmoqchi bo'lsangiz `config.py` dagi `SUPER_ADMINS`
ro'yxatiga qo'shishingiz mumkin (yoki botdan turib "👥 Adminlarni boshqarish"
orqali oddiy admin qo'shsangiz ham bo'ladi):

```bash
nano config.py
```

### 7-qadam. Botni albatta kanal/guruhga admin qilib qo'shing

`-1004370130434` ID li kanal yoki guruhga botni **administrator** huquqi bilan
qo'shing. Aks holda majburiy obuna tekshiruvi ishlamaydi va foydalanuvchilar
botdan foydalana olmaydi.

### 8-qadam (ixtiyoriy). Namuna test savollarini bazaga qo'shish

Baza dastlab bo'sh bo'ladi (faqat fanlar ro'yxati tayyor, savollar yo'q).
Har bir fan bo'yicha bir nechta tayyor namuna savol qo'shib qo'yish uchun:

```bash
python seed_questions.py
```

Bu — faqat boshlang'ich namuna (jami 50 ta savol, 10 ta fan bo'yicha). Qolgan
savollarni "⚙️ Admin panel → ❓ Savollarni boshqarish → ➕ Savol qo'shish"
bo'limi orqali istalgancha qo'shib borishingiz mumkin.

### 9-qadam. Botni ishga tushirish

```bash
python main.py
```

Terminalda quyidagiga o'xshash xabar chiqsa — bot ishga tushgan bo'ladi:

```
Ma'lumotlar bazasi tayyor.
Bot ishga tushmoqda...
```

Endi Telegram'da botingizga o'ting va `/start` bosing.

### 10-qadam. Botni doimiy (fonda) ishlab turishi uchun

Termux yopilganda yoki telefon uxlab qolganda bot to'xtab qolmasligi uchun:

**a) Termux ilovasini uxlab qolishdan saqlash:**

```bash
termux-wake-lock
```

**b) `tmux` yordamida fonda ishlatish** (tavsiya etiladi):

```bash
pkg install tmux -y
tmux new -s bot
source venv/bin/activate
python main.py
```

Endi `Ctrl+B`, so'ngra `D` tugmalarini bosib sessiyadan chiqsangiz ham, bot
fonda ishlashda davom etadi. Qayta ulanish uchun:

```bash
tmux attach -s bot
```

Botni to'xtatish uchun `tmux attach -s bot` bilan sessiyaga kirib, `Ctrl+C` bosing.

---

## Admin panel qanday ishlaydi

Botda `/start` bosgach, agar sizning ID raqamingiz `SUPER_ADMINS` ro'yxatida
bo'lsa, pastki menyuda **⚙️ Admin panel** tugmasi chiqadi. Uni bosganingizda:

- **📚 Fanlarni boshqarish** — yangi fan qo'shish, mavjudini o'chirish, ro'yxatni ko'rish
- **❓ Savollarni boshqarish** — fan tanlab savol qo'shish (savol matni, 4 variant,
  to'g'ri javob harfi ketma-ket so'raladi), ID orqali savol o'chirish, savollar sonini ko'rish
- **👥 Adminlarni boshqarish** — yangi admin ID qo'shish/o'chirish (faqat bosh adminlar
  uchun ochiq)
- **📣 Kanallarni boshqarish** — majburiy obuna kanal/guruh qo'shish (username yoki
  chat ID orqali) va o'chirish
- **📊 Statistika** — umumiy sonlar + kunlik/haftalik/oylik dinamika bitta ekranda
- **👤 Foydalanuvchilar** — oxirgi qo'shilgan foydalanuvchilar ro'yxati va istalgan
  foydalanuvchining ID sini yuborib, uning to'liq statistikasini (ball, o'rin,
  to'g'ri/noto'g'ri javoblar, so'nggi natijalari) ko'rish
- **📢 Xabar yuborish** — istalgan matn/rasm/video xabarni barcha foydalanuvchilarga
  bir zumda yuborish (tasdiqlash bilan)
- **📩 Murojaatlar** — foydalanuvchilardan kelgan javobsiz murojaatlar ro'yxati,
  har biriga bosib to'g'ridan-to'g'ri javob yozish (javob avtomatik foydalanuvchiga yetadi)
- **🔄 Ballarni nollash** — barcha foydalanuvchilarning ball/reytingini bitta tugma
  bilan 0 ga tushirish (tasdiqlash so'raladi, chunki bu amalni ortga qaytarib bo'lmaydi)

## Ball va reyting tizimi qanday ishlaydi

- Har bir to'g'ri javob uchun foydalanuvchiga **+1 ball** yoziladi (ikkala rejimda ham:
  "Fanlar va Testlar" va "Haqiqiy Imtihon")
- **🏆 Reyting** bo'limi ballar bo'yicha eng yuqori 10 ta foydalanuvchini va sizning
  o'z o'rningizni ko'rsatadi
- **📊 Mening natijalarim** — shaxsiy ball, o'rin, jami ishlangan/to'g'ri/noto'g'ri
  javoblar va o'rtacha aniqlik foizini ko'rsatadi

## Muhim eslatmalar

- Botni birinchi marta ishga tushirganingizda `database.db` fayli avtomatik
  yaratiladi — bu SQLite ma'lumotlar bazasi bo'lib, barcha foydalanuvchilar,
  testlar, savollar shu faylda saqlanadi. Uni tasodifan o'chirmang.
- **Xavfsizlik:** bot tokeningizni hech kimga ulashmang — token orqali
  istalgan kishi botingizni to'liq boshqarishi mumkin. Agar token boshqa
  birov qo'liga tushgan bo'lsa, @BotFather ga `/revoke` buyrug'ini yuborib
  yangi token oling va uni `.env` faylga yozing.
- Test savollarini "Admin panel → ❓ Savollarni boshqarish → ➕ Savol qo'shish"
  bo'limi orqali qo'shib boring.
- Botni to'xtatish uchun terminalda `Ctrl+C` bosing.
