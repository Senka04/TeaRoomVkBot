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

# массив клавиатур
kboards = []
admin_kboards = []
ADMIN = None


def main():
    global kboards, admin_kboards, ADMIN

    state = read_admin_mode()

    # keyboard
    keyboard_base()
    members = vk1.groups.getMembers(group_id=GROUPID, filter="managers")
    for i in range(members['count']):
        if str(members['items'][i]['role']) == 'creator':
            ADMIN = members['items'][i]['id']
            break

    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.obj.message["text"] in ["Начать", "начать", "НАЧАТЬ"]:
                    message_id = take_last_message_id(user_id=event.obj.message["from_id"], t=True)
                    if message_id is not None and message_id != []:
                        message = vk1.messages.getById(message_ids=message_id)
                        timestamp = message['items'][0]['date']
                        now = time.time()
                        time_diff = now - timestamp
                        if time_diff < diff_timer:
                            for i in range(int(message['count'])):
                                try:
                                    vk1.messages.delete(message_ids=message_id[i], delete_for_all=1)
                                except vk_api.exceptions.ApiError as e:
                                    if e.code != 15 or e.error['error_msg'] != 'Access denied: message can not be found (3)':
                                        raise e
                    update_last_message_id(new_id=[], user_id=event.obj.message["from_id"], t=True)

                    if str(ADMIN) == str(event.obj.message["from_id"]):
                        send_message_new(event=event, pos=0, kboard=admin_kboards)
                    else:
                        send_message_new(event=event, pos=0, kboard=kboards)

                    update_position(0, event.obj.message["from_id"])
                else:
                    msgs = vk1.messages.getHistory(
                        user_id=event.obj.message["from_id"],
                        peer_id=event.obj.message["peer_id"],
                        count=100,
                    )

                    command_begin_flag = True
                    for m in range(len(msgs['items'])):
                        if msgs['items'][m]['text'] == MESSAGES[4]:
                            timestamp = msgs['items'][1]['date']
                            now = time.time()
                            time_diff = now - timestamp
                            if time_diff < diff_timer:
                                command_begin_flag = False

                    if command_begin_flag:
                        vk1.messages.send(
                            user_id=event.obj.message["from_id"],
                            random_id=get_random_id(),
                            peer_id=event.obj.message["peer_id"],
                            message=MESSAGES[4],
                        )
                    vk1.messages.send(
                        user_id=ADMIN,
                        forward_messages=event.obj.message["id"],
                        random_id=get_random_id()
                    )

            elif event.type == VkBotEventType.MESSAGE_EVENT:
                conversation_message_id = event.obj.get('conversation_message_id')
                message = vk1.messages.getByConversationMessageId(
                    peer_id=event.obj.peer_id,
                    conversation_message_ids=conversation_message_id
                )

                if list(message['items']):
                    message_id = message['items'][0]['id']
                else:
                    message_id = None

                if message_id in take_last_message_id(user_id=event.obj.user_id):
                    if event.obj.payload.get("type") == CALLBACK_MODES[0]:  # next
                        pos = int(take_position(event.obj.user_id))
                        update_prev_buttons(event.obj.user_id, pos+1, event.obj.payload.get("but"))
                        prev_but2 = take_prev_buttons(event.obj.user_id, 2)
                        prev_but3 = take_prev_buttons(event.obj.user_id, 3)
                        keyboard_base()
                        fill_keyboard(event.obj.user_id, 1)
                        fill_keyboard(event.obj.user_id, 2, prev_but2)
                        append_admin_butts123()

                        if pos == 2:
                            market_respose = vk2.market.get(owner_id=group_id, count=200, offset=0, extended=1)

                            items = market_respose['items']
                            titles = []
                            for item in items:
                                titles.append(item['title'])

                            counter = 0
                            att = take_text_or_voice(prev_but3)
                            new_last_message_ids = take_last_message_id(user_id=event.obj.user_id, t=True)

                            if att[0] is not None:
                                if str(event.obj.user_id) == str(ADMIN) and read_admin_mode() is True:
                                    new_last_message_id = vk1.messages.send(
                                        user_id=event.obj.user_id,
                                        random_id=get_random_id(),
                                        peer_id=event.obj.peer_id,
                                        attachment=att[0]
                                    )
                                    new_last_message_ids.append(new_last_message_id)
                                else:
                                    if int(take_prev_buttons(event.obj.user_id, 1)) == 1:
                                        new_last_message_id = vk1.messages.send(
                                            user_id=event.obj.user_id,
                                            random_id=get_random_id(),
                                            peer_id=event.obj.peer_id,
                                            attachment=att[0]
                                        )
                                        new_last_message_ids.append(new_last_message_id)
                                        for title in titles:
                                            if str(title) == str(event.obj.payload.get("label")):
                                                prod = items[counter]
                                                new_last_message_id = vk1.messages.send(
                                                    user_id=event.obj.user_id,
                                                    random_id=get_random_id(),
                                                    peer_id=event.obj.peer_id,
                                                    attachment=f"market{group_id}_{prod['id']}",
                                                )
                                                new_last_message_ids.append(new_last_message_id)
                                                break
                                            counter = counter + 1

                            if att[1] is not None:
                                if str(event.obj.user_id) == str(ADMIN) and read_admin_mode() is True:
                                    new_last_message_id = vk1.messages.send(
                                        user_id=event.obj.user_id,
                                        random_id=get_random_id(),
                                        peer_id=event.obj.peer_id,
                                        message=att[1]
                                    )
                                    new_last_message_ids.append(new_last_message_id)
                                else:
                                    if int(take_prev_buttons(event.obj.user_id, 1)) == 0:
                                        new_last_message_id = vk1.messages.send(
                                            user_id=event.obj.user_id,
                                            random_id=get_random_id(),
                                            peer_id=event.obj.peer_id,
                                            message=att[1]
                                        )
                                        new_last_message_ids.append(new_last_message_id)
                                        for title in titles:
                                            if str(title) == str(event.obj.payload.get("label")):
                                                prod = items[counter]
                                                new_last_message_id = vk1.messages.send(
                                                    user_id=event.obj.user_id,
                                                    random_id=get_random_id(),
                                                    peer_id=event.obj.peer_id,
                                                    attachment=f"market{group_id}_{prod['id']}",
                                                )
                                                new_last_message_ids.append(new_last_message_id)
                                                break
                                            counter = counter + 1

                            if str(ADMIN) == str(event.obj.user_id) and read_admin_mode() is True:
                                for title in titles:
                                    if str(title) == str(event.obj.payload.get("label")):
                                        prod = items[counter]
                                        new_last_message_id = vk1.messages.send(
                                            user_id=event.obj.user_id,
                                            random_id=get_random_id(),
                                            peer_id=event.obj.peer_id,
                                            attachment=f"market{group_id}_{prod['id']}",
                                        )
                                        new_last_message_ids.append(new_last_message_id)
                                        break
                                    counter = counter + 1
                            update_last_message_id(new_id=new_last_message_ids, user_id=event.obj.user_id, t=True)

                        if str(ADMIN) == str(event.obj.user_id) and read_admin_mode() is True:
                            send_message(event=event, pos=pos+1, kboard=admin_kboards)
                        else:
                            send_message(event=event, pos=pos+1, kboard=kboards)
                        update_position(pos+1, event.obj.user_id)

                    elif event.obj.payload.get("type") == CALLBACK_MODES[1]:  # back
                        pos = take_position(event.obj.user_id)
                        if pos == 3:
                            message_id = take_last_message_id(user_id=event.obj.user_id, t=True)
                            if message_id is not None and message_id != []:
                                message = vk1.messages.getById(message_ids=message_id)
                                timestamp = message['items'][0]['date']
                                now = time.time()
                                time_diff = now - timestamp

                                if time_diff < diff_timer:
                                    for i in range(int(message['count'])):
                                        try:
                                            vk1.messages.delete(message_ids=message_id[i], delete_for_all=1)
                                        except vk_api.exceptions.ApiError as e:
                                            if e.code != 15 or e.error['error_msg'] != 'Access denied: message can not be found (3)':
                                                raise e
                            update_last_message_id(new_id=[], user_id=event.obj.user_id, t=True)

                        newpos = pos-1
                        prev_but2 = take_prev_buttons(event.obj.user_id, 2)
                        keyboard_base()
                        fill_keyboard(event.obj.user_id, 1)
                        fill_keyboard(event.obj.user_id, 2, prev_but2)
                        append_admin_butts123()
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
                        send_message_cancel(event, 1)
                        pos = int(take_position(event.obj.user_id))
                        for event_add in longpoll.listen():
                            try:
                                if event_add.type == VkBotEventType.MESSAGE_EVENT:
                                    if event_add.obj.payload.get("type") == "cancel":
                                        send_message(event=event_add, pos=pos, kboard=admin_kboards)
                                        break
                                elif event_add.type == VkBotEventType.MESSAGE_NEW:
                                    if str(event_add.obj.message["text"]) != '':
                                        keyboard = take_buttons(pos)
                                        label = event_add.obj.message["text"]
                                        pb = take_prev_buttons(event.obj.user_id, pos)
                                        butts = []
                                        for n in range(len(keyboard)):
                                            butts.append(int(eval(keyboard[n][0]['action']['payload']).get("but")))
                                        b = add_missing_numbers(butts)
                                        new_butt = [
                                            {
                                                "action": {
                                                    "type": "callback",
                                                    "label": f"{label}",
                                                    "payload": f'{{\"type\": \"next\", \"prev_but\": \"{pb}\", \"but\": \"{b}\", \"text\": \"0\", \"voice\": \"0\", \"label\": \"{0}\"}}'
                                                },
                                                "color": "secondary"
                                            }
                                        ]
                                        lbl_write = eval(new_butt[0]['action']['payload'])
                                        lbl_write["label"] = str(label)
                                        new_butt[0]['action']['payload'] = json.dumps(lbl_write, ensure_ascii=False)

                                        if keyboard is None:
                                            keyboard = []
                                        if str(ADMIN) == str(event_add.obj.message["from_id"]) and read_admin_mode() is True:
                                            keyboard.append(new_butt)
                                            update_buttons(pos, keyboard)
                                            prev_but2 = take_prev_buttons(ADMIN, 2)
                                            keyboard_base()
                                            fill_keyboard(event.obj.user_id, 1)
                                            fill_keyboard(event.obj.user_id, 2, prev_but2)
                                            append_admin_butts123()
                                            send_message_new(event=event_add, pos=pos, kboard=admin_kboards)
                                            break

                            except vk_api.exceptions.ApiError as e:
                                if e.code != 912 or e.error['error_msg'] != 'This is a chat bot feature, change this status in settings':
                                    raise e

                    elif event.obj.payload.get("type") == CALLBACK_MODES[4]:  # del_butt
                        send_message_cancel(event, 0)
                        pos = int(take_position(event.obj.user_id))
                        break_flag = False
                        for event_del in longpoll.listen():
                            try:
                                if event_del.type == VkBotEventType.MESSAGE_EVENT:
                                    if event_del.obj.payload.get("type") == "cancel":
                                        send_message(event=event_del, pos=pos, kboard=admin_kboards)
                                        break
                                    if event_del.obj.payload.get("type") == CALLBACK_MODES[0]:
                                        keyboard1 = take_buttons(1)
                                        keyboard2 = take_buttons(2)
                                        butt1 = event_del.obj.payload.get("but")
                                        if pos == 1:
                                            copy = keyboard1.copy()
                                            for i in range(len(copy)-1, -1, -1):
                                                butt2 = eval(copy[i][0]['action']['payload']).get("but")
                                                if str(butt1) == str(butt2):
                                                    del keyboard1[i]
                                                    break_flag = True
                                                    break

                                            copy = keyboard2.copy()
                                            for i in range(len(copy)-1, -1, -1):
                                                if int(eval(copy[i][0]['action']['payload']).get("prev_but")) == int(butt1):
                                                    btn = int(eval(copy[i][0]['action']['payload']).get("but"))
                                                    break_flag = True
                                                    vc = take_text_or_voice(btn)[0]
                                                    txt = take_text_or_voice(btn)[1]
                                                    if vc is not None or txt is not None:
                                                        update_text_or_voice(button_number=btn, text_message='',
                                                                             voice_message='')
                                                    del keyboard2[i]

                                        if pos == 2:
                                            copy = keyboard2.copy()
                                            for i in range(len(copy)-1, -1, -1):
                                                butt2 = eval(copy[i][0]['action']['payload']).get("but")
                                                pb = int(eval(copy[i][0]['action']['payload']).get("prev_but"))
                                                if str(butt1) == str(butt2):
                                                    del keyboard2[i]
                                                    vc = take_text_or_voice(butt2)[0]
                                                    txt = take_text_or_voice(butt2)[1]
                                                    if vc is not None or txt is not None:
                                                        update_text_or_voice(button_number=butt2, text_message='',
                                                                             voice_message='')
                                                        p1 = eval(keyboard1[pb][0]['action']['payload'])
                                                        p1['voice'] = "0"
                                                        p1['text'] = "0"
                                                        keyboard1[pb][0]['action']['payload'] = json.dumps(p1, ensure_ascii=False)
                                                    break_flag = True
                                                    break

                                        update_buttons(1, keyboard1)
                                        update_buttons(2, keyboard2)
                                        prev_but2 = take_prev_buttons(event.obj.user_id, 2)
                                        keyboard_base()
                                        fill_keyboard(event.obj.user_id, 1)
                                        fill_keyboard(event.obj.user_id, 2, prev_but2)
                                        append_admin_butts123()
                                        send_message(event=event_del, pos=pos, kboard=admin_kboards)
                                        if break_flag is True:
                                            break

                            except vk_api.exceptions.ApiError as e:
                                if e.code != 912 or e.error['error_msg'] != 'This is a chat bot feature, change this status in settings':
                                    raise e

                    elif event.obj.payload.get("type") == CALLBACK_MODES[5]:  # add_text
                        send_message_cancel(event, 2)
                        pos = int(take_position(event.obj.user_id))
                        for event_add_text in longpoll.listen():
                            try:
                                if event_add_text.type == VkBotEventType.MESSAGE_EVENT:
                                    if event_add_text.obj.payload.get("type") == "cancel":
                                        send_message(event=event_add_text, pos=pos, kboard=admin_kboards)
                                        break
                                if event_add_text.type == VkBotEventType.MESSAGE_NEW:
                                    message = vk1.messages.getById(message_ids=event_add_text.obj.message["id"])['items'][0]
                                    if message['text'] != '':
                                        text = message['text']
                                        update_text_or_voice(button_number=take_prev_buttons(ADMIN, 3), text_message=text)
                                        change_text("1")
                                        vk1.messages.send(
                                            user_id=event_add_text.obj.message["from_id"],
                                            random_id=get_random_id(),
                                            peer_id=event_add_text.obj.message["peer_id"],
                                            message="Текстовое сообщение добавлено"
                                        )
                                        send_message_new(event=event_add_text, pos=pos, kboard=admin_kboards)
                                        break

                                    if message['fwd_messages']:
                                        if message['fwd_messages'][0]['text'] != '':
                                            text = message['fwd_messages'][0]['text']
                                            update_text_or_voice(button_number=take_prev_buttons(ADMIN, 3), text_message=text)
                                            change_text("1")
                                            vk1.messages.send(
                                                user_id=event_add_text.obj.message["from_id"],
                                                random_id=get_random_id(),
                                                peer_id=event_add_text.obj.message["peer_id"],
                                                message="Текстовое сообщение добавлено"
                                            )
                                            send_message_new(event=event_add_text, pos=pos, kboard=admin_kboards)
                                            break

                            except vk_api.exceptions.ApiError as e:
                                if e.code != 912 or e.error['error_msg'] != 'This is a chat bot feature, change this status in settings':
                                    raise e

                    elif event.obj.payload.get("type") == CALLBACK_MODES[6]:  # del_text
                        pos = int(take_position(event.obj.user_id))
                        send_message_confirm(event, 4)
                        for event_del_text in longpoll.listen():
                            try:
                                if event_del_text.type == VkBotEventType.MESSAGE_EVENT:
                                    if event_del_text.obj.payload.get("type") == "cancel":
                                        send_message(event=event_del_text, pos=pos, kboard=admin_kboards)
                                        break
                                    if event_del_text.obj.payload.get("type") == "confirm":
                                        txt_vc = take_text_or_voice(button_number=take_prev_buttons(ADMIN, 3))
                                        if txt_vc[1] is not None:
                                            update_text_or_voice(button_number=take_prev_buttons(ADMIN, 3), text_message='')
                                            change_text("0")
                                            vk1.messages.send(
                                                user_id=event.obj.user_id,
                                                random_id=get_random_id(),
                                                peer_id=event.obj.peer_id,
                                                message="Текстовое сообщение удалено"
                                            )
                                        else:
                                            vk1.messages.send(
                                                user_id=event.obj.user_id,
                                                random_id=get_random_id(),
                                                peer_id=event.obj.peer_id,
                                                message="Нет информации для удаления"
                                            )
                                        send_message(event=event, pos=pos, kboard=admin_kboards)
                                        break

                            except vk_api.exceptions.ApiError as e:
                                if e.code != 912 or e.error['error_msg'] != 'This is a chat bot feature, change this status in settings':
                                    raise e

                    elif event.obj.payload.get("type") == CALLBACK_MODES[7]:  # add_voice
                        send_message_cancel(event, 3)
                        pos = int(take_position(event.obj.user_id))
                        break_flag = False
                        for event_add_voice in longpoll.listen():
                            try:
                                if event_add_voice.type == VkBotEventType.MESSAGE_EVENT:
                                    if event_add_voice.obj.payload.get("type") == "cancel":
                                        send_message(event=event_add_voice, pos=pos, kboard=admin_kboards)
                                        break
                                if event_add_voice.type == VkBotEventType.MESSAGE_NEW:
                                    message = vk1.messages.getById(message_ids=event_add_voice.obj.message["id"])['items'][0]
                                    if message['attachments']:
                                        for attachment in message['attachments']:
                                            if attachment['type'] == 'audio_message':
                                                owner = attachment['audio_message']['owner_id']
                                                audio_id = attachment['audio_message']['id']
                                                access = attachment['audio_message']['access_key']
                                                att = f"doc{owner}_{audio_id}_{access}"
                                                update_text_or_voice(button_number=take_prev_buttons(ADMIN, 3),
                                                                     voice_message=att)
                                                change_voice("1")
                                                vk1.messages.send(
                                                    user_id=event_add_voice.obj.message["from_id"],
                                                    random_id=get_random_id(),
                                                    peer_id=event_add_voice.obj.message["peer_id"],
                                                    message="Голосовое сообщение добавлено"
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
                                                update_text_or_voice(button_number=take_prev_buttons(ADMIN, 3),
                                                                     voice_message=att)
                                                change_voice("1")
                                                vk1.messages.send(
                                                    user_id=event_add_voice.obj.message["from_id"],
                                                    random_id=get_random_id(),
                                                    peer_id=event_add_voice.obj.message["peer_id"],
                                                    message="Голосовое сообщение добавлено"
                                                )
                                                send_message_new(event=event_add_voice, pos=pos, kboard=admin_kboards)
                                                break_flag = True
                                                break

                                        if break_flag is True:
                                            break

                            except vk_api.exceptions.ApiError as e:
                                if e.code != 912 or e.error['error_msg'] != 'This is a chat bot feature, change this status in settings':
                                    raise e

                    elif event.obj.payload.get("type") == CALLBACK_MODES[8]:  # del_voice
                        pos = int(take_position(event.obj.user_id))
                        send_message_confirm(event, 4)
                        for event_del_voice in longpoll.listen():
                            try:
                                if event_del_voice.type == VkBotEventType.MESSAGE_EVENT:
                                    if event_del_voice.obj.payload.get("type") == "cancel":
                                        send_message(event=event_del_voice, pos=pos, kboard=admin_kboards)
                                        break
                                    if event_del_voice.obj.payload.get("type") == "confirm":
                                        txt_vc = take_text_or_voice(button_number=take_prev_buttons(ADMIN, 3))
                                        if txt_vc[0] is not None:
                                            update_text_or_voice(button_number=take_prev_buttons(ADMIN, 3), voice_message='')
                                            change_voice("0")
                                            vk1.messages.send(
                                                user_id=event.obj.user_id,
                                                random_id=get_random_id(),
                                                peer_id=event.obj.peer_id,
                                                message="Голосовое сообщение удалено"
                                            )
                                        else:
                                            vk1.messages.send(
                                                user_id=event.obj.user_id,
                                                random_id=get_random_id(),
                                                peer_id=event.obj.peer_id,
                                                message="Нет информации для удаления"
                                            )
                                        send_message(event=event, pos=pos, kboard=admin_kboards)
                                        break

                            except vk_api.exceptions.ApiError as e:
                                if e.code != 912 or e.error['error_msg'] != 'This is a chat bot feature, change this status in settings':
                                    raise e

                    elif event.obj.payload.get("type") == CALLBACK_MODES[9]:  # rename_butt
                        send_message_cancel(event, 5)
                        pos = int(take_position(event.obj.user_id))
                        break_flag = False
                        butt_pos = None
                        butt_name = None
                        keyboard1 = take_buttons(1)
                        keyboard2 = take_buttons(2)
                        for event_rename in longpoll.listen():
                            try:
                                if event_rename.type == VkBotEventType.MESSAGE_EVENT:
                                    if event_rename.obj.payload.get("type") == "cancel":
                                        send_message(event=event_rename, pos=pos, kboard=admin_kboards)
                                        break
                                    if event_rename.obj.payload.get("type") == CALLBACK_MODES[0]:
                                        butt1 = event_rename.obj.payload.get("but")
                                        if pos == 1:
                                            copy = keyboard1.copy()
                                            for i in range(len(copy)-1, -1, -1):
                                                butt2 = eval(copy[i][0]['action']['payload']).get("but")
                                                if str(butt1) == str(butt2):
                                                    butt_pos = i
                                                    break
                                        if pos == 2:
                                            copy = keyboard2.copy()
                                            for i in range(len(copy)-1, -1, -1):
                                                butt2 = eval(copy[i][0]['action']['payload']).get("but")
                                                if str(butt1) == str(butt2):
                                                    butt_pos = i
                                                    break

                                if event_rename.type == VkBotEventType.MESSAGE_NEW:
                                    message = vk1.messages.getById(message_ids=event_rename.obj.message["id"])['items'][0]
                                    if message['text'] != '':
                                        butt_name = message['text']

                                    if butt_pos is not None:
                                        if pos == 1:
                                            keyboard1[butt_pos][0]['action']['label'] = butt_name
                                            p1 = eval(keyboard1[butt_pos][0]['action']['payload'])
                                            p1['label'] = butt_name
                                            keyboard1[butt_pos][0]['action']['payload'] = json.dumps(p1,  ensure_ascii=False)
                                            update_buttons(1, keyboard1)
                                        elif pos == 2:
                                            keyboard2[butt_pos][0]['action']['label'] = butt_name
                                            p2 = eval(keyboard2[butt_pos][0]['action']['payload'])
                                            p2['label'] = butt_name
                                            keyboard2[butt_pos][0]['action']['payload'] = json.dumps(p2, ensure_ascii=False)
                                            update_buttons(2, keyboard2)

                                        keyboard_base()
                                        prev_but2 = take_prev_buttons(event.obj.user_id, 2)
                                        fill_keyboard(event.obj.user_id, 1)
                                        fill_keyboard(event.obj.user_id, 2, prev_but2)
                                        append_admin_butts123()
                                        send_message_new(event=event_rename, pos=pos, kboard=admin_kboards)
                                        break_flag = True

                                if break_flag is True:
                                    break
                            except vk_api.exceptions.ApiError as e:
                                if e.code != 912 or e.error['error_msg'] != 'This is a chat bot feature, change this status in settings':
                                    raise e

        except vk_api.exceptions.ApiError as e:
            if e.code != 912 or e.error['error_msg'] != 'This is a chat bot feature, change this status in settings':
                raise e


def add_missing_numbers(numbers):
    i = 0
    while i in numbers:
        i += 1
    return i


def update_text_or_voice(button_number, voice_message=None, text_message=None):
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS text_or_voice
                     (button_number INTEGER PRIMARY KEY,
                      voice_message TEXT,
                      text_message TEXT)''')

    c.execute("SELECT * FROM text_or_voice WHERE button_number=?", (button_number,))
    data = c.fetchone()

    if str(voice_message) == '' and str(text_message) == '':
        c.execute('DELETE FROM text_or_voice WHERE button_number = ?', (button_number,))

    if data is None:
        c.execute("INSERT INTO text_or_voice VALUES (?, ?, ?)", (button_number, voice_message, text_message))
    else:
        if voice_message is not None:
            c.execute("UPDATE text_or_voice SET voice_message=? WHERE button_number=?", (voice_message, button_number))
        if text_message is not None:
            c.execute("UPDATE text_or_voice SET text_message=? WHERE button_number=?", (text_message, button_number))

    conn.commit()
    conn.close()


def take_text_or_voice(button_number):
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
        voice_message = data[1] if data[1] != '' else None
        text_message = data[2] if data[2] != '' else None
        return voice_message, text_message


def change_voice(n: str):
    if n == "0" or n == "1":
        flag = False
        pb1 = take_prev_buttons(ADMIN, 2)
        pb2 = take_prev_buttons(ADMIN, 3)
        butts1 = take_buttons(1)
        butts2 = take_buttons(2)
        p1 = None
        p2 = None
        i1 = None
        i2 = None

        for i in range(len(butts1)):
            if str(pb1) == str(eval(butts1[i][0]['action']['payload']).get("but")):
                p1 = eval(butts1[i][0]['action']['payload'])
                i1 = i

        for i in range(len(butts2)):
            if str(pb2) == str(eval(butts2[i][0]['action']['payload']).get("but")):
                p2 = eval(butts2[i][0]['action']['payload'])
                i2 = i

        if p1 is not None and p2 is not None:
            p2['voice'] = n
            butts2[i2][0]['action']['payload'] = json.dumps(p2, ensure_ascii=False)
            update_buttons(2, butts2)

            for i in range(len(butts2)):
                if int(eval(butts2[i][0]['action']['payload']).get("voice")):
                    if str(pb1) == str(eval(butts2[i][0]['action']['payload']).get("prev_but")):
                        flag = True

            p1['voice'] = "1" if flag is True else "0"
            butts1[i1][0]['action']['payload'] = json.dumps(p1, ensure_ascii=False)
            update_buttons(1, butts1)


def change_text(n: str):
    if n == "0" or n == "1":
        flag = False
        pb1 = take_prev_buttons(ADMIN, 2)
        pb2 = take_prev_buttons(ADMIN, 3)
        butts1 = take_buttons(1)
        butts2 = take_buttons(2)
        p1 = None
        p2 = None
        i1 = None
        i2 = None

        for i in range(len(butts1)):
            if str(pb1) == str(eval(butts1[i][0]['action']['payload']).get("but")):
                p1 = eval(butts1[i][0]['action']['payload'])
                i1 = i

        for i in range(len(butts2)):
            if str(pb2) == str(eval(butts2[i][0]['action']['payload']).get("but")):
                p2 = eval(butts2[i][0]['action']['payload'])
                i2 = i

        if p1 is not None and p2 is not None:
            p2['text'] = n
            butts2[i2][0]['action']['payload'] = json.dumps(p2, ensure_ascii=False)
            update_buttons(2, butts2)

            for i in range(len(butts2)):
                if int(eval(butts2[i][0]['action']['payload']).get("text")):
                    if str(pb1) == str(eval(butts2[i][0]['action']['payload']).get("prev_but")):
                        flag = True

            p1['text'] = "1" if flag is True else "0"
            butts1[i1][0]['action']['payload'] = json.dumps(p1, ensure_ascii=False)
            update_buttons(1, butts1)


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


def fill_keyboard(user_id, pos: int, prev_but=-1):
    if pos == 1 or pos == 2:
        buttons_list = take_buttons(pos)
        for n in range(len(buttons_list)):
            prev_but_list = eval(buttons_list[n][0]['action']['payload']).get('prev_but')
            voice = eval(buttons_list[n][0]['action']['payload']).get('voice')
            text = eval(buttons_list[n][0]['action']['payload']).get('text')
            pb = take_prev_buttons(user_id, 1)
            if str(prev_but_list) == str(prev_but) or prev_but == -1:
                if str(user_id) != str(ADMIN) or read_admin_mode() is not True:
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


def append_admin_butts123():
    for i in range(len(json_admin2)):
        admin_kboards[1]['buttons'].append(json_admin2[i])
        admin_kboards[2]['buttons'].append(json_admin2[i])
    for i in range(len(json_admin3)):
        admin_kboards[3]['buttons'].append(json_admin3[i])


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


def update_last_message_id(new_id, user_id, t=False):  # t - table (False - keyboards, True - messages)
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    if t is True:
        c.execute('''CREATE TABLE IF NOT EXISTS messages2 (userid INTEGER PRIMARY KEY, LastMessageId TEXT)''')
        try:
            c.execute("SELECT * FROM messages2 WHERE userid = ?", (user_id,))
            row = c.fetchone()
            if row is None:
                c.execute("INSERT INTO messages2 (userid, LastMessageId) VALUES (?, ?)", (user_id, str(new_id)))
            else:
                c.execute("UPDATE messages2 SET LastMessageId = ? WHERE userid = ?", (str(new_id), user_id))
            conn.commit()
        finally:
            conn.close()
        return

    else:
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


def take_last_message_id(user_id, t=False):  # t - table (False - keyboards, True - messages)
    conn = sqlite3.connect('menu_positions.db')
    c = conn.cursor()
    if t is True:
        c.execute('''CREATE TABLE IF NOT EXISTS messages2 (userid INTEGER PRIMARY KEY, LastMessageId TEXT)''')
        try:
            c.execute("SELECT LastMessageId FROM messages2 WHERE userid = ?", (user_id,))
            row = c.fetchone()
            if row is None:
                return None
            else:
                return eval(row[0])
        finally:
            conn.close()

    else:
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
    message_id = take_last_message_id(user_id=event.obj.user_id)
    if message_id is not None:
        message = vk1.messages.getById(message_ids=message_id)
        timestamp = message['items'][0]['date']
        now = time.time()
        time_diff = now - timestamp

        if time_diff < diff_timer:
            for i in range(int(message['count'])):
                try:
                    vk1.messages.delete(message_ids=message_id[i], delete_for_all=1)
                except vk_api.exceptions.ApiError as e:
                    if e.code != 15 or e.error['error_msg'] != 'Access denied: message can not be found (3)':
                        raise e

    kboard_send = template_kboard.copy()
    for i in range(0, len(kboard[pos]['buttons']), 6):
        kboard_send['buttons'] = []
        for j in range(i, i+6, 1):
            if j < len(kboard[pos]['buttons']):
                kboard_send['buttons'].append(kboard[pos]['buttons'][j])

        if pos != 3:
            new_last_message_id = vk1.messages.send(
                user_id=event.obj.user_id,
                random_id=get_random_id(),
                peer_id=event.obj.peer_id,
                message=MESSAGES[pos],
                keyboard=json.dumps(kboard_send)
            )
        else:
            pb = take_prev_buttons(event.obj.user_id, 3)
            butts = take_buttons(2)
            lbl = MESSAGES[pos]
            for b in range(len(butts)):
                if int(eval(butts[b][0]['action']['payload']).get("but")) == int(pb):
                    lbl = str(eval(butts[b][0]['action']['payload']).get("label"))

            new_last_message_id = vk1.messages.send(
                user_id=event.obj.user_id,
                random_id=get_random_id(),
                peer_id=event.obj.peer_id,
                message=lbl,
                keyboard=json.dumps(kboard_send)
            )
        new_last_message_ids.append(new_last_message_id)

    update_last_message_id(new_id=new_last_message_ids, user_id=event.obj.user_id)
    vk1.messages.sendMessageEventAnswer(
        event_id=event.obj.event_id,
        user_id=event.obj.user_id,
        peer_id=event.obj.peer_id
    )


def send_message_cancel(event, mes):  # only for message_event
    new_last_message_ids = take_last_message_id(user_id=event.obj.user_id)
    new_last_message_id = vk1.messages.send(
        user_id=event.obj.user_id,
        random_id=get_random_id(),
        peer_id=event.obj.peer_id,
        message=ADMIN_MESSAGES[mes],
        keyboard=json.dumps(cancel)
    )
    new_last_message_ids.append(new_last_message_id)
    update_last_message_id(new_id=new_last_message_ids, user_id=event.obj.user_id)


def send_message_confirm(event, mes):  # only for message_event
    new_last_message_ids = take_last_message_id(user_id=event.obj.user_id)
    new_last_message_id = vk1.messages.send(
        user_id=event.obj.user_id,
        random_id=get_random_id(),
        peer_id=event.obj.peer_id,
        message=ADMIN_MESSAGES[mes],
        keyboard=json.dumps(confirm)
    )
    new_last_message_ids.append(new_last_message_id)
    update_last_message_id(new_id=new_last_message_ids, user_id=event.obj.user_id)


def send_message_new(event, pos, kboard):  # only for message_new
    new_last_message_ids = []
    message_id = take_last_message_id(user_id=event.obj.message["from_id"])
    if message_id is not None:
        message = vk1.messages.getById(message_ids=message_id)
        timestamp = message['items'][0]['date']
        now = time.time()
        time_diff = now - timestamp

        if time_diff < diff_timer:
            for i in range(int(message['count'])):
                try:
                    vk1.messages.delete(message_ids=message_id[i], delete_for_all=1)
                except vk_api.exceptions.ApiError as e:
                    if e.code != 15 or e.error['error_msg'] != 'Access denied: message can not be found (3)':
                        raise e

    kboard_send = template_kboard.copy()
    for i in range(0, len(kboard[pos]['buttons']), 6):
        kboard_send['buttons'] = []
        for j in range(i, i + 6, 1):
            if j < len(kboard[pos]['buttons']):
                kboard_send['buttons'].append(kboard[pos]['buttons'][j])

        if pos != 3:
            new_last_message_id = vk1.messages.send(
                user_id=event.obj.message["from_id"],
                random_id=get_random_id(),
                peer_id=event.obj.message["peer_id"],
                message=MESSAGES[pos],
                keyboard=json.dumps(kboard_send)
            )
        else:
            pb = take_prev_buttons(event.obj.message["from_id"], 3)
            butts = take_buttons(2)
            lbl = MESSAGES[pos]

            for b in range(len(butts)):
                if int(eval(butts[b][0]['action']['payload']).get("but")) == int(pb):
                    lbl = str(eval(butts[b][0]['action']['payload']).get("label"))

            new_last_message_id = vk1.messages.send(
                user_id=event.obj.message["from_id"],
                random_id=get_random_id(),
                peer_id=event.obj.message["peer_id"],
                message=lbl,
                keyboard=json.dumps(kboard_send)
            )

        new_last_message_ids.append(new_last_message_id)

    update_last_message_id(new_id=new_last_message_ids, user_id=event.obj.message["from_id"])


# keep_alive() #для деплоя

if __name__ == '__main__':
    main()
