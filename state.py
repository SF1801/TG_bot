from typing import Any, Dict, Set

from api_client import ApiClient

user_nav_stack: Dict[int, list[Any]] = {}
waiting_for_message: Set[int] = set()
user_ticket_id: Dict[int, int] = {}
creating_conversation: Dict[int, bool] = {}
awaiting_username: Dict[int, bool] = {}
awaiting_password: Dict[int, str] = {}
api = ApiClient()
