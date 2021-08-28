import logging
import os
import time
import requests
import telegram
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler


logging.basicConfig(filename='bot_logger.log', encoding='UTF-8',
                    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(10)
handler = RotatingFileHandler('bot_logger.log', maxBytes=10 ** 7, backupCount=3)
logger.addHandler(handler)

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    # Тут 'lesson_name' выглядит красивее
    # Или хoтя бы '.zip' отрезать
    homework_name = homework['homework_name']
    if homework['status'] != 'approved':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    homework_statuses = requests.get(
        url='https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
        params={'from_date': current_timestamp})
    return homework_statuses.json()


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    while True:
        try:
            logger.debug('Program started')
            homeworks = get_homeworks(current_timestamp)
            for homework in homeworks['homeworks']:
                message = parse_homework_status(homework)
                send_message(message)
                logger.info(f'Status sent to {CHAT_ID}')
            time.sleep(29 * 60)

        except Exception as e:
            message = f'Бот упал с ошибкой: {e}'
            logger.error(message, exc_info=True)
            send_message(message)
            logger.info(f'Error sent to {CHAT_ID}')
            print(message)
            time.sleep(29 * 60)


if __name__ == '__main__':
    main()
