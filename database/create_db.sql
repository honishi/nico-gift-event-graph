CREATE DATABASE IF NOT EXISTS nico_gift_event_graph_db;

CREATE TABLE IF NOT EXISTS nico_gift_event_graph_db.ranking
(
    /* custom fields: */
    `gift_event_id` varchar(100)  NOT NULL,
    `timestamp`     int           NOT NULL,
    /* fields from ranking json: */
    `id`            int           NOT NULL,
    `item_type`     varchar(20)   NOT NULL,
    `item_id`       varchar(20)   NOT NULL, /* user id */
    `status`        varchar(20)   NOT NULL,
    `total_score`   int           NOT NULL,
    `name`          varchar(1000) NOT NULL,
    `thumbnail_url` varchar(1000) NOT NULL,
    `rank`          INT           NOT NULL,
    PRIMARY KEY (`gift_event_id`, `timestamp`, `item_id`)
);