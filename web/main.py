#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import mysql.connector
from flask import render_template, Flask
from flask_caching import Cache
from gevent.pywsgi import WSGIServer

SETTINGS_INI = '../settings.ini'
# https://www.heavy.ai/blog/12-color-palettes-for-telling-better-stories-with-your-data
CHART_COLORS = ["#e60049", "#0bb4ff", "#50e991", "#e6d800", "#9b19f5", "#ffa300", "#dc0ab4", "#b3d4ff", "#00bfa0"]
USER_PAGE_URL = 'https://www.nicovideo.jp/user'

app = Flask(__name__)

# Configure cache for the app.
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 60
})
cache.init_app(app)


@dataclass
class Event:
    event_id: str
    title: str
    short_title: str
    icon: str
    begin_time_jst: datetime
    end_time_jst: datetime
    ranking_page_url: str


@dataclass
class EventSetting:
    event_id: str
    events: List[Event]
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    gtm_container_id: str


@dataclass
class RankUser:
    name: str
    scores: List[int]
    color: str
    user_page_url: str


@dataclass
class FooterEvent:
    event_id: str
    title: str
    icon: str


@dataclass
class PageData:
    event_id: str
    title: str
    icon: str
    ranking_page_url: str
    labels: List[str]
    top_users: List[RankUser]
    data_as_of: str
    generated_at: datetime
    footer_events: List[FooterEvent]
    gtm_container_id: str


@dataclass
class PageMeta:
    page_generation_seconds: str


@app.route("/")
@app.route("/<string:gift_event_id>")
def top(gift_event_id: Optional[str] = None):
    page_start_time = datetime.now()
    event_setting = read_event_settings()
    if gift_event_id is not None:
        event_setting.event_id = gift_event_id
    page_data_cache_key = f"page_data_cache_key_{event_setting.event_id}"
    page_data: Optional[PageData] = cache.get(page_data_cache_key)
    if page_data is None:
        # print('not cached, or cache is expired. make.')
        page_data = make_page_data(event_setting)
        cache.set(page_data_cache_key, page_data)
    else:
        # print('use cache.')
        pass
    # print(ranking_data)
    page_end_time = datetime.now()
    page_duration = (page_end_time - page_start_time).total_seconds()
    meta = PageMeta(f"{page_duration:.3f}")
    return render_template('index.html', data=page_data, meta=meta)


def read_event_settings() -> EventSetting:
    config = configparser.ConfigParser()
    config.read(SETTINGS_INI)

    section_common = "common"
    db_host = config.get(section_common, "db_host")
    db_port = int(config.get(section_common, "db_port"))
    db_user = config.get(section_common, "db_user")
    db_password = config.get(section_common, "db_password")
    gtm_container_id = config.get(section_common, "gtm_container_id")

    events: List[Event] = []
    for section in config.sections():
        if section == section_common:
            continue
        event = Event(
            section,
            config.get(section, "title"),
            config.get(section, "short_title"),
            config.get(section, "icon"),
            datetime.fromisoformat(config.get(section, "begin_time_jst")),
            datetime.fromisoformat(config.get(section, "end_time_jst")),
            config.get(section, "ranking_page_url")
        )
        events.append(event)

    ongoing_events = list(filter(lambda _event: is_event_ongoing(_event.begin_time_jst, _event.end_time_jst), events))
    default_event = events[0] if len(ongoing_events) == 0 else ongoing_events[-1]
    default_gift_event_id = default_event.event_id

    return EventSetting(
        default_gift_event_id,
        events,
        db_host,
        db_port,
        db_user,
        db_password,
        gtm_container_id,
    )


def is_event_ongoing(begin: datetime, end: datetime) -> bool:
    jst = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(jst)
    # print(f"now: {now} end: {setting.gift_event_end_time_jst}")
    return begin < now < end


def make_page_data(setting: EventSetting) -> PageData:
    event = list(filter(lambda e: e.event_id == setting.event_id, setting.events))[0]
    footer_events = list(map(lambda e: FooterEvent(e.event_id, e.short_title, e.icon), setting.events))

    # Query database.
    connection = mysql.connector.connect(
        host=setting.db_host,
        port=setting.db_port,
        user=setting.db_user,
        password=setting.db_password,
        database='nico_gift_event_graph_db'
    )
    cursor = connection.cursor()

    latest_timestamps = query_timestamps(cursor, setting)
    if len(latest_timestamps) == 0:
        # No data found. Return empty page.
        return PageData(
            setting.event_id,
            event.title,
            event.icon,
            event.ranking_page_url,
            [],
            [],
            "No Data",
            datetime.now(),
            footer_events,
            setting.gtm_container_id,
        )
    latest_timestamp = latest_timestamps[0]
    top_users = query_top_users(cursor, setting, latest_timestamp)
    score_histories = query_score_histories(cursor, setting, top_users, latest_timestamps)

    # Make data.
    x_labels = make_x_labels(latest_timestamps)
    x_labels.reverse()
    users = []
    for index, (user_id, name, scores) in enumerate(score_histories):
        medal = '🥇' if index == 0 else '🥈' if index == 1 else '🥉' if index == 2 else ''
        user = RankUser(
            f"{index + 1}. {medal}{name}",
            list(reversed(scores)),
            CHART_COLORS[index % len(CHART_COLORS)],
            f"{USER_PAGE_URL}/{user_id}"
        )
        users.append(user)
    data_as_of = datetime.fromtimestamp(latest_timestamp).strftime('%Y/%-m/%-d %-H:%M:%S')
    return PageData(
        setting.event_id,
        event.title,
        event.icon,
        event.ranking_page_url,
        x_labels,
        users,
        data_as_of,
        datetime.now(),
        footer_events,
        setting.gtm_container_id,
    )


def query_timestamps(cursor, setting: EventSetting) -> List[int]:
    sql = f"""
    select distinct timestamp 
    from ranking 
    where gift_event_id = '{setting.event_id}'
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
        date = _datetime.strftime('%-m/%-d')
        time = _datetime.strftime('%-H:%M')
        labels.append(" ".join([date, time]))
    # print(labels)
    return labels


def query_top_users(cursor, setting: EventSetting, latest_timestamp: int) -> List:
    sql = f"""
    select item_id, name
    from ranking
    where gift_event_id = '{setting.event_id}' 
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
        where gift_event_id = '{setting.event_id}'
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
        histories.append((user_id, name, scores))
    return histories


if __name__ == "__main__":
    if len(sys.argv) == 3:
        # EXPERIMENTAL: use gevent for slow performance issue with Chrome.
        # https://stackoverflow.com/a/29887309/13220031
        http_server = WSGIServer((sys.argv[1], int(sys.argv[2])), app)
        http_server.serve_forever()
    else:
        app.run(debug=True, threaded=True, port=5001)
