import os

import telebot
from setting import Setting
from df_methods import get_lesson, get_lesson_at_time, get_link, set_link, get_now, get_week, get_lesson_desc, \
    get_lesson_duration, get_users, add_users, get_lesson_number_at_time, get_today_schedule, get_week_schedule, \
    get_lesson_in_minutes
import datetime
import threading
from time import sleep
import zipfile
from shutil import rmtree
import io

setting = Setting()
bot = telebot.TeleBot(token=setting.bot_token)
locker = threading.RLock()


@bot.message_handler(commands=['start'])
def start_handler(message: telebot.types.Message):
    with locker:
        bot.reply_to(message, 'Hello')
        add_users(message.from_user.id)


@bot.message_handler(commands=['set_link'])
def set_link_handler(message: telebot.types.Message):
    with locker:
        try:
            command, short_entry, lesson_type, *_ = message.text.split()
            bot.reply_to(message, f'old link : {get_link(short_entry, lesson_type)}')
            set_link(short_entry, lesson_type,
                     message.text.replace(command, '').replace(short_entry, '').replace(lesson_type, ''))
        except Exception as ex:
            bot.reply_to(message, str(ex))


@bot.message_handler(commands=['get_link'])
def get_link_handler(message: telebot.types.Message):
    with locker:
        try:
            _, short_entry, lesson_type = message.text.split()
            bot.reply_to(message, f'link : {get_link(short_entry, lesson_type)}')
        except Exception as ex:
            bot.reply_to(message, str(ex))


@bot.message_handler(commands=['set_schedule'])
def set_schedule_handler(message: telebot.types.Message):
    setting.set_schedule = True


@bot.message_handler(func=lambda _: setting.set_schedule, content_types=['document'])
def set_schedule_handler(message: telebot.types.Message):
    with locker:
        file_id_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_id_info.file_path)
        rmtree(os.path.join(setting.data_dir, 'Schedule'))
        print(type(downloaded_file))
        zip = zipfile.ZipFile(io.BytesIO(downloaded_file))
        zip.extractall(setting.data_dir)
        setting.set_schedule = False


@bot.message_handler(commands=['today'])
def today_schedule_handler(message: telebot.types.Message):
    today, _ = get_now()
    today_schedule = get_today_schedule(today)
    if today_schedule is not None:
        bot.send_message(message.from_user.id, str(today_schedule), parse_mode='HTML')
    else:
        bot.send_message(message.from_user.id, 'there are no schedule today')


@bot.message_handler(commands=['week', 'next_week'])
def week_schedule_handler(message: telebot.types.Message):
    command = message.text.split()[0].replace('/', '')
    week = get_week() if command == 'week' else 3 - get_week()
    week_schedule = get_week_schedule(week)
    if week_schedule is not None:
        bot.send_message(message.from_user.id, str(week_schedule), parse_mode='HTML')
    else:
        bot.send_message(message.from_user.id, 'there are no schedule today')


@bot.message_handler(commands=['info'])
def info_handler(message: telebot.types.Message):
    mess = f'''
    commands:
    /start
    /set_link short_entry lesson_type link
    /get_link short_entry lesson_type
    /today
    /week
    /next_week
    /info
    /set_schedule
    '''
    bot.reply_to(message, mess)


def create_scheduler(bot: telebot.TeleBot):
    while True:
        try:
            today, time = get_now()
            lesson, lesson_type, lesson_number = get_lesson_in_minutes(today, get_week(), time, setting.minutes)
            with locker:
                if lesson:
                    lesson, lesson_type = lesson.strip(), lesson_type.strip()
                    link = get_link(lesson, lesson_type)
                    start_lesson, end_lesson = get_lesson_duration(lesson_number)
                    lesson_duration = f"{':'.join(str(start_lesson).split()[3].split(':')[:2])} - {':'.join(str(end_lesson).split()[3].split(':')[:2])}"
                    _, full_entry, _, teacher, _ = get_lesson_desc(lesson, lesson_type).values[0]
                    for user in get_users():
                        bot.send_message(user,
                                         f'{lesson_number}) {full_entry} ({lesson_duration})\n'
                                         f'teacher: {teacher}\n'
                                         f'link: {link}')
        except Exception as ex:
            for user in get_users():
                bot.send_message(user, str(ex))

        sleep(setting.sleep_seconds)


thread = threading.Thread(target=create_scheduler, args=(bot,))
thread.setDaemon(True)
thread.start()

bot.infinity_polling()
