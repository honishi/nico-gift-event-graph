#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
import sys
from datetime import datetime
from typing import List

import mysql.connector
from flask import render_template, Flask

app = Flask(__name__)


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

    def __init__(self, name: str, scores: List[int]):
        self.name = name
        self.scores = scores


class RankingData:
    labels: List[str]
    top_users: List[RankUser]

    def __init__(self, labels: List[str], top_users: List[RankUser]):
        self.labels = labels
        self.top_users = top_users


@app.route("/")
def top():
    event_setting = read_event_settings()
    data = make_ranking_data(event_setting)
    print(data)
    return render_template('index.html', data=data)


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

    # latest timestamp
    sql = f"""
    select max(timestamp) 
    from ranking 
    where gift_event_id = '{setting.gift_event_id}'
    """
    cursor.execute(sql)
    row = cursor.fetchone()
    latest_timestamp = row[0]

    # timestamps
    sql = f"""
    select distinct timestamp 
    from ranking 
    where gift_event_id = '{setting.gift_event_id}'
    order by timestamp asc
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    labels = []
    for row in rows:
        date = datetime.fromtimestamp(row[0])
        label = date.strftime('%Y/%m/%d %H:%M:%S')
        labels.append(label)
    print(labels)

    # top n user at lates timestamp
    sql = f"""
    select item_id, name
    from ranking
    where gift_event_id = '{setting.gift_event_id}' 
    and timestamp = {latest_timestamp} 
    order by `rank` asc limit 10
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    top_users = []
    for row in rows:
        top_users.append(row)
    print(top_users)

    # each user's score history
    history = []
    for user_id, name in top_users:
        sql = f"""
        select total_score 
        from ranking 
        where gift_event_id = '{setting.gift_event_id}'
        and item_id = '{user_id}'
        order by timestamp desc;
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        scores = []
        for row in rows:
            scores.append(row[0])
        print(user_id, name)
        print(scores)
        history.append((name, scores))

    # make data
    return RankingData(
        labels,
        list((RankUser(name, list(reversed(scores))) for name, scores in history)),
    )

if __name__ == "__main__":
    if len(sys.argv) == 3:
        # EXPERIMENTAL: use gevent for slow performance issue with Chrome.
        # https://stackoverflow.com/a/29887309/13220031
        # http_server = WSGIServer((sys.argv[1], int(sys.argv[2])), app)
        # http_server.serve_forever()
        pass
    else:
        app.run(debug=True, threaded=True, port=5001)
