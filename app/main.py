import configparser
import datetime
from typing import List, Optional

import boto3
import requests

TMP_DIR = "./tmp"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"


class EventSetting:
    setting_name: str
    ranking_json_url: str
    s3_iam_access_key_id: str
    s3_iam_secret_access_key: str
    s3_region: str
    s3_bucket: str
    s3_folder: str
    save_file_prefix: str

    def __init__(self, setting_name: str, ranking_json_url: str, s3_iam_access_key_id: str,
                 s3_iam_secret_access_key: str, s3_region: str, s3_bucket: str, s3_folder: str, save_file_prefix: str):
        self.setting_name = setting_name
        self.ranking_json_url = ranking_json_url
        self.s3_iam_access_key_id = s3_iam_access_key_id
        self.s3_iam_secret_access_key = s3_iam_secret_access_key
        self.s3_region = s3_region
        self.s3_bucket = s3_bucket
        self.s3_folder = s3_folder
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
            filename = f"{event_setting.save_file_prefix}_{date.strftime('%Y%m%d%H%M%S')}_{int(date.timestamp())}.json"
            NicoGiftEventLoader.save_ranking_json(
                text,
                TMP_DIR,
                filename
            )
            NicoGiftEventLoader.backup_json_to_s3(
                TMP_DIR,
                filename,
                event_setting.s3_iam_access_key_id,
                event_setting.s3_iam_secret_access_key,
                event_setting.s3_region,
                event_setting.s3_bucket,
                event_setting.s3_folder,
            )
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
                    config.get(section, "s3_iam_access_key_id"),
                    config.get(section, "s3_iam_secret_access_key"),
                    config.get(section, "s3_region"),
                    config.get(section, "s3_bucket"),
                    config.get(section, "s3_folder"),
                    config.get(section, "save_file_prefix")
                )
            )
        return event_settings

    @staticmethod
    def get_ranking_json(url: str) -> Optional[str]:
        response = requests.get(url, headers=NicoGiftEventLoader.make_http_header())
        return response.text if response.status_code == 200 else None

    @staticmethod
    def save_ranking_json(text: str, directory: str, filename: str) -> Optional[str]:
        fullpath = f"{directory}/{filename}"
        with open(fullpath, "wb") as f:
            f.write(text.encode('utf-8'))
        return fullpath

    @staticmethod
    def backup_json_to_s3(directory: str, filename: str, s3_access_key_id: str, s3_secret_access_key: str,
                          s3_region: str, s3_bucket: str, s3_folder: str):
        client = boto3.client(
            's3',
            aws_access_key_id=s3_access_key_id,
            aws_secret_access_key=s3_secret_access_key,
            region_name=s3_region
        )
        local_file = f"{directory}/{filename}"
        s3_object = f"{s3_folder}/{filename}"
        client.upload_file(local_file, s3_bucket, s3_object)

    @staticmethod
    def make_http_header():
        return {'User-Agent': USER_AGENT}


loader = NicoGiftEventLoader()
loader.start()
