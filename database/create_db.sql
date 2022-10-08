--
-- Create Database.
--
CREATE DATABASE IF NOT EXISTS nico_gift_event_graph_db;

--
-- Create Table.
--
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

--
-- Create User.
--
DROP USER 'nico_gift_event_graph_user';
CREATE USER 'nico_gift_event_graph_user' IDENTIFIED BY 'xxx';
GRANT ALL PRIVILEGES ON nico_gift_event_graph_db.* TO 'nico_gift_event_graph_user';
FLUSH PRIVILEGES;

--
-- Create Index.
--
DROP INDEX ranking_index_gift_event_id_timestamp
ON nico_gift_event_graph_db.ranking;
CREATE INDEX ranking_index_gift_event_id_timestamp
ON nico_gift_event_graph_db.ranking (gift_event_id, timestamp);

DROP INDEX ranking_index_gift_event_id_item_id_timestamp_total_score
ON nico_gift_event_graph_db.ranking;
CREATE INDEX ranking_index_gift_event_id_item_id_timestamp_total_score
ON nico_gift_event_graph_db.ranking (gift_event_id, item_id, timestamp desc, total_score);
