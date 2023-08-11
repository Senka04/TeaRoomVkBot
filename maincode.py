import os
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from dotenv import load_dotenv
load_dotenv()

#from webserver import keep_alive #для деплоя

# Запуск в SHELL: gunicorn --bind 0.0.0.0:8000 maincode:app
# Команда для поиска запущенных gunicorn: ps aux | grep gunicorn
# kill <4значный код> - остановка запущенного gunicorn

def main():

    vk_session = vk_api.VkApi(token=os.environ.get("BTOKEN"))

    longpoll = VkBotLongPoll(vk_session, os.environ.get("GROUPID"))

    for event in longpoll.listen():

        if event.type == VkBotEventType.MESSAGE_NEW:
            print('Новое сообщение:')

            print('Для меня от: ', end='')

            print(event.obj.message['from_id'])

            print('Текст:', event.obj.message['text'])
            print()

        elif event.type == VkBotEventType.MESSAGE_REPLY:
            print('Новое сообщение:')

            print('От меня для: ', end='')

            print(event.obj.peer_id)

            print('Текст:', event.obj.text)
            print()

        elif event.type == VkBotEventType.MESSAGE_TYPING_STATE:
            print('Печатает ', end='')

            print(event.obj.from_id, end=' ')

            print('для ', end='')

            print(event.obj.to_id)
            print()

        else:
            print(event.type)
            print()


if __name__ == '__main__':
    main()

#keep_alive() #для деплоя