import json
import random
import asyncio
import nest_asyncio  # Дозволяє вкладати event loop
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import logging

# Завантаження змінних середовища
load_dotenv()

# Отримання токена з .env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не встановлено у змінних середовища.")

# Застосування nest_asyncio
nest_asyncio.apply()

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Шлях до файлу JSON
DATA_FILE = "participants.json"

# Початкові дані з новими учасниками та кольорами
initial_data = {
    "participants": [
        {"name": "Віка",   "approved": False, "user_id": None, "assigned_to": None, "color": None},
        {"name": "Коля",   "approved": False, "user_id": None, "assigned_to": None, "color": None},
        {"name": "Дана",   "approved": False, "user_id": None, "assigned_to": None, "color": None},
        {"name": "Костя",  "approved": False, "user_id": None, "assigned_to": None, "color": None},
        {"name": "Люда",   "approved": False, "user_id": None, "assigned_to": None, "color": None},
        {"name": "Ярік",   "approved": False, "user_id": None, "assigned_to": None, "color": None},
        {"name": "Олена",  "approved": False, "user_id": None, "assigned_to": None, "color": None},
        {"name": "Даня",   "approved": False, "user_id": None, "assigned_to": None, "color": None},

        # Нові учасники
        {"name": "Славік", "approved": False, "user_id": None, "assigned_to": None, "color": None},
        {"name": "Настя",  "approved": False, "user_id": None, "assigned_to": None, "color": None}
    ],
    "colors": [
        "Чорний 🖤", "Червоний ❤️", "Синій 💙", "Рожевий 💖",
        "Жовтий 💛", "Зелений 💚", "Білий 🤍", "Фіолетовий 💜",

        # Нові кольори
        "Помаранчевий 🧡", "Коричневий 🤎"
    ]
}

# Ініціалізація JSON
try:
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
except FileNotFoundError:
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(initial_data, file, ensure_ascii=False, indent=4)
    data = initial_data

# Збереження JSON
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    logger.info("Дані збережено.")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    selected_participant = next((p for p in data["participants"] if p["user_id"] == user_id), None)

    if selected_participant:
        # Перевірка, чи користувач вже обрав ім'я
        assigned_to = selected_participant["assigned_to"]
        color = selected_participant["color"]
        if assigned_to and color:
            await update.message.reply_text(
                f"🎉 Ви вже обрали ім'я: {selected_participant['name']}.\n"
                f"Ваше завдання: дарувати подарунок для {assigned_to} з кольором {color} 🎁"
            )
            logger.info(f"Користувач {user_id} переглядає своє завдання.")
        else:
            await update.message.reply_text(
                f"🎉 Ви вже обрали ім'я: {selected_participant['name']}.\n"
                f"Ваше завдання ще не призначене."
            )
            logger.info(f"Користувач {user_id} обрав ім'я {selected_participant['name']} але завдання ще не призначене.")
    else:
        # Перевірка доступних імен (включаючи своє ім'я, якщо користувач не обирав)
        available_names = [
            p["name"] for p in data["participants"]
            if not p["approved"] or p.get("user_id") == user_id
        ]
        if not available_names:
            await update.message.reply_text("😢 На жаль, всі імена вже вибрані.")
            logger.info("Всі імена вже вибрані.")
            return
        keyboard = [[name] for name in available_names]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "🎅 Привіт! Обери своє ім'я зі списку, щоб отримати завдання Таємного Санти 🎁:",
            reply_markup=reply_markup
        )
        logger.info(f"Користувач {user_id} отримав список доступних імен.")

# Обробка імені учасника
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.message.text.strip()
    participant = next((p for p in data["participants"] if p["name"] == user_name and not p["approved"]), None)

    if participant:
        # Перевірка, чи користувач вже обрав ім'я
        existing_selection = next((p for p in data["participants"] if p["user_id"] == user_id), None)
        if existing_selection:
            await update.message.reply_text(
                f"⚠️ Ви вже обрали ім'я: {existing_selection['name']}. "
                f"Якщо ви хочете змінити вибір, будь ласка, зверніться до адміністратора."
            )
            logger.info(f"Користувач {user_id} спробував обрати додаткове ім'я {user_name}, але вже обрав {existing_selection['name']}.")
            return

        # Відправка підтвердження
        confirmation_text = f"Ви вибрали ім'я *{user_name}*. Підтвердіть вибір?"
        keyboard = [
            [
                InlineKeyboardButton("✅ Підтвердити", callback_data=f"confirm|{user_name}"),
                InlineKeyboardButton("❌ Скасувати", callback_data=f"cancel|{user_name}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info(f"Користувач {user_id} вибрав ім'я {user_name}, очікує підтвердження.")
    else:
        await update.message.reply_text("⚠️ Це ім'я вже вибрано або не знайдено. Спробуйте ще раз.")
        logger.warning(f"Користувач {user_id} спробував обрати ім'я {user_name}, яке вже вибране або не існує.")

# Обробка підтвердження (Inline кнопки)
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split('|')

    if len(data_parts) != 2:
        await query.edit_message_text("⚠️ Некоректні дані.")
        logger.error("Некоректні дані у callback_query.data")
        return

    action, name = data_parts
    user_id = query.from_user.id
    participant = next((p for p in data["participants"] if p["name"] == name), None)

    if not participant:
        await query.edit_message_text("⚠️ Ім'я не знайдено.")
        logger.warning(f"Ім'я {name} не знайдено в списку учасників.")
        return

    if action == "confirm":
        # Перевірка, чи користувач уже обрав ім'я
        existing_selection = next((p for p in data["participants"] if p["user_id"] == user_id), None)
        if existing_selection:
            await query.edit_message_text(
                f"⚠️ Ви вже обрали ім'я: {existing_selection['name']}."
            )
            logger.info(f"Користувач {user_id} вже обрав ім'я {existing_selection['name']}.")
            return

        # Перевірка, чи ім'я вже обране іншим користувачем
        if participant["approved"] and participant["user_id"] != user_id:
            await query.edit_message_text(
                f"⚠️ Ім'я *{name}* вже обране іншим користувачем. Спробуйте інше ім'я.",
                parse_mode='Markdown'
            )
            logger.info(f"Ім'я {name} вже обране іншим користувачем {participant['user_id']}.")
            return

        # Призначення імені користувачу
        participant["approved"] = True
        participant["user_id"] = user_id
        logger.info(f"Ім'я {name} підтверджено користувачем {user_id}.")

        # Вибір учасника для дарування подарунка
        remaining_participants = [
            p for p in data["participants"]
            if p["name"] != name and not p.get("assigned_to")
        ]
        remaining_colors = data["colors"]

        if not remaining_participants or not remaining_colors:
            await query.edit_message_text("😢 На жаль, немає доступних учасників для призначення.")
            logger.warning("Немає доступних учасників або кольорів для призначення.")
            return

        # Випадковий вибір з доступних
        assigned_participant = random.choice(remaining_participants)
        assigned_color = random.choice(remaining_colors)
        logger.info(f"Призначено колір {assigned_color} для {assigned_participant['name']} від {name}.")

        # Оновлення стану призначеного учасника
        assigned_participant["assigned_to"] = name
        assigned_participant["color"] = assigned_color
        data["colors"].remove(assigned_color)
        logger.info(f"Колір {assigned_color} видалено з доступних кольорів.")

        # Додавання інформації про призначення до вибраного користувача
        participant["assigned_to"] = assigned_participant["name"]
        participant["color"] = assigned_color

        save_data()
        logger.info(f"Дані збережено після призначення {assigned_color} для {assigned_participant['name']}.")

        await query.edit_message_text(
            f"🎉 Вітаю, {name}! Ви будете дарувати подарунок для {assigned_participant['name']} з кольором {assigned_color}! 🎁"
        )
    elif action == "cancel":
        await query.edit_message_text("❌ Вибір скасовано.")
        logger.info(f"Користувач {user_id} скасував вибір імені {name}.")
    else:
        await query.edit_message_text("⚠️ Невідома дія.")
        logger.warning(f"Невідома дія: {action}")

# Додаткова команда для перегляду завдання
async def my_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    participant = next((p for p in data["participants"] if p["user_id"] == user_id), None)

    if participant and participant["assigned_to"] and participant["color"]:
        await update.message.reply_text(
            f"🎉 Ваше завдання: дарувати подарунок для {participant['assigned_to']} з кольором {participant['color']} 🎁"
        )
        logger.info(f"Користувач {user_id} переглядає своє завдання.")
    else:
        await update.message.reply_text("⚠️ Ви ще не обрали ім'я або ваше завдання ще не призначене.")
        logger.info(f"Користувач {user_id} спробував переглянути завдання, але воно не призначене.")

# Запуск бота
async def main():
    application = Application.builder().token(TOKEN).build()

    # Додавання хендлерів
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_task", my_task))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    application.add_handler(CallbackQueryHandler(handle_confirmation, pattern=r"^(confirm|cancel)\|.+$"))

    logger.info("🤖 Bot is running...")
    try:
        await application.run_polling()
    except Exception as e:
        logger.error(f"Виникла помилка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
