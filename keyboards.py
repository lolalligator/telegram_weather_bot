from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура для выбора количества дней в прогнозе
days_choice_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="1"),
            KeyboardButton(text="2"),
            KeyboardButton(text="3"),
            KeyboardButton(text="4"),
            KeyboardButton(text="5"),
        ],
    ],
    resize_keyboard=True
)