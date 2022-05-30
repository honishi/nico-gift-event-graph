#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
import sys
from datetime import datetime
from typing import List, Optional

import mysql.connector
from flask import render_template, Flask
from flask_caching import Cache
from gevent.pywsgi import WSGIServer

# https://www.heavy.ai/blog/12-color-palettes-for-telling-better-stories-with-your-data
CHART_COLORS = ["#e60049", "#0bb4ff", "#50e991", "#e6d800", "#9b19f5", "#ffa300", "#dc0ab4", "#b3d4ff", "#00bfa0"]

app = Flask(__name__)

# Configure cache for the app.
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 60
})
cache.init_app(app)


class EventSetting:
    setting_name: str
    gift_event_id: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str

    def __init__(self, setting_name: str, gift_event_id: str, db_host: str, db_port: int, db_user: str,
                 db_password: str):
        self.setting_name = setting_name
        self.gift_event_id = gift_event_id
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password


class RankUser:
    name: str
    scores: List[int]
    color: str

    def __init__(self, name: str, scores: List[int], color: str):
        self.name = name
        self.scores = scores
        self.color = color


class RankingData:
    labels: List[str]
    top_users: List[RankUser]
    data_as_of: str
    generated_at: datetime

    def __init__(self, labels: List[str], top_users: List[RankUser], data_as_of: str, generated_at: datetime):
        self.labels = labels
        self.top_users = top_users
        self.data_as_of = data_as_of
        self.generated_at = generated_at


@app.route("/")
def top():
    event_setting = read_event_settings()
    ranking_data_cache_key = "ranking_data_cache_key"
    ranking_data: Optional[RankingData] = cache.get(ranking_data_cache_key)
    if ranking_data is None:
        # print('not cached, or cache is expired. make.')
        ranking_data = make_ranking_data(event_setting)
        cache.set(ranking_data_cache_key, ranking_data)
    else:
        # print('use cache.')
        pass
    # print(ranking_data)
    return render_template('index.html', data=ranking_data)


def read_event_settings() -> EventSetting:
    config = configparser.ConfigParser()
    config.read('settings.ini')
    section = config.sections()[0]
    return EventSetting(
        section,
        config.get(section, "gift_event_id"),
        config.get(section, "db_host"),
        int(config.get(section, "db_port")),
        config.get(section, "db_user"),
        config.get(section, "db_password")
    )


def make_ranking_data(setting: EventSetting) -> RankingData:
    connection = mysql.connector.connect(
        host=setting.db_host,
        port=setting.db_port,
        user=setting.db_user,
        password=setting.db_password,
        database='nico_gift_event_graph_db'
    )
    cursor = connection.cursor()

    # Query database.
    latest_timestamp = query_latest_timestamp(cursor, setting)
    latest_timestamps = query_timestamps(cursor, setting)
    top_users = query_top_users(cursor, setting, latest_timestamp)
    score_histories = query_score_histories(cursor, setting, top_users, latest_timestamps)

    # Make data.
    x_labels = reversed(make_x_labels(latest_timestamps))
    users = []
    for index, (name, scores) in enumerate(score_histories):
        user = RankUser(
            f"{index + 1}. {name}",
            list(reversed(scores)),
            CHART_COLORS[index % len(CHART_COLORS)]
        )
        users.append(user)
    data_as_of = datetime.fromtimestamp(latest_timestamp).strftime('%Y/%m/%d %H:%M:%S')
    return RankingData(x_labels, users, data_as_of, datetime.now())


def query_latest_timestamp(cursor, setting: EventSetting) -> int:
    sql = f"""
    select max(timestamp) 
    from ranking 
    where gift_event_id = '{setting.gift_event_id}'
    """
    cursor.execute(sql)
    row = cursor.fetchone()
    return row[0]


def query_timestamps(cursor, setting: EventSetting) -> List[int]:
    sql = f"""
    select distinct timestamp 
    from ranking 
    where gift_event_id = '{setting.gift_event_id}'
    order by timestamp desc
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    timestamps = []
    for row in rows:
        timestamps.append(row[0])
    # print(timestamps)
    return timestamps


def make_x_labels(timestamps: List[int]) -> List[str]:
    labels = []
    for timestamp in timestamps:
        _datetime = datetime.fromtimestamp(timestamp)
        date = _datetime.strftime('%m/%d')
        time = _datetime.strftime('%H:%M')
        labels.append(" ".join([date, time]))
    # print(labels)
    return labels


def query_top_users(cursor, setting: EventSetting, latest_timestamp: int) -> List:
    sql = f"""
    select item_id, name
    from ranking
    where gift_event_id = '{setting.gift_event_id}' 
    and timestamp = {latest_timestamp} 
    order by `rank` asc limit 15
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    top_users = []
    for row in rows:
        top_users.append(row)
    # print(top_users)
    return top_users


def query_score_histories(cursor, setting: EventSetting, top_users: List[str], latest_timestamps: List[int]) -> List:
    # print(f"timestamps.len: {len(latest_timestamps)}")
    histories = []
    for user_id, name in top_users:
        sql = f"""
        select timestamp, total_score 
        from ranking 
        where gift_event_id = '{setting.gift_event_id}'
        and item_id = '{user_id}'
        order by timestamp desc;
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        # print(f"user_id: {user_id} rows: {len(rows)}")
        score_dic = {}
        for timestamp, total_score in rows:
            score_dic[timestamp] = total_score
        scores = []
        for valid_timestamp in latest_timestamps:
            scores.append(score_dic[valid_timestamp] if valid_timestamp in score_dic else 0)
        # print(user_id, name)
        # print(len(scores))
        histories.append((name, scores))
    return histories


if __name__ == "__main__":
    if len(sys.argv) == 3:
        # EXPERIMENTAL: use gevent for slow performance issue with Chrome.
        # https://stackoverflow.com/a/29887309/13220031
        http_server = WSGIServer((sys.argv[1], int(sys.argv[2])), app)
        http_server.serve_forever()
    else:
        app.run(debug=True, threaded=True, port=5001)
