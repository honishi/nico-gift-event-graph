#!/usr/bin/env python

import configparser
import datetime
import json
import os
from dataclasses import dataclass
from time import sleep
from typing import List, Optional

import boto3
import mysql.connector
import requests

SETTINGS_INI = '../settings.ini'
TMP_DIR = "./tmp"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) " + \
             "Chrome/96.0.4664.110 Safari/537.36"
FETCH_RETRY_INTERVAL = 3
MAX_FETCH_RETRY_COUNT = 100


@dataclass
class EventSetting:
    gift_event_id: str
    begin_time_jst: datetime
    end_time_jst: datetime
    ranking_json_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str


class NicoGiftEventLoader:
    def __init__(self):
        self.event_settings = self.read_event_settings()

    def start(self):
        for event_setting in self.event_settings:
            date = datetime.datetime.now()
            timestamp = int(date.timestamp())
            print(f"*** {date} [{event_setting.gift_event_id}]")

            # 1. Is Event Ongoing?
            if not NicoGiftEventLoader.is_event_ongoing(event_setting):
                # print(f"The event is not ongoing. "
                #       f"({event_setting.begin_time_jst} -> {event_setting.end_time_jst})")
                continue

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
            filename = f"{event_setting.gift_event_id}_{date.strftime('%Y%m%d%H%M%S')}_{timestamp}.json"
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
        config.read(SETTINGS_INI)
        event_settings = []
        section_common = "common"
        aws_access_key_id = config.get(section_common, "aws_access_key_id")
        aws_secret_access_key = config.get(section_common, "aws_secret_access_key")
        aws_region = config.get(section_common, "aws_region")
        s3_bucket = config.get(section_common, "s3_bucket")
        db_host = config.get(section_common, "db_host")
        db_port = int(config.get(section_common, "db_port"))
        db_user = config.get(section_common, "db_user")
        db_password = config.get(section_common, "db_password")

        for section in config.sections():
            if section == section_common:
                continue
            event_settings.append(
                EventSetting(
                    section,
                    datetime.datetime.fromisoformat(config.get(section, "begin_time_jst")),
                    datetime.datetime.fromisoformat(config.get(section, "end_time_jst")),
                    config.get(section, "ranking_json_url"),
                    aws_access_key_id,
                    aws_secret_access_key,
                    aws_region,
                    s3_bucket,
                    db_host,
                    db_port,
                    db_user,
                    db_password,
                )
            )
        return event_settings

    @staticmethod
    def is_event_ongoing(setting: EventSetting) -> bool:
        jst = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
        now = datetime.datetime.now(jst)
        # print(f"now: {now} end: {setting.gift_event_end_time_jst}")
        return setting.begin_time_jst < now < setting.end_time_jst

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
        s3_key = f"{setting.gift_event_id}/{filename}"
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
