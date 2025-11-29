import logging
from typing import Any, List, Optional

import httpx
from config import (
    API_BASE_URL,
    API_BOT_NODE_URL,
    API_BOT_ROOT_URL,
    API_MESSAGES_URL,
)


class ApiClient:
    """Клиент для взаимодействия с API сервера."""

    def __init__(self, base_url: str = API_BASE_URL) -> None:
        """Инициализирует клиент API с базовым URL и HTTP-сессией.

        Args:
            base_url (str): Базовый URL API сервера.

        """
        self.base_url = base_url
        self.session = httpx.AsyncClient(base_url=base_url)
        self.token = None

    async def login(
        self, username: str, password: str, telegram_id: int,
    ) -> Optional[dict[str, Any]]:
        """Выполняет аутентификацию пользователя через API.

        Args:
            username (str): Имя пользователя.
            password (str): Пароль.
            telegram_id (int): Telegram ID.

        Returns:
            Optional[dict[str, Any]]: Токен и данные пользователя.

        """
        try:
            login_data = {
                "username": username,
                "password": password,
                "telegram_id": telegram_id,
            }
            response = await self.session.post("/auth/login", json=login_data)
            response.raise_for_status()
            data = response.json()
            self.token = data["token"]
            self.session.headers.update(
                {"Authorization": f"Bearer {self.token}"},
            )
            return data
        except httpx.HTTPStatusError as e:
            logging.error(
                f"HTTP ошибка при логине для {username}: {e}, "
                f"ответ: {e.response.text}",
            )
            return None
        except httpx.RequestError as e:
            logging.error(f"Ошибка запроса при логине для {username}: {e}")
            return None

    async def get_root_node(self) -> Optional[dict[str, Any]]:
        """Получает данные корневого узла контента."""
        try:
            response = await self.session.get(API_BOT_ROOT_URL)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP ошибка при получении корневого узла: {e}")
            return None
        except httpx.RequestError as e:
            logging.error(f"Ошибка запроса при получении корневого узла: {e}")
            return None

    async def get_content_node(self, node_id: int) -> Optional[dict[str, Any]]:
        """Получает данные узла контента по его ID.

        Args:
            node_id (int): Идентификатор узла.

        Returns:
            Optional[dict[str, Any]]: Данные узла.

        """
        try:
            response = await self.session.get(f"{API_BOT_NODE_URL}/{node_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(
                f"HTTP ошибка при получении узла контента {node_id}: {e}",
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"Ошибка запроса при получении узла контента {node_id}: {e}",
            )
            return None

    async def get_user_tickets(self) -> Optional[List[dict[str, Any]]]:
        """Получает список бесед (тикетов) текущего пользователя."""
        try:
            response = await self.session.get(API_MESSAGES_URL)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP ошибка при получении списка бесед: {e}")
            return None
        except httpx.RequestError as e:
            logging.error(f"Ошибка запроса при получении списка бесед: {e}")
            return None

    async def create_ticket(
        self, ticket_data: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Создаёт новую беседу (тикет).

        Args:
            ticket_data (dict[str, Any]): Данные тикета.

        Returns:
            Optional[dict[str, Any]]: Данные созданного тикета.

        """
        try:
            response = await self.session.post(
                API_MESSAGES_URL, json=ticket_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP ошибка при создании тикета: {e}")
            return None
        except httpx.RequestError as e:
            logging.error(f"Ошибка запроса при создании тикета: {e}")
            return None

    async def get_ticket_messages(
        self, ticket_id: int,
    ) -> Optional[List[dict[str, Any]]]:
        """Получает список сообщений указанного тикета.

        Args:
            ticket_id (int): ID тикета.

        Returns:
            Optional[List[dict[str, Any]]]: Список сообщений.

        """
        try:
            response = await self.session.get(
                f"{API_MESSAGES_URL}/{ticket_id}/messages",
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(
                f"HTTP ошибка при получении сообщений тикета {ticket_id}: {e}",
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"Ошибка запроса при получении сообщений тикета "
                f"{ticket_id}: {e}",
            )
            return None

    async def send_message_to_conversation(
        self, ticket_id: int, message_data: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Отправляет сообщение в указанную беседу (тикет).

        Args:
            ticket_id (int): ID тикета.
            message_data (dict[str, Any]): Данные сообщения.

        Returns:
            Optional[dict[str, Any]]: Ответ от API.

        """
        try:
            response = await self.session.post(
                f"{API_MESSAGES_URL}/{ticket_id}/messages", json=message_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(
                f"Ошибка при отправке сообщения в беседу {ticket_id}: {e}",
            )
            return None
        except httpx.RequestError as e:
            logging.error(
                f"Ошибка запроса при отправке сообщения в беседу "
                f"{ticket_id}: {e}",
            )
            return None

    async def close(self) -> None:
        """Закрывает асинхронную HTTP-сессию."""
        await self.session.aclose()
