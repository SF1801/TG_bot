import unicodedata
from typing import Any, Dict, List

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

normalized_button_actions: Dict[str, Any] = {}


def normalize_text(text: str) -> str:
    """Нормализует текстовую строку для сравнения.

    Удаляет пробелы и приводит к нижнему регистру.

    :param text: Входная строка.
    :return: Нормализованная строка.
    """
    return unicodedata.normalize("NFKC", text.strip().lower())


def make_keyboard(
    current_node_id: int,
    current_node_data: Dict[str, Any],
    is_root: bool = False,
) -> ReplyKeyboardMarkup:
    """Создает клавиатуру для заданного узла контента.

    :param current_node_id: ID текущего узла контента.
    :param current_node_data: Данные текущего узла контента, содержащие кнопки.
    :param is_root: Флаг, указывающий, является ли текущий узел корневым.
    :return: Объект ReplyKeyboardMarkup.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    current_row_buttons = []
    children_buttons = current_node_data.get('buttons', [])

    for i, button_data in enumerate(children_buttons):
        text = button_data.get('text', 'Неизвестно')
        node_id_for_button = button_data.get('next_node_id')
        if node_id_for_button is not None:
            button = KeyboardButton(text)
            current_row_buttons.append(button)
            normalized_button_actions[
                normalize_text(text)
            ] = node_id_for_button
            if len(current_row_buttons) == 2 or i == len(children_buttons) - 1:
                markup.add(*current_row_buttons)
                current_row_buttons = []

    support_button_text = "✉ Написать в поддержку"
    normalized_button_actions[
        normalize_text(support_button_text)
    ] = "support_menu"
    markup.add(KeyboardButton(support_button_text))

    if not is_root:
        back_button_text = "⬅️ Назад"
        home_button_text = "🏠 В начало"
        normalized_button_actions[normalize_text(back_button_text)] = "back"
        normalized_button_actions[normalize_text(home_button_text)] = "home"
        navigation_buttons = [
            KeyboardButton(back_button_text),
            KeyboardButton(home_button_text),
        ]
        markup.add(*navigation_buttons)

    return markup


def build_ticket_chat_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для чата с тикетами.

    Содержит кнопки "Назад" и "В начало" в одной строке.

    :return: Объект ReplyKeyboardMarkup.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button_text = "⬅️ Назад"
    home_button_text = "🏠 В начало"
    markup.add(
        KeyboardButton(back_button_text),
        KeyboardButton(home_button_text),
    )
    normalized_button_actions[normalize_text(back_button_text)] = "back"
    normalized_button_actions[normalize_text(home_button_text)] = "home"
    return markup


def build_support_menu_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для меню поддержки.

    :return: Объект ReplyKeyboardMarkup.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    new_conv = "➕ Новая беседа"
    my_conv = "📂 Мои беседы"
    back_button_text = "⬅️ Назад"
    home_button_text = "🏠 В начало"

    markup.add(KeyboardButton(new_conv))
    markup.add(KeyboardButton(my_conv))
    markup.add(
        KeyboardButton(back_button_text),
        KeyboardButton(home_button_text),
    )

    normalized_button_actions[normalize_text(new_conv)] = "new_conversation"
    normalized_button_actions[normalize_text(my_conv)] = "list_conversations"
    normalized_button_actions[normalize_text(back_button_text)] = "back"
    normalized_button_actions[normalize_text(home_button_text)] = "home"
    return markup


def build_user_tickets_keyboard(
        tickets: List[Dict[str, Any]],
) -> ReplyKeyboardMarkup:
    """Создает клавиатуру со списком бесед пользователя.

    Включает кнопки "Назад" и "В начало" в одной строке.

    :param tickets: Список словарей, представляющих беседы пользователя.
    :return: Объект ReplyKeyboardMarkup.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for t in tickets:
        title = t.get("conversation_name", f"Беседа #{t['id']}")
        button_text = f"💬 {title}"
        markup.add(KeyboardButton(button_text))
        normalized_button_actions[
            normalize_text(button_text)
        ] = f"ticket:{t['id']}"

    back_button_text = "⬅️ Назад"
    home_button_text = "🏠 В начало"
    markup.add(
        KeyboardButton(back_button_text),
        KeyboardButton(home_button_text),
    )
    normalized_button_actions[normalize_text(back_button_text)] = "back"
    normalized_button_actions[normalize_text(home_button_text)] = "home"
    return markup
