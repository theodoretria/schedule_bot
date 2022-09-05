import json

from setting import Setting
import pandas as pd
import os
import datetime
import calendar
from math import isnan

setting = Setting()


def get_lesson(day, week, lesson_number):
    schedule_dir = os.path.join(setting.data_dir, setting.schedule_dir)
    file_name = f'{day}_{week}.xlsx'
    if file_name not in os.listdir(schedule_dir):
        return None, None
    schedule_df = pd.read_excel(os.path.join(schedule_dir, file_name), index_col=0)
    try:
        if all(map(isnan, schedule_df.iloc[lesson_number - 1, 1:3])):
            return None, None
    except TypeError:
        return schedule_df.iloc[lesson_number - 1, 1:3]


def get_lesson_at_time(day, week, time):
    schedule_dir = os.path.join(setting.data_dir, setting.schedule_dir)
    file_name = f'{day}_{week}.xlsx'
    if file_name not in os.listdir(schedule_dir):
        return None, None
    lesson_number = get_lesson_number_at_time(time)
    if lesson_number:
        return get_lesson(day, week, lesson_number)
    return None, None


def get_lesson_time():
    lesson_time = pd.read_excel(os.path.join(setting.data_dir, 'lessons_time_start.xlsx'), index_col=0)
    lesson_time['start'] = lesson_time['start'].apply(lambda a: datetime.timedelta(a))
    lesson_time['end'] = lesson_time['end'].apply(lambda a: datetime.timedelta(a))
    return lesson_time


def get_link(short_entry, type_of_lesson):
    links = pd.read_excel(os.path.join(setting.data_dir, 'links.xlsx'), index_col=0)
    link = links[(links['short_entry'] == short_entry) & (links['type_of_lesson'] == type_of_lesson)]['link'].values[0]
    return link


def set_link(short_entry, type_of_lesson, link):
    links = pd.read_excel(os.path.join(setting.data_dir, 'links.xlsx'), index_col=0)
    links.loc[(links['short_entry'] == short_entry) & (links['type_of_lesson'] == type_of_lesson), 'link'] = link
    links.to_excel(os.path.join(setting.data_dir, 'links.xlsx'))


def get_lesson_number_at_time(time):
    lesson_time = get_lesson_time()
    for _, row in lesson_time.iterrows():
        if row['start'] <= time <= row['end']:
            return row['lesson number']
    return 0


def get_now():
    today = datetime.date.today()
    now = datetime.datetime.now()
    today = calendar.day_name[today.weekday()]
    time = datetime.timedelta(hours=now.time().hour, minutes=now.time().minute, seconds=now.time().second)
    # return setting.work_days_of_the_week[0], datetime.timedelta(hours=14, minutes=5, seconds=30)
    return today, time


def get_week():
    week_now = datetime.date.today().isocalendar().week
    return week_now % 2 + 1


def get_lesson_desc(short_entry, type_of_lesson):
    subject_path = os.path.join(setting.data_dir, 'subject.xlsx')
    try:
        subject = pd.read_excel(subject_path, index_col=0)
    except Exception as ex:
        raise ex
    else:
        desc = subject[(subject['short_entry'] == short_entry) & (subject['type_of_lesson'] == type_of_lesson)]
        return desc


def get_lesson_duration(lesson_number: int):
    lesson_time = get_lesson_time()
    row = lesson_time[lesson_time['lesson number'] == lesson_number]
    if not row.empty:
        return row['start'], row['end']
    return None, None
    # return f"{':'.join(str(row['start']).split()[3].split(':')[:2])} - {':'.join(str(row['end']).split()[3].split(':')[:2])}"


def get_users():
    with open(os.path.join(setting.data_dir, 'users.json'), 'r') as f:
        users = json.load(f)
    return users


def add_users(user):
    users = get_users()
    users.append(user)
    users = list(set(users))
    with open(os.path.join(setting.data_dir, 'users.json'), 'w') as f:
        json.dump(users, f)


def get_today_schedule(today):
    schedule_dir = os.path.join(setting.data_dir, setting.schedule_dir)
    file_name = f'{today}_{get_week()}.xlsx'
    if file_name in os.listdir(schedule_dir):
        res = ''
        today_schedule = pd.read_excel(os.path.join(schedule_dir, file_name), index_col=0)
        for _, (lesson_number, lesson_short_entry, lesson_type) in today_schedule.iterrows():
            start_lesson, end_lesson = get_lesson_duration(lesson_number)
            lesson_duration = f"{':'.join(str(start_lesson).split()[3].split(':')[:2])} - {':'.join(str(end_lesson).split()[3].split(':')[:2])}"
            if not type(lesson_short_entry) is float:
                _, full_entry, _, teacher, _ = get_lesson_desc(lesson_short_entry, lesson_type).values[0]
                res += f'<b>{lesson_number}</b> ({lesson_duration}):\n{full_entry}  <i>{lesson_type}</i>\n{teacher}\n\n'
            else:
                res += f'<b>{lesson_number}</b> ({lesson_duration}):\n---\n\n'

        return res

    return None


def get_week_schedule(week):
    res = f'week: {week}\n'
    for day in setting.work_days_of_the_week:
        res += f'<b>{day}</b>\n'
        res += get_today_schedule(day)
        res += '\n'
    return res


def get_lesson_in_minutes(today, week, time, minutes):
    for minute in minutes:
        lesson_number = get_lesson_number_at_time(time+datetime.timedelta(minutes=minute))
        if lesson_number:
            start, _ = get_lesson_duration(lesson_number)
            if (datetime.timedelta(minutes=0, hours=0) < time - (
                    start - datetime.timedelta(minutes=minute, hours=0))).values[0] and \
                    (time - (start - datetime.timedelta(minutes=minute, hours=0)) < datetime.timedelta(minutes=1,
                                                                                                       hours=0)).values[0]:
                return *get_lesson_at_time(today, week, time + datetime.timedelta(minutes=minute, hours=0)), lesson_number
    return None, None, None
