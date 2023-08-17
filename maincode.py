import os
import json
import vk_api
import sqlite3
import time
from config import *
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
# from webserver import keep_alive  # для деплоя

# vk
vk_session1 = vk_api.VkApi(token=os.environ.get("BTOKEN"), api_version=API_VERSION)
vk1 = vk_session1.get_api()
longpoll = VkBotLongPoll(vk_session1, GROUPID)

vk_session2 = vk_api.VkApi(token=os.environ.get("USERID"), api_version=API_VERSION)
vk2 = vk_session2.get_api()

# carousel
carousel = ''

# массив клавиатур
kboards = []
admin_kboards = []


def main():
    state = False
    global carousel, kboards, admin_kboards

    market_respose = vk2.market.get(owner_id=group_id, count=100, offset=0, extended=1)
    response = vk1.groups.getById(group_id=GROUPID)

    # carousel
    try:
        with open('carousel.json', 'r', encoding='UTF-8') as f:
            template = json.load(f)
    except FileNotFoundError:
        return None

    carousel = template.copy()
    carousel['elements'] = []

    group_addr = response[0]['screen_name']
    items = market_respose['items']
    for item in items:
        element = create_element(item, group_addr)
        carousel['elements'].append(element)

    # keyboards
    try:
        with open('keyboard.json', 'r', encoding='UTF-8') as f:
            template1 = json.load(f)
    except FileNotFoundError:
        return None

    for i in range(4):
        kboard1 = template1.copy()
        kboard2 = template1.copy()
        kboard1['buttons'] = keyboard_buttons[i].copy()
        kboard2['buttons'] = keyboard_buttons[i].copy()
        kboards.append(kboard1)
        admin_kboards.append(kboard2)

    if read_admin_mode() is True:
        for i in range(len(json_admin1_exit)):
            admin_kboards[0]['buttons'].append(json_admin1_exit[i])
    else:
        for i in range(len(json_admin1_entrance)):
            admin_kboards[0]['buttons'].append(json_admin1_entrance[i])

    for i in range(len(json_admin2)):
        admin_kboards[1]['buttons'].append(json_admin2[i])
        admin_kboards[2]['buttons'].append(json_admin2[i])
    for i in range(len(json_admin3)):
        admin_kboards[3]['buttons'].append(json_admin3[i])

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.message["text"] == "Начать":

                # market_respose = vk2.market.get(owner_id=group_id, count=100, offset=0, extended=1)
                # carousel = template.copy()
                # carousel['elements'] = []
                #
                # group_addr = response[0]['screen_name']
                # items = market_respose['items']
                # for item in items:
                #     element = create_element(item, group_addr)
                #     carousel['elements'].append(element)
                # vk1.messages.send(
                #     user_id=event.obj.message["from_id"],
                #     random_id=get_random_id(),
                #     peer_id=event.obj.message["peer_id"],
                #     message="товары",
                #     template=json.dumps(carousel),
                # )
                if str(ADMIN) == str(event.obj.message["from_id"]):
                    new_last_message_id = vk1.messages.send(
                        user_id=event.obj.message["from_id"],
                        random_id=get_random_id(),
                        peer_id=event.obj.message["peer_id"],
                        message=MESSAGES[0],
                        keyboard=json.dumps(admin_kboards[0]),
                    )
                else:
                    new_last_message_id = vk1.messages.send(
                        user_id=event.obj.message["from_id"],
                        random_id=get_random_id(),
                        peer_id=event.obj.message["peer_id"],
                        message=MESSAGES[0],
                        keyboard=json.dumps(kboards[0]),
                    )
                update_last_message_id(new_last_message_id, event.obj.message["from_id"])
                update_position(0, event.obj.message["from_id"])
            else:
                vk1.messages.send(
                    user_id=event.obj.message["from_id"],
                    random_id=get_random_id(),
                    peer_id=event.obj.message["peer_id"],
                    message="Отправьте сообщение: \"Начать\"",
                )

        elif event.type == VkBotEventType.MESSAGE_EVENT:
            conversation_message_id = event.obj.get('conversation_message_id')
            message = vk1.messages.getByConversationMessageId(
                peer_id=event.obj.peer_id,
                conversation_message_ids=conversation_message_id
            )
            message_id = message['items'][0]['id']
            if message_id == take_last_message_id(event.obj.user_id):
                if event.obj.payload.get("type") == CALLBACK_MODES[0]:  # next
                    pos = take_position(event.obj.user_id)
                    if str(ADMIN) == str(event.obj.user_id) and read_admin_mode() is True:
                        send_message(event=event, pos=pos+1, kboard=admin_kboards)
                    else:
                        send_message(event=event, pos=pos+1, kboard=kboards)
                    update_position(pos+1, event.obj.user_id)

                elif event.obj.payload.get("type") == CALLBACK_MODES[1]:  # back
                    newpos = take_position(event.obj.user_id)-1
                    if str(ADMIN) == str(event.obj.user_id) and (read_admin_mode() is True or newpos == 0):
                        send_message(event=event, pos=newpos, kboard=admin_kboards)
                    else:
                        send_message(event=event, pos=newpos, kboard=kboards)
                    update_position(newpos, event.obj.user_id)

                elif event.obj.payload.get("type") == CALLBACK_MODES[2]:  # admin
                    if str(ADMIN) == str(event.obj.user_id):
                        state = not state
                        update_admin_mode(state)
                        if state:
                            admin_kboards[0]['buttons'][3] = json_admin1_exit[0]
                        else:
                            admin_kboards[0]['buttons'][3] = json_admin1_entrance[0]
                        send_message(event=event, pos=0, kboard=admin_kboards)
                    else:
                        send_message(event=event, pos=0, kboard=kboards)
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


def update_last_message_id(new_id, user_id):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (userid INTEGER PRIMARY KEY, LastMessageId INTEGER)''')
    try:
        c.execute("SELECT * FROM messages WHERE userid = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            c.execute("INSERT INTO messages (userid, LastMessageId) VALUES (?, ?)", (user_id, new_id))
        else:
            c.execute("UPDATE messages SET LastMessageId = ? WHERE userid = ?", (new_id, user_id))
        conn.commit()
    finally:
        conn.close()
    return


def take_last_message_id(user_id):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (userid INTEGER PRIMARY KEY, LastMessageId INTEGER)''')
    try:
        c.execute("SELECT LastMessageId FROM messages WHERE userid = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            return None
        else:
            return row[0]
    finally:
        conn.close()


def update_admin_mode(state):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admin (state INTEGER)''')
    c.execute("INSERT OR REPLACE INTO admin (rowid, state) VALUES (1, ?)", (state,))
    conn.commit()
    conn.close()


def read_admin_mode():
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute("SELECT state FROM admin WHERE rowid=1")
    data = c.fetchone()
    conn.close()

    if data is None:
        return None
    else:
        return True if data[0] else False


def send_message(event, pos, kboard):  # only for message_event
    message_id = take_last_message_id(event.obj.user_id)
    if message_id:
        message = vk1.messages.getById(message_ids=message_id)
        timestamp = message['items'][0]['date']
        now = time.time()
        time_diff = now - timestamp

        if time_diff < 24 * 60 * 60:
            vk1.messages.delete(message_ids=message_id, delete_for_all=1)

    new_last_message_id = vk1.messages.send(
        user_id=event.obj.user_id,
        random_id=get_random_id(),
        peer_id=event.obj.peer_id,
        message=MESSAGES[pos],
        keyboard=json.dumps(kboard[pos])
    )
    update_last_message_id(new_last_message_id, event.obj.user_id)
    vk1.messages.sendMessageEventAnswer(
        event_id=event.obj.event_id,
        user_id=event.obj.user_id,
        peer_id=event.obj.peer_id
    )


def save_keyboard(n, data):
    with open(f'keyboard_{n}.json', 'w', encoding='UTF-8') as f:
        json.dump(data, f)


def load_keyboard(n):
    try:
        with open(f'keyboard_{n}.json', 'r', encoding='UTF-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# keep_alive() #для деплоя

if __name__ == '__main__':
    main()
