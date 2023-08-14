from dotenv import load_dotenv  # можно не использовать в replit

# для чтения env файла
load_dotenv()  # можно не использовать в replit

# определения, глобальные переменные
API_VERSION = "5.131"
GROUPID = '221959616'
ADMIN = '350929022'
group_id = '-'+str(GROUPID)

# списки
CALLBACK_MODES = ("menu1", "menu2", "menu3", "back", "admin")
MESSAGES = ("Режим общения", "Сорт чая", "Выберите чай", "Выбор сделан")
ADMIN_MESSAGES = ("Можете поменять названия кнопок",)
PAYLOAD_TEXT = ('txt', 'vc')
keyboard_buttons = []

json1 = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Текстовые сообщения",
                "payload": f'{{\"type\": \"menu1\", \"text\": "{PAYLOAD_TEXT[0]}"}}'
            },
            "color": "secondary"
        }
    ],
    [
        {
            "action": {
                "type": "callback",
                "label": "Голосовые сообщения",
                "payload": f'{{\"type\": \"menu1\", \"text\": "{PAYLOAD_TEXT[1]}"}}'
            },
            "color": "secondary"
        }
    ],
    [
        {
            "action": {
                "type": "open_link",
                "label": "Создатель бота",
                "link": "https://vk.com/az_projects",
            }
        }
    ]
]

json2 = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Назад",
                "payload": "{\"type\": \"back\"}"
            },
            "color": "primary"
        }
    ],
    [
        {
            "action": {
                "type": "callback",
                "label": "Дальше",
                "payload": "{\"type\": \"menu2\"}"
            },
            "color": "secondary"
        }
    ]
]

json3 = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Назад",
                "payload": "{\"type\": \"back\"}"
            },
            "color": "primary"
        }
    ],
    [
        {
            "action": {
                "type": "callback",
                "label": "Дальше",
                "payload": "{\"type\": \"menu3\"}"
            },
            "color": "secondary"
        }
    ]
]

json4 = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Назад",
                "payload": "{\"type\": \"back\"}"
            },
            "color": "primary"
        }
    ]
]
json_admin = [
    {
        "action": {
            "type": "callback",
            "label": "Админ",
            "payload": "{\"type\": \"admin\"}"
        },
        "color": "primary"
    }
]
keyboard_buttons.append(json1.copy())
keyboard_buttons.append(json2.copy())
keyboard_buttons.append(json3.copy())
keyboard_buttons.append(json4.copy())
