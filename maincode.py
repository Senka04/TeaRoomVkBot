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
    keyboard_base()

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.message["text"] == "Начать":

                # market_respose = vk2.market.get(owner_id=group_id, count=100, offset=0, extended=1)
                # carousel = template_carousel.copy()
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
                print(event.obj.message)
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
                    pos = int(take_position(event.obj.user_id))
                    update_prev_buttons(event.obj.user_id, pos+1, event.obj.payload.get("but"))
                    prev_but2 = take_prev_buttons(event.obj.user_id, 2)
                    prev_but3 = take_prev_buttons(event.obj.user_id, 3)
                    keyboard_base()
                    fill_keyboard(event.obj.user_id, 1)
                    fill_keyboard(event.obj.user_id, 2, prev_but2)
                    if pos == 2:
                        att = take_text_or_voice(prev_but3, True, False)
                        txt = take_text_or_voice(prev_but3, False, True)
                        if att[0] is not None and int(take_prev_buttons(event.obj.user_id, 1)) != 0:
                            vk1.messages.send(
                                user_id=event.obj.user_id,
                                random_id=get_random_id(),
                                peer_id=event.obj.peer_id,
                                attachment=att[0]
                            )
                        if txt[1] is not None and int(take_prev_buttons(event.obj.user_id, 1)) != 1:
                            vk1.messages.send(
                                user_id=event.obj.user_id,
                                random_id=get_random_id(),
                                peer_id=event.obj.peer_id,
                                message=txt[1]
                            )
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
                            keyboard_base()
                        else:
                            keyboard_base()
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
                            keyboard = take_buttons(pos)
                            label = event_add.obj.message["text"]
                            b = len(keyboard)
                            pb = take_prev_buttons(event.obj.user_id, pos)
                            new_butt = [
                                {
                                    "action": {
                                        "type": "callback",
                                        "label": f"{label}",
                                        "payload": f'{{\"type\": \"next\", \"prev_but\": \"{pb}\", \"but\": \"{b}\", \"text\": \"0\", \"voice\": \"0\"}}'
                                    },
                                    "color": "secondary"
                                }
                            ]
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
                                butt1 = event_del.obj.payload.get("but")
                                for i in range(len(keyboard)):
                                    keyboard_copy = keyboard.copy()
                                    butt2 = eval(keyboard_copy[i][0]['action']['payload']).get("but")
                                    if str(butt1) == str(butt2):
                                        del keyboard[i]
                                        update_buttons(pos, keyboard)
                                        prev_but2 = take_prev_buttons(event.obj.user_id, 2)
                                        keyboard_base()
                                        fill_keyboard(event.obj.user_id, 1)
                                        fill_keyboard(event.obj.user_id, 2, prev_but2)
                                        send_message(event=event_del, pos=pos, kboard=admin_kboards)
                                        break_flag = True
                                        break
                                if break_flag is True:
                                    break

                elif event.obj.payload.get("type") == CALLBACK_MODES[7]:  # add_voice
                    pos = int(take_position(event.obj.user_id))
                    break_flag = False
                    for event_add_voice in longpoll.listen():
                        if event_add_voice.type == VkBotEventType.MESSAGE_NEW:
                            message = vk1.messages.getById(message_ids=event_add_voice.obj.message["id"])['items'][0]
                            if message['attachments']:
                                for attachment in message['attachments']:
                                    if attachment['type'] == 'audio_message':
                                        owner = attachment['audio_message']['owner_id']
                                        audio_id = attachment['audio_message']['id']
                                        access = attachment['audio_message']['access_key']
                                        att = f"doc{owner}_{audio_id}_{access}"
                                        change_voice("1")
                                        add_text_or_voice(button_number=take_prev_buttons(ADMIN, 3), voice_message=att)
                                        vk1.messages.send(
                                            user_id=event_add_voice.obj.message["from_id"],
                                            random_id=get_random_id(),
                                            peer_id=event_add_voice.obj.message["peer_id"],
                                            message="Добавлено"
                                        )
                                        send_message_new(event=event_add_voice, pos=pos, kboard=admin_kboards)
                                        break_flag = True
                                        break

                                if break_flag is True:
                                    break

                            if message['fwd_messages']:
                                for attachment in message['fwd_messages'][0]['attachments']:
                                    if attachment['type'] == 'audio_message':
                                        owner = attachment['audio_message']['owner_id']
                                        audio_id = attachment['audio_message']['id']
                                        access = attachment['audio_message']['access_key']
                                        att = f"doc{owner}_{audio_id}_{access}"
                                        change_voice("1")
                                        add_text_or_voice(button_number=take_prev_buttons(ADMIN, 3), voice_message=att)
                                        vk1.messages.send(
                                            user_id=event_add_voice.obj.message["from_id"],
                                            random_id=get_random_id(),
                                            peer_id=event_add_voice.obj.message["peer_id"],
                                            message="Добавлено"
                                        )
                                        send_message_new(event=event_add_voice, pos=pos, kboard=admin_kboards)
                                        break_flag = True
                                        break

                                if break_flag is True:
                                    break

                elif event.obj.payload.get("type") == CALLBACK_MODES[5]:  # add_text
                    pos = int(take_position(event.obj.user_id))
                    for event_add_text in longpoll.listen():
                        if event_add_text.type == VkBotEventType.MESSAGE_NEW:
                            message = vk1.messages.getById(message_ids=event_add_text.obj.message["id"])['items'][0]
                            if message['text'] != '':
                                text = message['text']
                                change_text("1")
                                add_text_or_voice(button_number=take_prev_buttons(ADMIN, 3), text_message=text)
                                vk1.messages.send(
                                    user_id=event_add_text.obj.message["from_id"],
                                    random_id=get_random_id(),
                                    peer_id=event_add_text.obj.message["peer_id"],
                                    message="Добавлено"
                                )
                                send_message_new(event=event_add_text, pos=pos, kboard=admin_kboards)
                                break

                            if message['fwd_messages']:
                                if message['fwd_messages'][0]['text'] != '':
                                    text = message['fwd_messages'][0]['text']
                                    change_text("1")
                                    add_text_or_voice(button_number=take_prev_buttons(ADMIN, 3), text_message=text)
                                    vk1.messages.send(
                                        user_id=event_add_text.obj.message["from_id"],
                                        random_id=get_random_id(),
                                        peer_id=event_add_text.obj.message["peer_id"],
                                        message="Добавлено"
                                    )
                                    send_message_new(event=event_add_text, pos=pos, kboard=admin_kboards)
                                    break


def add_text_or_voice(button_number, voice_message=None, text_message=None):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS text_or_voice
                     (button_number INTEGER PRIMARY KEY,
                      voice_message TEXT,
                      text_message TEXT)''')
    c.execute("SELECT * FROM text_or_voice WHERE button_number=?", (button_number,))
    data = c.fetchone()
    if data is None:
        c.execute("INSERT INTO text_or_voice VALUES (?, ?, ?)", (button_number, voice_message, text_message))
    else:
        if voice_message is not None:
            c.execute("UPDATE text_or_voice SET voice_message=? WHERE button_number=?", (voice_message, button_number))
        if text_message is not None:
            c.execute("UPDATE text_or_voice SET text_message=? WHERE button_number=?", (text_message, button_number))
    conn.commit()
    conn.close()


def take_text_or_voice(button_number, read_voice=True, read_text=True):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS text_or_voice
                     (button_number INTEGER PRIMARY KEY,
                      voice_message TEXT,
                      text_message TEXT)''')
    c.execute("SELECT * FROM text_or_voice WHERE button_number=?", (button_number,))
    data = c.fetchone()
    conn.close()
    if data is None:
        return None, None
    else:
        voice_message = data[1] if read_voice else None
        text_message = data[2] if read_text else None
        return voice_message, text_message


def change_voice(n: str):
    if n == "0" or n == "1":
        pb1 = take_prev_buttons(ADMIN, 2)
        pb2 = take_prev_buttons(ADMIN, 3)
        butts1 = take_buttons(1)
        butts2 = take_buttons(2)
        p1 = eval(butts1[pb1][0]['action']['payload'])
        p2 = eval(butts2[pb2][0]['action']['payload'])
        p1['voice'] = n
        p2['voice'] = n
        butts1[pb1][0]['action']['payload'] = json.dumps(p1)
        butts2[pb2][0]['action']['payload'] = json.dumps(p2)
        update_buttons(1, butts1)
        update_buttons(2, butts2)


def change_text(n: str):
    if n == "0" or n == "1":
        pb1 = take_prev_buttons(ADMIN, 2)
        pb2 = take_prev_buttons(ADMIN, 3)
        butts1 = take_buttons(1)
        butts2 = take_buttons(2)
        p1 = eval(butts1[pb1][0]['action']['payload'])
        p2 = eval(butts2[pb2][0]['action']['payload'])
        p1['text'] = n
        p2['text'] = n
        butts1[pb1][0]['action']['payload'] = json.dumps(p1)
        butts2[pb2][0]['action']['payload'] = json.dumps(p2)
        update_buttons(1, butts1)
        update_buttons(2, butts2)


def keyboard_base():
    global kboards, admin_kboards
    kboards = []
    admin_kboards = []
    for i in range(4):
        kboard1 = template_kboard.copy()
        kboard2 = template_kboard.copy()
        kboard1['buttons'] = keyboard_buttons[i].copy()
        kboards.append(kboard1)
        if i > 0:
            kboard2['buttons'] = keyboard_buttons[i].copy()
            admin_kboards.append(kboard2)
        else:
            kboard2['buttons'] = []
            if read_admin_mode() is True:
                for j in range(len(json_admin1_exit)):
                    kboard2['buttons'].append(json_admin1_exit[j])
            else:
                for j in range(len(json_admin1_entrance)):
                    kboard2['buttons'].append(json_admin1_entrance[j])
            admin_kboards.append(kboard2)

    for i in range(len(json_admin2)):
        admin_kboards[1]['buttons'].append(json_admin2[i])
        admin_kboards[2]['buttons'].append(json_admin2[i])
    for i in range(len(json_admin3)):
        admin_kboards[3]['buttons'].append(json_admin3[i])


def fill_keyboard(user_id, pos: int, prev_but=-1):
    if pos == 1 or pos == 2:
        buttons_list = take_buttons(pos)
        for n in range(len(buttons_list)):
            prev_but_list = eval(buttons_list[n][0]['action']['payload']).get('prev_but')
            voice = eval(buttons_list[n][0]['action']['payload']).get('voice')
            text = eval(buttons_list[n][0]['action']['payload']).get('text')
            pb = take_prev_buttons(user_id, 1)
            if str(prev_but_list) == str(prev_but) or prev_but == -1:
                if read_admin_mode() is not True:
                    if int(pb):
                        if int(voice):
                            admin_kboards[pos]['buttons'].append(buttons_list[n])
                            kboards[pos]['buttons'].append(buttons_list[n])
                    else:
                        if int(text):
                            admin_kboards[pos]['buttons'].append(buttons_list[n])
                            kboards[pos]['buttons'].append(buttons_list[n])
                else:
                    admin_kboards[pos]['buttons'].append(buttons_list[n])
                    kboards[pos]['buttons'].append(buttons_list[n])



def update_buttons(column, buttons):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS buttons (menu1 TEXT, menu2 TEXT)''')

    c.execute("SELECT COUNT(*) FROM buttons")
    row_count = c.fetchone()[0]

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
        return []
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


def update_prev_buttons(user_id, menu, but):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prev_buttons (userid INTEGER PRIMARY KEY, for_m1 INTEGER, for_m2 INTEGER, for_m3 INTEGER)''')
    try:
        c.execute("SELECT * FROM prev_buttons WHERE userid = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            if menu == 1:
                c.execute("INSERT INTO prev_buttons (userid, for_m1) VALUES (?, ?)", (user_id, but,))
            elif menu == 2:
                c.execute("INSERT INTO prev_buttons (userid, for_m2) VALUES (?, ?)", (user_id, but,))
            elif menu == 3:
                c.execute("INSERT INTO prev_buttons (userid, for_m3) VALUES (?, ?)", (user_id, but,))
        else:
            if menu == 1:
                c.execute("UPDATE prev_buttons SET for_m1 = ? WHERE userid = ?", (but, user_id))
            elif menu == 2:
                c.execute("UPDATE prev_buttons SET for_m2 = ? WHERE userid = ?", (but, user_id))
            elif menu == 3:
                c.execute("UPDATE prev_buttons SET for_m3 = ? WHERE userid = ?", (but, user_id))
        conn.commit()
    finally:
        conn.close()
    return


def take_prev_buttons(user_id, menu):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prev_buttons (userid INTEGER PRIMARY KEY, for_m1 INTEGER, for_m2 INTEGER,  for_m3 INTEGER)''')
    try:
        if menu == 1:
            c.execute("SELECT for_m1 FROM prev_buttons WHERE userid = ?", (user_id,))
        elif menu == 2:
            c.execute("SELECT for_m2 FROM prev_buttons WHERE userid = ?", (user_id,))
        elif menu == 3:
            c.execute("SELECT for_m3 FROM prev_buttons WHERE userid = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            return None
        else:
            return row[0]
    finally:
        conn.close()


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
