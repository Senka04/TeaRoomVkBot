import os
from dotenv import load_dotenv  # можно не использовать в replit

# для чтения env файла
load_dotenv()  # можно не использовать в replit

# определения, глобальные переменные
API_VERSION = "5.131"
group_id = '-'+str(os.environ.get("GROUPID"))

# списки
CALLBACK_MODES = ("menu1", "menu2", "menu3", "back")
MESSAGES = ("Режим общения", "Сорт чая", "Выберите чай", "Выбор сделан")
