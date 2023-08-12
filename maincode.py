import json
import os
import vk_api
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from dotenv import load_dotenv

# from webserver import keep_alive #для деплоя

load_dotenv()
API_VERSION = "5.131"


CALLBACK_MODES = ("mode1", "mode2", "back")
group_id = '-'+str(os.environ.get("GROUPID"))
NOT_INLINE_KEYBOARD = ("shop", "keyboard_inline")


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


def main():
    vk_session1 = vk_api.VkApi(token=os.environ.get("BTOKEN"), api_version=API_VERSION)
    vk1 = vk_session1.get_api()
    longpoll = VkBotLongPoll(vk_session1, os.environ.get("GROUPID"))

    vk_session2 = vk_api.VkApi(token=os.environ.get("USERID"), api_version=API_VERSION)
    vk2 = vk_session2.get_api()

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

    keyboard_1 = VkKeyboard(inline=True)
    keyboard_1.add_callback_button(
        label="Текстовые сообщения",
        color=VkKeyboardColor.SECONDARY,
        payload={"type": "mode1"},
    )
    keyboard_1.add_line()
    keyboard_1.add_callback_button(
        label="Голосовые сообщения",
        color=VkKeyboardColor.SECONDARY,
        payload={"type": "mode2"},
    )

    keyboard_2 = VkKeyboard(inline=True)
    keyboard_2.add_callback_button(
        label="Назад",
        color=VkKeyboardColor.NEGATIVE,
        payload={"type": "back"},
    )
    keyboard_3 = VkKeyboard(inline=True)
    keyboard_3.add_callback_button(
        label="Товары",
        color=VkKeyboardColor.POSITIVE,
        payload={"type": "shop"},
    )
    keyboard_3.add_callback_button(
        label="Пообщаться",
        color=VkKeyboardColor.POSITIVE,
        payload={"type": "keyboard_inline"},
    )

    f_toggle: bool = False
    for event in longpoll.listen():

        if event.type == VkBotEventType.MESSAGE_NEW:
            if "callback" not in event.obj.client_info["button_actions"]:
                print(
                    f'Клиент user_id{event.obj.message["from_id"]} не поддерживает callback-кнопки.'
                )
            vk1.messages.send(
                user_id=event.obj.message["from_id"],
                random_id=get_random_id(),
                peer_id=event.obj.message["from_id"],
                message="Привет",
                keyboard=keyboard_3.get_keyboard(),
            )

        elif event.type == VkBotEventType.MESSAGE_EVENT:
            if event.obj.payload.get("type") == NOT_INLINE_KEYBOARD[0]:
                vk1.messages.send(
                    user_id=event.obj.user_id,
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id,
                    message="Товары",
                    template=json.dumps(carousel)
                )
                r = vk1.messages.sendMessageEventAnswer(
                    event_id=event.obj.event_id,
                    user_id=event.obj.user_id,
                    peer_id=event.obj.peer_id
                )
            elif event.obj.payload.get("type") == NOT_INLINE_KEYBOARD[1]:
                vk1.messages.send(
                    user_id=event.obj.user_id,
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id,
                    message="Режим общения",
                    keyboard=keyboard_1.get_keyboard(),
                )
                r = vk1.messages.sendMessageEventAnswer(
                    event_id=event.obj.event_id,
                    user_id=event.obj.user_id,
                    peer_id=event.obj.peer_id
                )
            elif event.obj.payload.get("type") in CALLBACK_MODES:
                mode = event.obj.payload.get("type")
                last_id = vk1.messages.edit(
                    peer_id=event.obj.peer_id,
                    message=("Режим общения" if f_toggle else "Понял, пишу" if mode == "mode1" else "Понял, говорю"),
                    conversation_message_id=event.obj.conversation_message_id,
                    keyboard=(keyboard_1 if f_toggle else keyboard_2).get_keyboard()
                )
                f_toggle = not f_toggle


# keep_alive() #для деплоя

if __name__ == '__main__':
    main()
