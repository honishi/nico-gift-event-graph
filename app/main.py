#!/usr/bin/env python

import configparser
import datetime
import json
import os
from time import sleep
from typing import List, Optional

import boto3
import mysql.connector
import requests

TMP_DIR = "./tmp"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
FETCH_RETRY_INTERVAL = 3
MAX_FETCH_RETRY_COUNT = 100


class EventSetting:
    setting_name: str
    ranking_json_url: str
    gift_event_id: str
    gift_event_end_time_jst: datetime
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket: str
    s3_folder: str
    save_file_prefix: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str

    def __init__(self, setting_name: str, ranking_json_url: str, gift_event_id: str, gift_event_end_time_jst: datetime,
                 aws_access_key_id: str, aws_secret_access_key: str, aws_region: str, s3_bucket: str, s3_folder: str,
                 save_file_prefix: str, db_host: str, db_port: int, db_user: str, db_password: str):
        self.setting_name = setting_name
        self.ranking_json_url = ranking_json_url
        self.gift_event_id = gift_event_id
        self.gift_event_end_time_jst = gift_event_end_time_jst
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.s3_bucket = s3_bucket
        self.s3_folder = s3_folder
        self.save_file_prefix = save_file_prefix
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password


class NicoGiftEventLoader:
    def __init__(self):
        self.event_settings = self.read_event_settings()

    def start(self):
        for event_setting in self.event_settings:
            date = datetime.datetime.now()
            timestamp = int(date.timestamp())
            print(f"*** {date}")
            print(f"{event_setting.ranking_json_url}")

            # 1. Is Event Ongoing?
            if NicoGiftEventLoader.is_event_ended(event_setting):
                print(f"The event is ended. ({event_setting.gift_event_end_time_jst})")
                exit()

            # 2. Get Ranking Data
            retry_count = 0
            while True:
                text = NicoGiftEventLoader.get_ranking_json(event_setting.ranking_json_url)
                if text is not None or retry_count == MAX_FETCH_RETRY_COUNT:
                    break
                retry_count += 1
                print(f"Fetch failed. Retrying... ({retry_count}/{MAX_FETCH_RETRY_COUNT})")
                sleep(FETCH_RETRY_INTERVAL)
            # print(text)
            if text is None:
                print('Failed to fetch ranking data.')
                exit()

            # 3. Save Data Locally
            filename = f"{event_setting.save_file_prefix}_{date.strftime('%Y%m%d%H%M%S')}_{timestamp}.json"
            NicoGiftEventLoader.save_ranking_json(
                text,
                TMP_DIR,
                filename
            )

            # 4. Configure AWS Session
            NicoGiftEventLoader.set_aws_environmental_values(event_setting)

            # 5. Backup Data to S3
            NicoGiftEventLoader.backup_json_to_s3(
                TMP_DIR,
                filename,
                event_setting
            )

            # 6. Insert Data to Database
            NicoGiftEventLoader.insert_to_database(
                text,
                timestamp,
                event_setting
            )

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
                    config.get(section, "gift_event_id"),
                    datetime.datetime.fromisoformat(config.get(section, "gift_event_end_time_jst")),
                    config.get(section, "aws_access_key_id"),
                    config.get(section, "aws_secret_access_key"),
                    config.get(section, "aws_region"),
                    config.get(section, "s3_bucket"),
                    config.get(section, "s3_folder"),
                    config.get(section, "save_file_prefix"),
                    config.get(section, "db_host"),
                    int(config.get(section, "db_port")),
                    config.get(section, "db_user"),
                    config.get(section, "db_password"),
                )
            )
        return event_settings

    @staticmethod
    def is_event_ended(setting: EventSetting) -> bool:
        jst = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
        now = datetime.datetime.now(jst)
        # print(f"now: {now} end: {setting.gift_event_end_time_jst}")
        return setting.gift_event_end_time_jst < now

    @staticmethod
    def get_ranking_json(url: str) -> Optional[str]:
        response = requests.get(url, headers=NicoGiftEventLoader.make_http_header())
        return response.text if response.status_code == 200 else None

    @staticmethod
    def make_http_header():
        return {'User-Agent': USER_AGENT}

    @staticmethod
    def save_ranking_json(text: str, directory: str, filename: str) -> Optional[str]:
        fullpath = f"{directory}/{filename}"
        with open(fullpath, "wb") as f:
            f.write(text.encode('utf-8'))
        return fullpath

    @staticmethod
    def set_aws_environmental_values(setting: EventSetting):
        os.environ['AWS_ACCESS_KEY_ID'] = setting.aws_access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = setting.aws_secret_access_key
        os.environ['AWS_DEFAULT_REGION'] = setting.aws_region

    @staticmethod
    def backup_json_to_s3(directory: str, filename: str, setting: EventSetting):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(setting.s3_bucket)
        local_file = f"{directory}/{filename}"
        s3_key = f"{setting.s3_folder}/{filename}"
        bucket.upload_file(local_file, s3_key)

    @staticmethod
    def insert_to_database(json_text: str, timestamp: int, setting: EventSetting):
        dic = json.loads(json_text)
        connection = mysql.connector.connect(
            host=setting.db_host,
            port=setting.db_port,
            user=setting.db_user,
            password=setting.db_password,
            database='nico_gift_event_graph_db'
        )
        cursor = connection.cursor()
        sql = '''
        INSERT INTO ranking 
            (`gift_event_id`, `timestamp`,
             `id`, `item_type`, `item_id`, `status`, `total_score`, `name`, `thumbnail_url`, `rank`)
        VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        # print(sql)
        data = []
        for entry_item in dic['data']['entry_items']:
            data.append((
                setting.gift_event_id, timestamp,
                entry_item['id'], entry_item['item_type'], entry_item['item_id'], entry_item['status'],
                entry_item['total_score'], entry_item['name'], entry_item['thumbnail_url'], entry_item['rank']
            ))
        # print(data)
        cursor.executemany(sql, data)
        connection.commit()
        cursor.close()
        print(f'Fetched and inserted {len(data)} entries.')


loader = NicoGiftEventLoader()
loader.start()
