import logging
from typing import Any, Optional

from aiogram import types
from bot_instance import bot
from keyboard_utils import (
    build_support_menu_keyboard,
    build_ticket_chat_keyboard,
    build_user_tickets_keyboard,
    make_keyboard,
)
from state import (
    api,
    creating_conversation,
    user_nav_stack,
    user_ticket_id,
    waiting_for_message,
)


async def reset_to_root_menu(user_id: int) -> None:
    """Сбрасывает навигацию пользователя к главному меню.

    Запрашивает данные корневого узла через API и отображает главное меню.
    Если данные не получены, отправляет сообщение об ошибке.

    Args:
        user_id: Идентификатор пользователя в Telegram.

    Returns:
        None

    """
    root_node_data = await api.get_root_node()
    if root_node_data:
        user_nav_stack[user_id] = [root_node_data["id"]]
        await show_main_menu(user_id, root_node_data)
    else:
        await bot.send_message(user_id, "Не удалось загрузить главное меню.")


async def show_main_menu(
    user_id: int,
    root_node_data: Optional[dict] = None,
) -> None:
    """Отображает главное меню бота для указанного пользователя.

    Запрашивает данные корневого узла, если они не переданы,
    и формирует клавиатуру с опциями.
    Отправляет изображения и текст меню, если они доступны.

    Args:
        user_id: Идентификатор пользователя в Telegram.
        root_node_data: Данные корневого узла меню (словарь).

    Returns:
        None

    Raises:
        Exception: Если не удалось отправить изображение, логируется ошибка.

    """
    if root_node_data is None:
        if not api.token:
            await bot.send_message(
                user_id,
                "Ошибка: пользователь не аутентифицирован. Попробуйте /start.",
            )
            return
        root_node_data = await api.get_root_node()
        if not root_node_data:
            await bot.send_message(
                user_id,
                "Не удалось загрузить главное меню. "
                "Возможно, проблема с аутентификацией.",
            )
            return
        user_nav_stack[user_id] = [root_node_data["id"]]

    markup = make_keyboard(root_node_data["id"], root_node_data, is_root=True)

    if root_node_data.get('images'):
        for img_url in root_node_data['images']:
            try:
                await bot.send_photo(user_id, img_url)
            except Exception as e:
                logging.error(
                    f"Не удалось отправить фото {img_url} "
                    f"пользователю {user_id}: {e}",
                )

    await bot.send_message(
        user_id,
        root_node_data.get('text', 'Выберите раздел:'),
        reply_markup=markup,
    )


async def handle_navigation_actions(
    message: types.Message,
    user_id: int,
    action: Any,
    back: bool = False,
) -> None:
    """Обрабатывает навигационные действия пользователя."""
    if action == "support_menu":
        await open_support_menu(message, user_id, back)
        return

    if action == "new_conversation":
        await request_new_conversation(message, user_id)
        return

    if action == "list_conversations":
        await show_user_conversations(message, user_id, back)
        return

    if isinstance(action, str) and action.startswith("ticket:"):
        await show_ticket_messages(message, user_id, action, back)
        return

    if action == "back":
        if user_id in user_nav_stack and len(user_nav_stack[user_id]) > 1:
            user_nav_stack[user_id].pop()
            node_id = user_nav_stack[user_id][-1]
            await navigate_content_node(message, user_id, node_id, back=True)
        else:
            await reset_to_root_menu(user_id)
        return

    if action == "home":
        await reset_to_root_menu(user_id)
        return

    if isinstance(action, int):
        await navigate_content_node(message, user_id, action, back)
        return

    await bot.send_message(user_id, "Неизвестное навигационное действие.")


async def open_support_menu(
    message: types.Message,
    user_id: int,
    back: bool,
) -> None:
    """Открывает меню поддержки с соответствующей клавиатурой."""
    if not back:
        user_nav_stack.setdefault(user_id, []).append("support_menu")
    support_keyboard = build_support_menu_keyboard()
    await message.answer("Выберите действие:", reply_markup=support_keyboard)


async def request_new_conversation(
    message: types.Message,
    user_id: int,
) -> None:
    """Запрашивает название новой беседы у пользователя."""
    creating_conversation[user_id] = True
    await message.answer("Введите название новой беседы:")


async def show_user_conversations(
    message: types.Message,
    user_id: int,
    back: bool,
) -> None:
    """Показывает список активных бесед пользователя."""
    if not back:
        user_nav_stack.setdefault(user_id, []).append("list_conversations")
    tickets = await api.get_user_tickets()
    if tickets:
        markup = build_user_tickets_keyboard(tickets)
        await message.answer("Ваши беседы:", reply_markup=markup)
    else:
        await message.answer("У вас нет бесед.")


async def show_ticket_messages(
    message: types.Message,
    user_id: int,
    action: str,
    back: bool,
) -> None:
    """Показывает историю сообщений в выбранной беседе."""
    ticket_id = int(action.split(":")[1])
    messages = await api.get_ticket_messages(ticket_id)
    if not back:
        user_nav_stack.setdefault(user_id, []).append(action)
    if messages:
        await message.answer(f"\U0001F4AC Сообщения в беседе #{ticket_id}:")
        for m in messages:
            sender = "Вы" if m["sender_id"] == user_id else "Менеджер"
            dt = m["created_at"]
            await message.answer(
                f"\U0001F552 {dt}\n\U0001F464 {sender}:\n{m['text']}",
            )
    else:
        await message.answer("Беседа пуста.")

    user_ticket_id[user_id] = ticket_id
    waiting_for_message.add(user_id)
    await message.answer(
        "\u270F\ufe0f Напишите новое сообщение:",
        reply_markup=build_ticket_chat_keyboard(),
    )


async def navigate_content_node(
    message: types.Message,
    user_id: int,
    node_id: int,
    back: bool,
) -> None:
    """Навигация по узлам контента: отображение текста, кнопок, изображений."""
    node_data_response = await api.get_content_node(node_id)
    node_data = node_data_response.get("node") if node_data_response else None

    if not node_data:
        await bot.send_message(
            user_id,
            "Не удалось найти информацию по этому разделу. Попробуйте позже.",
        )
        return

    has_children_buttons = bool(node_data.get("buttons"))
    is_root = user_nav_stack.get(user_id) == [node_id]

    if has_children_buttons:
        if (
            not back
            and (
                not user_nav_stack.get(user_id)
                or user_nav_stack[user_id][-1] != node_id
            )
        ):
            user_nav_stack.setdefault(user_id, []).append(node_id)

        markup = make_keyboard(node_id, node_data, is_root=is_root)

        for img_url in node_data.get("images", []):
            try:
                await bot.send_photo(user_id, img_url)
            except Exception as e:
                logging.error(
                    f"Не удалось отправить фото "
                    f"{img_url} пользователю {user_id}: {e}",
                )

        await bot.send_message(
            user_id,
            node_data.get("text", "Раздел"),
            reply_markup=markup,
        )
    else:
        await bot.send_message(
            user_id,
            f"📌 {node_data.get('title', '')}"
            f"\n\n{node_data.get('text', '')}",
        )
