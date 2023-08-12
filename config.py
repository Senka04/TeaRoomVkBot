import os

from dotenv import load_dotenv  # можно не использовать в replit

# для чтения env файла
load_dotenv()  # можно не использовать в replit

# определения
API_VERSION = "5.131"
group_id = '-'+str(os.environ.get("GROUPID"))

# списки
CALLBACK_MODES = ("mode1", "mode2", "back")
NOT_INLINE_KEYBOARD = ("shop", "keyboard_inline")
