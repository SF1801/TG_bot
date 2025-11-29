import os

from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

API_BOT_ROOT_URL = "/bot/content/root"
API_BOT_NODE_URL = "/bot/content/nodes"
API_MESSAGES_URL = "/messenger/conversations"
API_CONVERSATIONS_URL = "/messenger/conversations"
