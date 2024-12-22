import requests
import json
from typing import Optional, Union
from api_key import WEATHER_API_KEY

response_lang = "ru-ru"


def fahrenheit_to_celsius(temperature: float) -> float:
    """
    Переводит температуру из шкалы Фаренгейта в шкалу Цельсия
    :param temperature: значение температуры в шкале Фаренгейта
    :return: значение температуры в шкале Цельсия
    """
    return (temperature - 32) * 5/9


def miles_to_kilometers(miles: float) -> float:
    """
    Переводит величину (скорость или расстояние), связанную с милями
    в величину, связанную с километрами
    :param miles: значение величины в милях
    :return: значение величины в километрах
    :param miles:
    :return:
    """
    return 1.609 * miles


def get_location_key_by_geo_position(latitude: float, longitude: float) -> Optional[str]:
    """
    Получает ключ гео-позиции с сайта AccuWeather по географической широте и географической долготе

    Возвращает полученный ключ гео-позиции в формате строки
    :param latitude: Географическая широта
    :param longitude: Географическая долгота
    :return: Ключ гео-позиции с сайта AccuWeather
    """
    q = f"{latitude},{longitude}"
    geo_base_url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
    params = {
        "apikey": WEATHER_API_KEY,
        "q": q,
        "language": response_lang,
    }
    response = requests.get(geo_base_url, params=params)
    if response.status_code != 200:
        print(f"Ошибка при получении геолокации: {response.text}")
        return
    if not response.json():
        return
    location_key = response.json()["Key"]
    return location_key


def get_location_key_by_city_name(city_name: str, return_geo: bool = False) -> Union[str, tuple, None]:
    """
    Получает ключ гео-позиции с сайта AccuWeather по названию города

    Возвращает полученный ключ гео-позиции в формате строки
    :param city_name: Название города
    :param return_geo: Нужно ли вернуть информацию о геопозиции (ширину и долготу)
    :return: None при ошибке, либо - ключ гео-позиции с сайта AccuWeather.
    При return_geo = True возвращает также словарь координат latitude, longitude
    """
    cities_base_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {
        "apikey": WEATHER_API_KEY,
        "q": city_name,
        "language": response_lang,
    }
    response = requests.get(cities_base_url, params=params)
    if response.status_code != 200:
        print(f"Ошибка при получении геолокации: {response.text}")
        return
    if not response.json():
        print(f"Не смог получить ключ геолокации для города {city_name}")
        return
    location_key = response.json()[0]["Key"]
    if return_geo:
        geo_position = response.json()[0]["GeoPosition"]
        geo_dict = {
            "latitude": geo_position["Latitude"],
            "longitude": geo_position["Longitude"]
        }
        return location_key, geo_dict
    return location_key


def get_forecast_data_by_location_key(location_key: str) -> Optional[str]:
    """Возвращает данные о дневном прогнозе погоды в локации по её ключу локации
    с сайта AccuWeather

    Ответ в формате JSON со следующими значениями:

    - temperature - Средняя дневная температура

    - humidity - Относительная влажность воздуха

    - wind_speed - Средняя дневная скорость воздуха

    - precipitation_probability - Дневная вероятность выпадения осадков

    :param location_key: Ключ локации с сайта AccuWeather
    :return: Данные о погоде в формате JSON, либо None при ошибке
    """
    forecast_base_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}"
    params = {
        "apikey": WEATHER_API_KEY,
        "language": response_lang,
        "details": True,
    }
    response = requests.get(forecast_base_url, params=params)
    if response.status_code != 200:
        print(f"Ошибка при получении прогноза погоды: {response.text}")
        return
    response_json = response.json()
    forecast = response_json["DailyForecasts"][0]
    temperature_data = forecast["Day"]["WetBulbTemperature"]["Average"]
    humidity_data = forecast["Day"]["RelativeHumidity"]["Average"]
    wind_speed_data = forecast["Day"]["Wind"]["Speed"]
    precipitation_probability = forecast["Day"]["PrecipitationProbability"]

    # Перевод температуры из шкалы Фаренгейта в шкалу Цельсия
    temperature_value = fahrenheit_to_celsius(temperature_data["Value"])

    # Перевод скорости в ветра из мили/ч в км/ч
    wind_speed_value = miles_to_kilometers(wind_speed_data["Value"])
    result = {
        "temperature": temperature_value,
        "humidity": humidity_data,
        "wind_speed": wind_speed_value,
        "precipitation_probability": precipitation_probability,
    }
    json_result = json.dumps(result, indent=4)
    return json_result


def get_several_days_forecast_by_location_key(location_key: str, days: int = 5) -> Optional[list]:
    """Возвращает данные о прогнозе погоды на несколько дней в локации по её ключу локации
    с сайта AccuWeather

    Ответ в формате списка словарей со следующими значениями:

    - temperature - Средняя дневная температура

    - humidity - Относительная влажность воздуха

    - wind_speed - Средняя дневная скорость воздуха

    - precipitation_probability - Дневная вероятность выпадения осадков

    :param location_key: Ключ локации с сайта AccuWeather
    :param days: Количество дней в прогнозе (целое число от одного до пяти)
    :return: Данные о погоде в формате списка словарей, либо None при ошибке
    """
    assert 1 <= days <= 5, "Возможно получение прогнозов погоды от 1 до 5 дней, включая концы"
    forecast_base_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}"
    params = {
        "apikey": WEATHER_API_KEY,
        "language": response_lang,
        "details": True,
    }
    response = requests.get(forecast_base_url, params=params)
    if response.status_code != 200:
        print(f"Ошибка при получении прогноза погоды: {response.text}")
        return
    response_json = response.json()
    result_array = []
    for i in range(days):
        forecast = response_json["DailyForecasts"][i]
        temperature_data = forecast["Day"]["WetBulbTemperature"]["Average"]
        humidity_data = forecast["Day"]["RelativeHumidity"]["Average"]
        wind_speed_data = forecast["Day"]["Wind"]["Speed"]
        precipitation_probability = forecast["Day"]["PrecipitationProbability"]

        # Перевод температуры из шкалы Фаренгейта в шкалу Цельсия
        temperature_value = fahrenheit_to_celsius(temperature_data["Value"])

        # Перевод скорости в ветра из мили/ч в км/ч
        wind_speed_value = miles_to_kilometers(wind_speed_data["Value"])
        result = {
            "temperature": temperature_value,
            "humidity": humidity_data,
            "wind_speed": wind_speed_value,
            "precipitation_probability": precipitation_probability,
        }
        result_array.append(result)

    return result_array


def check_bad_weather(temperature: float, humidity: float, wind_speed: float, precipitation_probability: float) -> bool:
    """
    Проверяет по данным из прогноза погоды (температуре, влажности, скорости ветра, вероятности осадков),
    является ли погода плохой. Возвращает True, если погода плохая и False - иначе.

    :param temperature: Температура
    :param humidity: Влажность
    :param wind_speed: Скорость ветра
    :param precipitation_probability: Вероятность осадков
    :return: Ответ на вопрос: является ли погода плохой. (True/False)
    """
    try:
        # Для величин, чьё значение не None, проверяем, подходят ли они под критерии
        # плохой погоды
        if temperature and (temperature < 0 or temperature > 35):
            return True
        if wind_speed and wind_speed > 50:
            return True
        if precipitation_probability and precipitation_probability > 70:
            return True
        if humidity and (humidity < 30 or humidity > 80):
            return True
    # В случае, когда в прогноз попало нечто, что нельзя сравнить возвращаем False
    except TypeError as e:
        print(repr(e))
        return False
    except Exception as e:
        print(repr(e))
        return False
    return False
