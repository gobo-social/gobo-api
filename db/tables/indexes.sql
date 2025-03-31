CREATE INDEX CONCURRENTLY 
ON link
USING btree 
(origin_type, origin_id, target_type, target_id, name, secondary, created, updated);

CREATE INDEX CONCURRENTLY 
ON link 
USING btree 
(target_type, target_id, origin_type, origin_id, name, secondary, created, updated);

CREATE INDEX CONCURRENTLY 
ON post 
USING btree 
(base_url, platform_id);

CREATE INDEX CONCURRENTLY 
ON bluesky_session 
USING btree 
(person_id, identity_id, base_url, did);

CREATE INDEX CONCURRENTLY 
ON identity 
USING btree 
(person_id, platform_id, created, updated);

CREATE INDEX CONCURRENTLY 
ON person 
USING btree 
(authority_id);

CREATE INDEX CONCURRENTLY 
ON gobo_key 
USING btree 
(key);

CREATE INDEX CONCURRENTLY 
ON post_edge 
USING btree 
(identity_id, post_id, secondary, created, updated);

CREATE INDEX CONCURRENTLY 
ON source 
USING btree 
(base_url, platform_id, created, updated);

CREATE INDEX CONCURRENTLY 
ON store
USING btree 
(person_id, name);

CREATE INDEX CONCURRENTLY 
ON notification 
USING btree 
(base_url, platform_id, created, updated);

CREATE INDEX CONCURRENTLY 
ON counter
USING btree 
(target_type, target_id, origin_type, origin_id, name, secondary, created, updated);

CREATE INDEX CONCURRENTLY 
ON linkedin_session 
USING btree 
(person_id, identity_id, platform_id);

CREATE INDEX CONCURRENTLY 
ON delivery 
USING btree 
(person_id, draft_id, created, updated);

CREATE INDEX CONCURRENTLY 
ON delivery_target 
USING btree 
(person_id, delivery_id, identity_id, created, updated);

CREATE INDEX CONCURRENTLY 
ON draft 
USING btree 
(person_id, created, updated);

CREATE INDEX CONCURRENTLY 
ON draft_file 
USING btree 
(person_id, created, updated);

CREATE INDEX CONCURRENTLY 
ON task 
USING btree 
(channel, shard, visible, priority, created, updated);

CREATE INDEX CONCURRENTLY 
ON channel
USING btree 
(name, claimed, paused, processing, created, updated);
