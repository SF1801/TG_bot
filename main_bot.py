import logging

from aiogram import Dispatcher, types
from aiogram.utils import executor
from bot_instance import bot
from state import (
    api,
    awaiting_username,
)
from text_handlers import text_message_handler

dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message) -> None:
    """Обрабатывает команду /start для начала взаимодействия с ботом.

    Запрашивает у пользователя имя пользователя для аутентификации.

    Args:
        message: Сообщение от пользователя с командой /start.

    Returns:
        None

    """
    user_id = message.from_user.id
    awaiting_username[user_id] = True
    await bot.send_message(user_id, "Введите ваше имя пользователя:")


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_text(message: types.Message) -> None:
    """Обрабатывает входящие текстовые сообщения от пользователя.

    Перенаправляет обработку текстового сообщения в функцию
    `text_message_handler` для дальнейшей логики обработки.

    Args:
        message: Объект входящего сообщения от пользователя, содержащий текст.

    Returns:
        None

    """
    await text_message_handler(message)


async def on_shutdown(dp: Dispatcher) -> None:
    """Выполняет действия при завершении работы бота.

    Закрывает сессию API клиента для освобождения ресурсов.

    Args:
        dp: Диспетчер бота aiogram.

    Returns:
        None

    """
    await api.close()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown)
