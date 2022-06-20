# nico-gift-event-graph

## Live Site

* [https://2525ans.com/gift/](https://2525ans.com/gift/)

## Setup

### 1. Database

Setup database and scheme using the following script.

* `database/create_db.sql`

### 2. Data Downloader

The ranking data json is fetched and stored to database by downloader script.

Configure Python runtime for the script as follows.

```shell
pyenv install
pip install -r requirements.txt
```

```shell
cp settings.ini.sample settings.ini
vi settings.ini
# -> configure setting
```

Then schedule the script using scheduler like cron.

```
*/10 * * * * /path/to/nico-gift-event-graph/app/run.sh >> /path/to/nico-gift-event-graph/app/log/nico-gift-event-graph.log 2>&1
```

### 3. Web Frontend

The chart dataset is dynamically generated from the database and visualized by `Chart.js`.
Web frontend is backed by `Flask`.

```shell
cd web
./start_production.sh
# or
./start_development.sh
```

Now we can access the chart at [http://127.0.0.1:5001/](http://127.0.0.1:5001/), if everything goes well.

## Reference / Cheatsheet

### AWS IAM Policy

* [Amazon S3: Allows read and write access to objects in an S3 Bucket](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_s3_rw-bucket.html)

### Sample JSON

* https://audition.nicovideo.jp/api/v1/auditions/202206-giftevent-camp/rankings?limit=100

```json
{
  "meta": {
    "status": 200
  },
  "data": {
    "entry_items": [
      {
        "id": 9416,
        "item_type": "user",
        "item_id": "54091817",
        "status": "enable",
        "total_score": 58080,
        "name": "うせつ",
        "thumbnail_url": "https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5409/54091817.jpg?1653667157",
        "related_items": null,
        "rank": 1
      },
      {
        "id": 7902,
        "item_type": "user",
        "item_id": "61407180",
        "status": "enable",
        "total_score": 39340,
        "name": "とろみ",
        "thumbnail_url": "https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/6140/61407180.jpg?1516790391",
        "related_items": null,
        "rank": 2
      }
      // ...
    ]
  }
}
```