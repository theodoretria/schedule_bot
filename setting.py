import pandas as pd
import json
import os
import platform


class Setting:
    def __init__(self):
        self.data_dir = 'Data'
        if platform.system() == 'Linux':
            self.data_dir = os.path.join(os.sep, *os.path.realpath(__file__).split(os.sep)[:-1], 'Data')
        self.schedule_dir = 'Schedule'
        self.work_days_of_the_week = ['Monday',
                                      'Tuesday', 'Wednesday',
                                      'Thursday', 'Friday']
        self.bot_token = '5647554971:AAHgZW4fv0DBZXqLO3F414cYcsVTN2ZU5xo'
        self.set_schedule = False
        self.sleep_seconds = 60
        self.minutes = [1, 10]
