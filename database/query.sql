use nico_gift_event_graph_db;
select * from ranking;
show grants;
truncate table ranking;
select max(timestamp) from ranking where gift_event_id = '202206_camp';
select distinct timestamp from ranking where gift_event_id = '202206_camp' order by timestamp asc;
select item_id from ranking where gift_event_id = '202206_camp' and timestamp = 1653748382 order by `rank` asc limit 10;
select total_score from ranking where gift_event_id = '202206_camp' and item_id = 54091817 order by timestamp desc;
