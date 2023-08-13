import json
import vk_api
import sqlite3
from config import *
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
# from webserver import keep_alive  # для деплоя

# vk
vk_session1 = vk_api.VkApi(token=os.environ.get("BTOKEN"), api_version=API_VERSION)
vk1 = vk_session1.get_api()
longpoll = VkBotLongPoll(vk_session1, os.environ.get("GROUPID"))

vk_session2 = vk_api.VkApi(token=os.environ.get("USERID"), api_version=API_VERSION)
vk2 = vk_session2.get_api()

# keyboards
kboards = []
for i in range(4):
    keyboard = VkKeyboard(inline=True)
    kboards.append(keyboard)

# carousel
carousel = ''

# message
last_message_id = 0


def main():
    global kboards, carousel, last_message_id

    market_respose = vk2.market.get(owner_id=group_id, count=100, offset=0, extended=1)
    response = vk1.groups.getById(group_id=os.environ.get("GROUPID"))

    with open('carousel_1.json', 'r', encoding='UTF-8') as f:
        template = json.load(f)

    carousel = template.copy()
    carousel['elements'] = []

    group_addr = response[0]['screen_name']
    items = market_respose['items']
    for item in items:
        element = create_element(item, group_addr)
        carousel['elements'].append(element)

    kboards[0].add_callback_button(
        label="Текстовые сообщения",
        color=VkKeyboardColor.SECONDARY,
        payload={"type": "menu1"},
    )
    kboards[0].add_line()
    kboards[0].add_callback_button(
        label="Голосовые сообщения",
        color=VkKeyboardColor.SECONDARY,
        payload={"type": "menu1"},
    )

    kboards[1].add_callback_button(
        label="Улуны",
        color=VkKeyboardColor.SECONDARY,
        payload={"type": "menu2"},
    )
    kboards[1].add_line()
    kboards[1].add_callback_button(
        label="Назад",
        color=VkKeyboardColor.NEGATIVE,
        payload={"type": "back"},
    )

    kboards[2].add_callback_button(
        label="Те Гуань Инь",
        color=VkKeyboardColor.SECONDARY,
        payload={"type": "menu3"},
    )
    kboards[2].add_line()
    kboards[2].add_callback_button(
        label="Назад",
        color=VkKeyboardColor.NEGATIVE,
        payload={"type": "back"},
    )

    kboards[3].add_callback_button(
        label="Назад",
        color=VkKeyboardColor.NEGATIVE,
        payload={"type": "back"},
    )

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.message["text"] == "Начать":
                history = vk1.messages.getHistory(peer_id=event.obj.message["from_id"])
                messages_with_keyboard = [message for message in history['items'] if 'keyboard' in message]
                for message in messages_with_keyboard:
                    vk1.messages.delete(
                        message_ids=message['id'],
                        delete_for_all=1
                    )

                last_message_id = vk1.messages.send(
                    user_id=event.obj.message["from_id"],
                    random_id=get_random_id(),
                    peer_id=event.obj.message["peer_id"],
                    message=MESSAGES[0],
                    keyboard=kboards[0].get_keyboard(),
                )
                update_position(0, event.obj.message["from_id"])
            else:
                vk1.messages.send(
                    user_id=event.obj.message["from_id"],
                    random_id=get_random_id(),
                    peer_id=event.obj.message["from_id"],
                    message="Чтобы вернуться в начало меню, напишите \"Начать\"",
                )

        elif event.type == VkBotEventType.MESSAGE_EVENT:
            if event.obj.payload.get("type") == CALLBACK_MODES[0]:  # menu1
                send_message(event=event, pos=1)
                update_position(1, event.obj.user_id)

            elif event.obj.payload.get("type") == CALLBACK_MODES[1]:  # menu2
                send_message(event=event, pos=2)
                update_position(2, event.obj.user_id)

            elif event.obj.payload.get("type") == CALLBACK_MODES[2]:  # menu3
                send_message(event=event, pos=3)
                update_position(3, event.obj.user_id)

            elif event.obj.payload.get("type") == CALLBACK_MODES[3]:  # back
                newpos = take_position(event.obj.user_id)-1
                send_message(event=event, pos=newpos)
                update_position(newpos, event.obj.user_id)


def create_element(item, group_addr):
    photos = item['photos']
    photo_id = str(item['owner_id']) + '_' + str(photos[0]['id'])

    product = item['id']
    product_id = str(group_id)+'_'+str(product)

    title = str(item['title'])+'\n'+str(item['price']['text'])
    description = item['description']
    if len(description) > 80:
        description = description[:77] + '...'
    if len(title) > 80:
        title = title[:77] + '...'
    element = {
        'photo_id': f"{photo_id}",
        'action': {
            'type': 'open_photo'
        },
        'title': title,
        'description': description,
        'buttons': [{
            'action': {
                'type': 'open_link',
                'link': f"https://vk.com/{group_addr}?w=product{product_id}",
                'label': 'К товару',
                'payload': '{}'
            }
        }, {
            'action': {
                'type': 'open_link',
                'link': f"https://vk.com/market{group_id}?screen=market_item",
                'label': 'В магазин',
                'payload': '{}'
            }
        }]
    }
    return element


def update_position(new_pos, user_id):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (userid INTEGER PRIMARY KEY, position INTEGER)''')
    try:
        c.execute("SELECT * FROM users WHERE userid = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            c.execute("INSERT INTO users (userid, position) VALUES (?, ?)", (user_id, new_pos))
        else:
            c.execute("UPDATE users SET position = ? WHERE userid = ?", (new_pos, user_id))
        conn.commit()
    finally:
        conn.close()
    return


def take_position(user_id):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (userid INTEGER PRIMARY KEY, position INTEGER)''')
    try:
        c.execute("SELECT position FROM users WHERE userid = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            return None
        else:
            return row[0]
    finally:
        conn.close()


def send_message(event, pos):  # only for message_event
    global last_message_id
    vk1.messages.delete(
        message_ids=last_message_id,
        delete_for_all=1
    )

    last_message_id = vk1.messages.send(
        user_id=event.obj.user_id,
        random_id=get_random_id(),
        peer_id=event.obj.peer_id,
        message=MESSAGES[pos],
        keyboard=kboards[pos].get_keyboard(),
    )

    vk1.messages.sendMessageEventAnswer(
        event_id=event.obj.event_id,
        user_id=event.obj.user_id,
        peer_id=event.obj.peer_id
    )


# keep_alive() #для деплоя

if __name__ == '__main__':
    main()
