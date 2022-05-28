#!/usr/bin/env python

import configparser
import datetime
import json
import os
from typing import List, Optional

import boto3
import requests

TMP_DIR = "./tmp"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"


class EventSetting:
    setting_name: str
    ranking_json_url: str
    gift_event_id: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket: str
    s3_folder: str
    save_file_prefix: str

    def __init__(self, setting_name: str, ranking_json_url: str, gift_event_id: str, aws_access_key_id: str,
                 aws_secret_access_key: str, aws_region: str, s3_bucket: str, s3_folder: str, save_file_prefix: str):
        self.setting_name = setting_name
        self.ranking_json_url = ranking_json_url
        self.gift_event_id = gift_event_id
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.s3_bucket = s3_bucket
        self.s3_folder = s3_folder
        self.save_file_prefix = save_file_prefix


class NicoGiftEventLoader:
    def __init__(self):
        self.event_settings = self.read_event_settings()

    def start(self):
        for event_setting in self.event_settings:
            date = datetime.datetime.now()
            timestamp = int(date.timestamp())
            print(f"*** {date}")
            print(f"{event_setting.ranking_json_url}")

            # 1. Get Ranking Data
            text = NicoGiftEventLoader.get_ranking_json(event_setting.ranking_json_url)
            # print(text)
            if text is None:
                continue

            # 2. Save Data Locally
            filename = f"{event_setting.save_file_prefix}_{date.strftime('%Y%m%d%H%M%S')}_{timestamp}.json"
            NicoGiftEventLoader.save_ranking_json(
                text,
                TMP_DIR,
                filename
            )

            # 3. Configure AWS Session
            NicoGiftEventLoader.set_aws_environmental_values(
                event_setting.aws_access_key_id,
                event_setting.aws_secret_access_key,
                event_setting.aws_region,
            )

            # 4. Backup Data to S3
            NicoGiftEventLoader.backup_json_to_s3(
                TMP_DIR,
                filename,
                event_setting.s3_bucket,
                event_setting.s3_folder,
            )

            # 5. Insert Data to DynamoDB
            NicoGiftEventLoader.upload_to_dynamodb(
                text,
                event_setting.gift_event_id,
                timestamp,
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
                    config.get(section, "aws_access_key_id"),
                    config.get(section, "aws_secret_access_key"),
                    config.get(section, "aws_region"),
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
    def make_http_header():
        return {'User-Agent': USER_AGENT}

    @staticmethod
    def save_ranking_json(text: str, directory: str, filename: str) -> Optional[str]:
        fullpath = f"{directory}/{filename}"
        with open(fullpath, "wb") as f:
            f.write(text.encode('utf-8'))
        return fullpath

    @staticmethod
    def set_aws_environmental_values(access_key_id: str, secret_access_key: str, region: str):
        os.environ['AWS_ACCESS_KEY_ID'] = access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_access_key
        os.environ['AWS_DEFAULT_REGION'] = region

    @staticmethod
    def backup_json_to_s3(directory: str, filename: str, s3_bucket: str, s3_folder: str):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(s3_bucket)
        local_file = f"{directory}/{filename}"
        s3_key = f"{s3_folder}/{filename}"
        bucket.upload_file(local_file, s3_key)

    @staticmethod
    def upload_to_dynamodb(json_text: str, gift_event_id: str, timestamp: int):
        dic = json.loads(json_text)
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('nico-gift-event-graph')
        for entry_item in dic['data']['entry_items']:
            entry_item['partition_key'] = f"{gift_event_id}_{timestamp}_{entry_item['item_id']}"
            entry_item['gift_event_id'] = gift_event_id
            entry_item['timestamp'] = timestamp
            # print(entry_item)
            table.put_item(Item=entry_item)


loader = NicoGiftEventLoader()
loader.start()
