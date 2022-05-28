# nico-gift-event-graph

## Setup

* TODO

## cheatsheet

### crontab
```
*/10 * * * * /path/to/nico-gift-event-graph/app/run.sh >> /path/to/nico-gift-event-graph/app/log/nico-gift-event-graph.log 2>&1
```

## Reference

### DynamoDB

<img src="./images/dynamodb-create.png" alt="">

### AWS IAM Policy

* [Amazon S3: Allows read and write access to objects in an S3 Bucket](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_s3_rw-bucket.html)
* [Amazon DynamoDB: Allows access to a specific table](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_dynamodb_specific-table.html)

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