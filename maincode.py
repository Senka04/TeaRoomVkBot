import os
import json
import vk_api
import sqlite3
import time
from transliterate import slugify
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

added_butt_label = ""
added_butt_text = ""


def main():
    global carousel, kboards, admin_kboards, added_butt_label, added_butt_text

    state = read_admin_mode()
    market_respose = vk2.market.get(owner_id=group_id, count=100, offset=0, extended=1)
    response = vk1.groups.getById(group_id=GROUPID)

    # carousel
    carousel = template_carousel.copy()
    carousel['elements'] = []

    group_addr = response[0]['screen_name']
    items = market_respose['items']
    for item in items:
        element = create_element(item, group_addr)
        carousel['elements'].append(element)

    # keyboard
    create_keyboard()
            
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
                    send_message_new(event=event, pos=0, kboard=admin_kboards)
                else:
                    send_message_new(event=event, pos=0, kboard=kboards)

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
            if message_id in take_last_message_id(event.obj.user_id):
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

                elif event.obj.payload.get("type") == CALLBACK_MODES[3]:  # add_butt
                    send_message_cancel(event)
                    pos = int(take_position(event.obj.user_id))
                    for event_add in longpoll.listen():
                        if event_add.type == VkBotEventType.MESSAGE_EVENT:
                            if event_add.obj.payload.get("type") == "cancel":
                                send_message(event=event_add, pos=pos, kboard=admin_kboards)
                                break
                        elif event_add.type == VkBotEventType.MESSAGE_NEW:
                            added_butt_label = str(event_add.obj.message["text"])
                            added_butt_text = slugify(added_butt_label)
                            new_butt = [
                                {
                                    "action": {
                                        "type": "callback",
                                        "label": f"{added_butt_label}",
                                        "payload": f'{{\"type\": \"next\", \"text\": "{added_butt_text}"}}'
                                    },
                                    "color": "secondary"
                                }
                            ]
                            keyboard = take_buttons(pos)
                            if keyboard is None:
                                keyboard = []
                            if str(ADMIN) == str(event_add.obj.message["from_id"]) and read_admin_mode() is True:
                                kboards[pos]['buttons'].append(new_butt)
                                admin_kboards[pos]['buttons'].append(new_butt)
                                keyboard.append(new_butt)
                                update_buttons(pos, keyboard)
                                send_message_new(event=event_add, pos=pos, kboard=admin_kboards)
                                break

                elif event.obj.payload.get("type") == CALLBACK_MODES[4]:  # del_butt
                    send_message_cancel(event)
                    pos = int(take_position(event.obj.user_id))
                    break_flag = False
                    for event_del in longpoll.listen():
                        if event_del.type == VkBotEventType.MESSAGE_EVENT:
                            if event_del.obj.payload.get("type") == "cancel":
                                send_message(event=event_del, pos=pos, kboard=admin_kboards)
                                break
                            if event_del.obj.payload.get("type") == CALLBACK_MODES[0]:
                                keyboard = take_buttons(pos)
                                text1 = event_del.obj.payload.get("text")
                                for i in range(len(keyboard)):
                                    keyboard_copy = keyboard.copy()
                                    text2 = eval(keyboard_copy[i][0]['action']['payload']).get("text")
                                    if str(text1) == str(text2):
                                        del keyboard[i]
                                        update_buttons(pos, keyboard)
                                        create_keyboard()
                                        send_message(event=event_del, pos=pos, kboard=admin_kboards)
                                        break_flag = True
                                        break
                                if break_flag is True:
                                    break


def create_keyboard():
    global kboards, admin_kboards
    kboards = []
    admin_kboards = []
    for i in range(4):
        kboard1 = template_kboard.copy()
        kboard2 = template_kboard.copy()
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

    buttons = take_buttons(1)
    if buttons is not None:
        for i in range(len(buttons)):
            kboards[1]['buttons'].append(buttons[i])
            admin_kboards[1]['buttons'].append(buttons[i])

    buttons = take_buttons(2)
    if buttons is not None:
        for i in range(len(buttons)):
            kboards[2]['buttons'].append(buttons[i])
            admin_kboards[2]['buttons'].append(buttons[i])


def update_buttons(column, buttons):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS buttons (menu1 TEXT, menu2 TEXT)''')

    c.execute("SELECT COUNT(*) FROM buttons")
    row_count = c.fetchone()[0]

    # Вставка новой строки, если таблица пуста
    if row_count == 0:
        c.execute("INSERT INTO buttons (menu1, menu2) VALUES ('', '')")

    if column == 1:
        c.execute("UPDATE buttons SET menu1 = ? WHERE rowid=1", (str(buttons),))
    elif column == 2:
        c.execute("UPDATE buttons SET menu2 = ? WHERE rowid=1", (str(buttons),))
    conn.commit()
    conn.close()


def take_buttons(column):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS buttons (menu1 TEXT, menu2 TEXT)''')
    if column == 1:
        c.execute("SELECT menu1 FROM buttons WHERE rowid=1")
    elif column == 2:
        c.execute("SELECT menu2 FROM buttons WHERE rowid=1")
    else:
        return
    data = c.fetchone()
    conn.close()
    if data is None or data[0] == '':
        return None
    else:
        return eval(data[0])


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
    c.execute('''CREATE TABLE IF NOT EXISTS messages (userid INTEGER PRIMARY KEY, LastMessageId TEXT)''')
    try:
        c.execute("SELECT * FROM messages WHERE userid = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            c.execute("INSERT INTO messages (userid, LastMessageId) VALUES (?, ?)", (user_id, str(new_id)))
        else:
            c.execute("UPDATE messages SET LastMessageId = ? WHERE userid = ?", (str(new_id), user_id))
        conn.commit()
    finally:
        conn.close()
    return


def take_last_message_id(user_id):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (userid INTEGER PRIMARY KEY, LastMessageId TEXT)''')
    try:
        c.execute("SELECT LastMessageId FROM messages WHERE userid = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            return None
        else:
            return eval(row[0])
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
    c.execute('''CREATE TABLE IF NOT EXISTS admin (state INTEGER)''')
    c.execute("SELECT state FROM admin WHERE rowid=1")
    data = c.fetchone()
    conn.close()

    if data is None:
        return None
    else:
        return True if data[0] else False


def send_message(event, pos, kboard):  # only for message_event
    new_last_message_ids = []
    message_id = take_last_message_id(event.obj.user_id)
    if message_id is not None:
        message = vk1.messages.getById(message_ids=message_id)
        timestamp = message['items'][0]['date']
        now = time.time()
        time_diff = now - timestamp

        if time_diff < 24 * 60 * 60:
            vk1.messages.delete(message_ids=message_id, delete_for_all=1)

    kboard_send = template_kboard.copy()
    for i in range(0, len(kboard[pos]['buttons']), 6):
        kboard_send['buttons'] = []
        for j in range(i, i+6, 1):
            if j < len(kboard[pos]['buttons']):
                kboard_send['buttons'].append(kboard[pos]['buttons'][j])
        new_last_message_id = vk1.messages.send(
            user_id=event.obj.user_id,
            random_id=get_random_id(),
            peer_id=event.obj.peer_id,
            message=MESSAGES[pos],
            keyboard=json.dumps(kboard_send)
        )
        new_last_message_ids.append(new_last_message_id)

    update_last_message_id(new_last_message_ids, event.obj.user_id)
    vk1.messages.sendMessageEventAnswer(
        event_id=event.obj.event_id,
        user_id=event.obj.user_id,
        peer_id=event.obj.peer_id
    )


def send_message_cancel(event):  # only for message_event
    new_last_message_ids = take_last_message_id(event.obj.user_id)
    new_last_message_id = vk1.messages.send(
        user_id=event.obj.user_id,
        random_id=get_random_id(),
        peer_id=event.obj.peer_id,
        message="Напишите название добавляемой кнопки либо отмените действие",
        keyboard=json.dumps(cancel)
    )
    new_last_message_ids.append(new_last_message_id)
    update_last_message_id(new_last_message_ids, event.obj.user_id)


def send_message_new(event, pos, kboard):  # only for message_new
    new_last_message_ids = []
    message_id = take_last_message_id(event.obj.message["from_id"])
    if message_id is not None:
        message = vk1.messages.getById(message_ids=message_id)
        timestamp = message['items'][0]['date']
        now = time.time()
        time_diff = now - timestamp

        if time_diff < 24 * 60 * 60:
            vk1.messages.delete(message_ids=message_id, delete_for_all=1)

    kboard_send = template_kboard.copy()
    for i in range(0, len(kboard[pos]['buttons']), 6):
        kboard_send['buttons'] = []
        for j in range(i, i + 6, 1):
            if j < len(kboard[pos]['buttons']):
                kboard_send['buttons'].append(kboard[pos]['buttons'][j])
        new_last_message_id = vk1.messages.send(
            user_id=event.obj.message["from_id"],
            random_id=get_random_id(),
            peer_id=event.obj.message["peer_id"],
            message=MESSAGES[pos],
            keyboard=json.dumps(kboard_send)
        )
        new_last_message_ids.append(new_last_message_id)

    update_last_message_id(new_last_message_ids, event.obj.message["from_id"])


# keep_alive() #для деплоя

if __name__ == '__main__':
    main()
