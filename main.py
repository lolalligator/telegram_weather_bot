from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
import asyncio
import logging
import weather_api
from api_key import TELEGRAM_API_TOKEN
from commands_text import start_text, help_text
from keyboards import days_choice_keyboard

# Включаем логирование для отладки
logging.basicConfig(level=logging.INFO)

# Инициализация экземпляров бота и диспетчера, хранилища для состояний и роутера
bot = Bot(token=TELEGRAM_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


# Создаем группу состояний для работы с пользовательским вводом
class Form(StatesGroup):
    cities = State()  # Города на маршруте
    days = State()  # Количество дней в прогнозе погоды


@dp.message(F.text == '/start')
async def send_welcome(message: types.Message):
    """Приветствует пользователя и предоставляет краткое описание возможностей бота"""
    await message.answer(start_text, reply_markup=ReplyKeyboardRemove())


@dp.message(F.text == '/help')
async def send_help(message: types.Message):
    """Отображает список доступных команд и выдаёт краткую инструкцию по использованию"""
    await message.answer(help_text, reply_markup=ReplyKeyboardRemove())


@dp.message(F.text == '/weather')
async def weather_start(message: types.Message, state: FSMContext):
    """Инициализация команды /weather и начало обработки ответов пользователя"""
    await message.answer("Введите список городов через запятую (например: Москва, Санкт-Петербург, Казань):",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.cities)  # Устанавливаем состояние для ввода городов


@dp.message(Form.cities)
async def get_cities(message: types.Message, state: FSMContext):
    """Обрабатывает список городов, введённый пользователем."""
    cities = [city.strip() for city in message.text.split(',')]

    if not cities:
        await message.answer("Список городов не может быть пустым. Попробуйте снова.")
        return

    await state.update_data(cities=cities)  # Сохраняем список городов
    await message.answer("Введите количество дней для прогноза (от 1 до 5):", reply_markup=days_choice_keyboard)
    await state.set_state(Form.days)  # Устанавливаем состояние для ввода дней


async def report_weather_api_error(message: types.Message, state):
    """Пишет отчёт об ошибке при получении прогнозов погоды"""
    logging.error(f"Возникла ошибка при получении прогнозов погоды")
    await message.answer("""Возникла ошибка при получении прогнозов погоды. 
Проверьте корректность введенных названий городов и наличие доступных запросов к AccuWeather API.""")
    await state.clear()

@dp.message(Form.days)
async def get_days(message: types.Message, state: FSMContext):
    """Обрабатывает количество дней для прогноза."""
    # Ожидаем, пока пользователь введёт целое число от 1 до 5
    try:
        days = int(message.text)
        if not (1 <= days <= 5):
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите число от 1 до 5.")
        return

    await state.update_data(days=days)  # Сохраняем количество дней
    user_data = await state.get_data()  # Получаем все данные пользователя
    cities = user_data['cities']

    # Формируем прогноз погоды и отправляем его пользователю:
    for city in cities:
        city_report = f"Прогноз погоды для города {city}.\n\n"
        # Получаем ключ локации с сайта AccuWeather для дальнейшей работы с API
        location_key = weather_api.get_location_key_by_city_name(city)

        try:
            forecasts = weather_api.get_several_days_forecast_by_location_key(location_key, days)
        except Exception as ex:
            await report_weather_api_error(message, state)
            logging.error(f"Информация об ошибке: {ex}")
            return

        if not forecasts:
            await report_weather_api_error(message, state)
            return

        # Нумеруем дни прогноза погоды и для каждого дня добавляем данные в отчёт
        for i, forecast in enumerate(forecasts, start=1):
            city_report += f"День {i}.\n\n"
            city_report += f"Температура (°C): {forecast['temperature']:.2f}\n"
            city_report += f"Влажность (%): {forecast['humidity']:.2f}\n"
            city_report += f"Скорость ветра (км/ч): {forecast['wind_speed']:.2f}\n"
            city_report += f"Вероятность осадков (%): {forecast['precipitation_probability']:.2f}\n"
            city_report += "\n"

        await message.answer(city_report, reply_markup=ReplyKeyboardRemove())

    # Завершаем состояние
    await state.clear()


async def main():
    # Подключаем бота и диспетчера
    await dp.start_polling(bot)


# Запуск бота
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
