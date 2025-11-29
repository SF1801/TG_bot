from typing import Optional

from aiogram import types
from keyboard_utils import (
    build_ticket_chat_keyboard,
    build_user_tickets_keyboard,
    normalize_text,
    normalized_button_actions,
)
from navigation_handler import handle_navigation_actions, reset_to_root_menu
from state import (
    api,
    awaiting_password,
    awaiting_username,
    creating_conversation,
    user_nav_stack,
    user_ticket_id,
    waiting_for_message,
)


async def text_message_handler(message: types.Message) -> None:
    """Обрабатывает входящее текстовое сообщение от пользователя.

    Определяет текущее состояние пользователя и делегирует обработку
    соответствующей функции: вход, навигация, отправка сообщений и др.

    :param message: Объект входящего сообщения от пользователя.
    """
    user_id: int = message.from_user.id
    user_text: str = normalize_text(message.text)

    if user_id in awaiting_username:
        await handle_username_input(message, user_id)
    elif user_id in awaiting_password:
        await handle_password_input(message, user_id)
    elif user_text == normalize_text("⬅️ Назад"):
        await handle_back_action(message, user_id)
    elif user_text == normalize_text("🏠 В начало"):
        await handle_home_action(message, user_id)
    elif user_id in creating_conversation:
        await handle_conversation_creation(message, user_id)
    elif user_id in waiting_for_message:
        await handle_send_message(message, user_id)
    else:
        await handle_navigation_or_fallback(message, user_id, user_text)


async def handle_username_input(message: types.Message, user_id: int) -> None:
    """Обрабатывает ввод имени пользователя.

    Сохраняет имя и запрашивает пароль для последующего входа.

    :param message: Сообщение с введённым именем.
    :param user_id: Идентификатор пользователя Telegram.
    """
    awaiting_username.pop(user_id)
    awaiting_password[user_id] = message.text.strip()
    await message.answer("Введите ваш пароль:")


async def handle_password_input(message: types.Message, user_id: int) -> None:
    """Обрабатывает ввод пароля и выполняет попытку входа.

    При успешной авторизации сбрасывает состояние в корневое меню.
    При ошибке уведомляет пользователя.

    :param message: Сообщение с введённым паролем.
    :param user_id: Идентификатор пользователя Telegram.
    """
    username: str = awaiting_password.pop(user_id)
    password: str = message.text.strip()
    login_response: Optional[dict] = await api.login(
        username,
        password,
        user_id,
    )

    if login_response and "token" in login_response:
        await reset_to_root_menu(user_id)
    else:
        await message.answer(
            "Неверные учетные данные. Попробуйте снова с /start.",
        )


async def handle_back_action(message: types.Message, user_id: int) -> None:
    """Обрабатывает нажатие кнопки «⬅️ Назад».

    Возвращает пользователя на предыдущий экран, либо в корень,
    если история навигации пуста.

    :param message: Сообщение от пользователя.
    :param user_id: Идентификатор пользователя Telegram.
    """
    if user_id in user_nav_stack and len(user_nav_stack[user_id]) > 1:
        user_nav_stack[user_id].pop()
        previous_action: str = user_nav_stack[user_id][-1]
        waiting_for_message.discard(user_id)
        user_ticket_id.pop(user_id, None)
        await handle_navigation_actions(
            message,
            user_id,
            previous_action,
            back=True,
        )
    else:
        waiting_for_message.discard(user_id)
        user_ticket_id.pop(user_id, None)
        await reset_to_root_menu(user_id)


async def handle_home_action(message: types.Message, user_id: int) -> None:
    """Обрабатывает нажатие кнопки «🏠 В начало».

    Сбрасывает все временные состояния пользователя:
    - удаляет текущую выбранную беседу;
    - отключает режим ожидания ввода сообщения;
    - сбрасывает навигацию в корень меню.

    :param message: Сообщение от пользователя.
    :param user_id: Идентификатор пользователя Telegram.
    """
    waiting_for_message.discard(user_id)
    user_ticket_id.pop(user_id, None)
    await reset_to_root_menu(user_id)


async def handle_conversation_creation(
    message: types.Message,
    user_id: int,
) -> None:
    """Создаёт новую беседу с указанным названием.

    Отправляет запрос на создание, добавляет беседу в список
    и предлагает выбрать её для продолжения общения.

    :param message: Сообщение с названием беседы.
    :param user_id: Идентификатор пользователя Telegram.
    """
    title: str = message.text.strip()
    ticket_response: Optional[dict] = await api.create_ticket({
        "client_id": user_id,
        "is_active": True,
        "conversation_name": title,
    })

    creating_conversation.pop(user_id, None)

    if ticket_response and "ticket_id" in ticket_response:
        tickets: Optional[list[dict]] = await api.get_user_tickets()
        user_nav_stack.setdefault(user_id, []).append("list_conversations")
        await message.answer(
            f"✅ Беседа «{title}» создана. "
            "Выберите её из списка, чтобы продолжить.",
            reply_markup=build_user_tickets_keyboard(tickets or []),
        )
    else:
        await message.answer("Не удалось создать беседу. Попробуйте позже.")


async def handle_send_message(message: types.Message, user_id: int) -> None:
    """Отправляет сообщение в текущую активную беседу пользователя.

    Проверяет, выбрана ли беседа, и передаёт сообщение через API.

    :param message: Текстовое сообщение от пользователя.
    :param user_id: Идентификатор пользователя Telegram.
    """
    ticket_id: Optional[int] = user_ticket_id.get(user_id)
    if ticket_id:
        send_status: Optional[dict] = await api.send_message_to_conversation(
            ticket_id=ticket_id,
            message_data={"text": message.text},
        )
        if send_status and send_status.get("status") == "success":
            await message.answer(
                "✅ Сообщение отправлено.",
                reply_markup=build_ticket_chat_keyboard(),
            )
        else:
            await message.answer(
                "Не удалось отправить сообщение. Попробуйте позже.",
            )
    else:
        await message.answer("Нет выбранной беседы. Выберите её из списка.")


async def handle_navigation_or_fallback(
    message: types.Message,
    user_id: int,
    user_text: str,
) -> None:
    """Обрабатывает навигационные действия или неизвестные команды.

    Ищет соответствующее действие по тексту, либо отправляет
    уведомление об ошибке.

    :param message: Входящее сообщение от пользователя.
    :param user_id: Идентификатор пользователя Telegram.
    :param user_text: Нормализованный текст сообщения.
    """
    action: Optional[str] = normalized_button_actions.get(user_text)
    if action is None:
        await message.answer("Неизвестная команда. Используйте кнопки.")
        return
    await handle_navigation_actions(message, user_id, action)
