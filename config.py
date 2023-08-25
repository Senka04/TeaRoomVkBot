from dotenv import load_dotenv  # можно не использовать в replit

# для чтения env файла
load_dotenv()  # можно не использовать в replit

# определения, глобальные переменные
API_VERSION = "5.131"
GROUPID = '221959616'
group_id = '-'+str(GROUPID)

# списки
CALLBACK_MODES = ("next", "back", "admin", "add_butt", "del_butt", "add_text", "del_text", "add_voice", "del_voice")
MESSAGES = ("Режим общения", "Сорт чая", "Выберите чай", "Выбор сделан")
ADMIN_MESSAGES = ("Нажмите на удаляемую кнопку либо отмените действие", "Напишите название либо отмените действие", "Напишите или перешлите текст", "Запишите или перешлите гс", "Вы точно хотите удалить информацию?")
keyboard_buttons = []

json1 = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Текстовые сообщения",
                "payload": "{\"type\": \"next\", \"but\": \"0\"}"
            },
            "color": "secondary"
        }
    ],
    [
        {
            "action": {
                "type": "callback",
                "label": "Голосовые сообщения",
                "payload": "{\"type\": \"next\", \"but\": \"1\"}"
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
json_admin1_entrance = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Текстовые сообщения",
                "payload": "{\"type\": \"next\", \"but\": \"0\"}"
            },
            "color": "secondary"
        }
    ], [
        {
            "action": {
                "type": "callback",
                "label": "Голосовые сообщения",
                "payload": "{\"type\": \"next\", \"but\": \"1\"}"
            },
            "color": "secondary"
        }
    ], [
        {
            "action": {
                "type": "open_link",
                "label": "Создатель бота",
                "link": "https://vk.com/az_projects",
            }
        }
    ], [
        {
            "action": {
                "type": "callback",
                "label": "Админ",
                "payload": "{\"type\": \"admin\"}"
            },
            "color": "primary"
        }
    ],
]
json_admin1_exit = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Далее",
                "payload": "{\"type\": \"next\", \"but\": \"0\"}"
            },
            "color": "secondary"
        }
    ], [
        {
            "action": {
                "type": "callback",
                "label": "Выйти из режима \"Админ\"",
                "payload": "{\"type\": \"admin\"}"
            },
            "color": "primary"
        }
    ],
]
json_admin2 = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Добавить кнопку",
                "payload": "{\"type\": \"add_butt\"}"
            },
            "color": "primary"
        }
    ], [
        {
            "action": {
                "type": "callback",
                "label": "Удалить кнопку",
                "payload": "{\"type\": \"del_butt\"}"
            },
            "color": "primary"
        }
    ]
]

json_admin3 = [
    [
        {
            "action": {
                "type": "callback",
                "label": "Добавить/Изменить текст",
                "payload": "{\"type\": \"add_text\"}"
            },
            "color": "primary"
        }
    ], [
        {
            "action": {
                "type": "callback",
                "label": "Удалить текст",
                "payload": "{\"type\": \"del_text\"}"
            },
            "color": "primary"
        }
    ], [
        {
            "action": {
                "type": "callback",
                "label": "Добавить/Изменить гс",
                "payload": "{\"type\": \"add_voice\"}"
            },
            "color": "primary"
        }
    ], [
        {
            "action": {
                "type": "callback",
                "label": "Удалить гс",
                "payload": "{\"type\": \"del_voice\"}"
            },
            "color": "primary"
        }
    ]
]
keyboard_buttons.append(json1.copy())
keyboard_buttons.append(json2.copy())
keyboard_buttons.append(json3.copy())
keyboard_buttons.append(json4.copy())

template_carousel = {
    "type": "carousel",
    "elements": []
}

template_kboard = {
    "inline": True,
    "buttons": []
}

cancel = {
    "inline": True,
    "buttons": [
        [
            {
                "action": {
                    "type": "callback",
                    "label": "Отмена",
                    "payload": "{\"type\": \"cancel\"}"
                },
                "color": "secondary"
            }
        ]
    ]
}

confirm = {
    "inline": True,
    "buttons": [
        [
            {
                "action": {
                    "type": "callback",
                    "label": "Отмена",
                    "payload": "{\"type\": \"cancel\"}"
                },
                "color": "secondary"
            }
        ], [
            {
                "action": {
                    "type": "callback",
                    "label": "Подтверждаю",
                    "payload": "{\"type\": \"confirm\"}"
                },
                "color": "secondary"
            }
        ]
    ]
}

