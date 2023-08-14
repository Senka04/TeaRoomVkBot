import os
import json
import vk_api
import sqlite3
from config import *
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
# from vk_api.keyboard import VkKeyboard, VkKeyboardColor
# from webserver import keep_alive  # для деплоя

# vk
vk_session1 = vk_api.VkApi(token=os.environ.get("BTOKEN"), api_version=API_VERSION)
vk1 = vk_session1.get_api()
longpoll = VkBotLongPoll(vk_session1, GROUPID)

vk_session2 = vk_api.VkApi(token=os.environ.get("USERID"), api_version=API_VERSION)
vk2 = vk_session2.get_api()

# carousel
carousel = ''

# message
last_message_id = 0

# массив клавиатур
kboards = []


def main():
    global carousel, last_message_id

    market_respose = vk2.market.get(owner_id=group_id, count=100, offset=0, extended=1)
    response = vk1.groups.getById(group_id=GROUPID)

    # carousel

    with open('carousel.json', 'r', encoding='UTF-8') as f:
        template = json.load(f)

    carousel = template.copy()
    carousel['elements'] = []

    group_addr = response[0]['screen_name']
    items = market_respose['items']
    for item in items:
        element = create_element(item, group_addr)
        carousel['elements'].append(element)

    # keyboards
    with open('keyboard.json', 'r', encoding='UTF-8') as f:
        template1 = json.load(f)

    for i in range(4):
        kboard = template1.copy()
        kboard['buttons'] = keyboard_buttons[i]
        kboards.append(kboard)

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.message["text"] == "Начать":
                history = vk1.messages.getHistory(peer_id=event.obj.message["peer_id"])
                messages_with_keyboard = [message for message in history['items'] if 'keyboard' in message]
                for message in messages_with_keyboard:
                    vk1.messages.delete(
                        message_ids=message['id'],
                        delete_for_all=1
                    )
                if str(ADMIN) == str(event.obj.message["from_id"]):
                    kb_len = len(kboards[0]['buttons'])
                    if kb_len == len(json1):
                        kboards[0]['buttons'].append(json_admin)

                market_respose = vk2.market.get(owner_id=group_id, count=100, offset=0, extended=1)
                carousel = template.copy()
                carousel['elements'] = []

                group_addr = response[0]['screen_name']
                items = market_respose['items']
                for item in items:
                    element = create_element(item, group_addr)
                    carousel['elements'].append(element)
                vk1.messages.send(
                    user_id=event.obj.message["from_id"],
                    random_id=get_random_id(),
                    peer_id=event.obj.message["peer_id"],
                    message="товары",
                    template=json.dumps(carousel),
                )
                last_message_id = vk1.messages.send(
                    user_id=event.obj.message["from_id"],
                    random_id=get_random_id(),
                    peer_id=event.obj.message["peer_id"],
                    message=MESSAGES[0],
                    keyboard=json.dumps(kboards[0]),
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

            elif event.obj.payload.get("type") == CALLBACK_MODES[4]:  # admin0
                send_message(event=event, pos=0)
                update_position(0, event.obj.user_id)


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
        keyboard=json.dumps(kboards[pos])
    )

    vk1.messages.sendMessageEventAnswer(
        event_id=event.obj.event_id,
        user_id=event.obj.user_id,
        peer_id=event.obj.peer_id
    )


def save_keyboard(id, data):
    with open(f'keyboard_{id}.json', 'w', encoding='UTF-8') as f:
        json.dump(data, f)


def load_keyboard(id):
    try:
        with open(f'keyboard_{id}.json', 'r', encoding='UTF-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# keep_alive() #для деплоя

if __name__ == '__main__':
    main()
