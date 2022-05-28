import configparser
import datetime
from typing import List, Optional

import requests

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"


class EventSetting:
    setting_name: str
    ranking_json_url: str
    save_file_prefix: str

    def __init__(self, setting_name: str, ranking_json_url: str, save_file_prefix: str):
        self.setting_name = setting_name
        self.ranking_json_url = ranking_json_url
        self.save_file_prefix = save_file_prefix


class NicoGiftEventLoader:
    def __init__(self):
        self.event_settings = self.read_event_settings()

    def start(self):
        for event_setting in self.event_settings:
            date = datetime.datetime.now()
            print(f"*** {date}")
            print(f"{event_setting.ranking_json_url}")
            text = NicoGiftEventLoader.get_ranking_json(event_setting.ranking_json_url)
            print(text)
            if text is None:
                continue
            NicoGiftEventLoader.save_ranking_json(text, event_setting.save_file_prefix, date)
            # dynamodb

    @staticmethod
    def read_event_settings() -> List[EventSetting]:
        config = configparser.ConfigParser()
        config.read('settings.ini')
        event_settings = []
        for section in config.sections():
            event_settings.append(
                EventSetting(
                    section,
                    config.get(section, "ranking_json_url"),
                    config.get(section, "save_file_prefix")
                )
            )
        return event_settings

    @staticmethod
    def get_ranking_json(url: str) -> Optional[str]:
        response = requests.get(url, headers=NicoGiftEventLoader.make_http_header())
        return response.text if response.status_code == 200 else None

    @staticmethod
    def save_ranking_json(text: str, prefix: str, date: datetime):
        filename = 'ranking_json/' + prefix + date.strftime('%Y%m%d_%H%M%S') + ".json"
        file = open(filename, "wb")
        file.write(text.encode('utf-8'))
        file.close()

    @staticmethod
    def make_http_header():
        return {'User-Agent': USER_AGENT}


loader = NicoGiftEventLoader()
loader.start()
