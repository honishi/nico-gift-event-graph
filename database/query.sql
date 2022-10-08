--
-- Configuration.
--
use nico_gift_event_graph_db;
show grants;


--
-- Basic Query.
--
select * from ranking;
select count(*) from ranking;
truncate table ranking;


--
-- Explain Plan.
--
explain
select distinct timestamp
from ranking
where gift_event_id = '202209-demae'
order by timestamp desc;

explain
select item_id, name
from ranking
where gift_event_id = '202209-demae'
  and timestamp = 1665042602
order by `rank` asc
limit 15;

explain
select timestamp, total_score
from ranking
where gift_event_id = '202209-demae'
  and item_id = '52553742'
order by timestamp desc;

--
-- Various Query.
--
select max(timestamp) from ranking where gift_event_id = '202206-camp';
select distinct timestamp from ranking where gift_event_id = '202206_camp' order by timestamp asc;
select item_id from ranking where gift_event_id = '202206_camp' and timestamp = 1653748382 order by `rank` asc limit 10;
select total_score from ranking where gift_event_id = '202206_camp' and item_id = 54091817 order by timestamp desc;
select count(*) from ranking;
