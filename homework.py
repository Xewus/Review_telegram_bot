import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

REQUESTS_PERIOD = 10 * 60
ERROR_PERIOD = 29 * 60
REQUESTS_API_URL = 'https://praktikum.yandex.ru/api/user_api/'
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
STATUSES = {'approved': 'Ревьюеру всё понравилось, работа зачтена!',
            'rejected': 'К сожалению, в работе нашлись ошибки.',
            'reviewing': 'Работа взята в ревью'}


formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(10)

rotating_handler = RotatingFileHandler(
    'bot_log.log', maxBytes=10 ** 7, backupCount=3)

file_handler = logging.FileHandler('bot_log.log', encoding='UTF-8')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(30)

logger.addHandler(rotating_handler)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def send_log_error(message):
    logger.error(message, exc_info=True)
    send_message(message)
    logger.info(f'Ошибка отправлена в чат: {CHAT_ID}\n'
                f'текст сообщения: {message}')
    time.sleep(ERROR_PERIOD)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('Отсутствует ключ "homework_name"')

    status = homework.get('status')
    if status is None:
        raise KeyError('Отсутствует ключ "status"')

    verdict = STATUSES.get(status)
    if verdict is None:
        raise ValueError(f'Получено неожиданное значение "status": "{status}"')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    try:
        homework_statuses = requests.get(
            url=REQUESTS_API_URL + 'homework_statuses/',
            headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
            params={'from_date': current_timestamp})

        code_200 = homework_statuses.status_code
        if code_200 != 200:
            raise ValueError(f'Некорректный ответ сервера, код "{code_200}"')
        return homework_statuses.json()

    except ConnectionError as ce:
        message = f'Соединение не установлено. Ошибка {ce}'
        send_log_error(message)

    except json.JSONDecodeError as je:
        message = f'Ошибка преобразования в JSON: {je}'
        send_log_error(message)


def main():
    current_timestamp = int(time.time())
    while True:
        try:
            logger.debug('Program started')
            homeworks = get_homeworks(current_timestamp)

            date_updated = homeworks.get('current_date')
            if date_updated:
                current_timestamp = date_updated

            homeworks = homeworks.get('homeworks')
            if homeworks is None:
                raise KeyError('Отсутствует ключ "homeworks"')

            for homework in homeworks:
                message = parse_homework_status(homework)
                send_message(message)
                logger.info(f'Статус отправлен в чат {CHAT_ID}')
            time.sleep(REQUESTS_PERIOD)

        except Exception as e:
            message = f'Бот упал с ошибкой: {e}'
            send_log_error(message)


if __name__ == '__main__':
    main()
