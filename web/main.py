#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
import os
import sys

import boto3
from boto3.dynamodb.conditions import Key, Attr
from flask import render_template, Flask

app = Flask(__name__)


class EventSetting:
    setting_name: str
    gift_event_id: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str

    def __init__(self, setting_name: str, gift_event_id: str, aws_access_key_id: str, aws_secret_access_key: str,
                 aws_region: str):
        self.setting_name = setting_name
        self.gift_event_id = gift_event_id
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region


@app.route("/")
def top():
    event_setting = read_event_settings()
    set_aws_environmental_values(event_setting)
    load_from_dynamodb(event_setting)
    return render_template('index.html')


def read_event_settings() -> EventSetting:
    config = configparser.ConfigParser()
    config.read('settings.ini')
    section = config.sections()[0]
    return EventSetting(
        section,
        config.get(section, "gift_event_id"),
        config.get(section, "aws_access_key_id"),
        config.get(section, "aws_secret_access_key"),
        config.get(section, "aws_region")
    )


def set_aws_environmental_values(setting: EventSetting):
    os.environ['AWS_ACCESS_KEY_ID'] = setting.aws_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = setting.aws_secret_access_key
    os.environ['AWS_DEFAULT_REGION'] = setting.aws_region


def load_from_dynamodb(setting: EventSetting):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('nico-gift-event-graph')
    result = table.query(
        KeyConditionExpression=Key('partition_key').eq(setting.gift_event_id),
        # FilterExpression=Key('gift_event_id').eq(setting.gift_event_id),
        # IndexName="partition_key-gift_event_id-index"
    )
    print(result)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        # EXPERIMENTAL: use gevent for slow performance issue with Chrome.
        # https://stackoverflow.com/a/29887309/13220031
        # http_server = WSGIServer((sys.argv[1], int(sys.argv[2])), app)
        # http_server.serve_forever()
        pass
    else:
        app.run(debug=True, threaded=True, port=5001)
