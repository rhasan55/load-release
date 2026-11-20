-- Executable SQLite counterpart of the accounting projection.
-- Input tables and test insertion are in test_engine.py. Normalized fixtures only.
-- Parameters: :tenant, :as_of (UTC ISO-8601 with identical precision).
WITH available AS (
 SELECT * FROM raw WHERE tenant=:tenant AND received_at<=:as_of
 AND occurred_at<=received_at
), unique_ids AS (
 SELECT tenant,source,event_id FROM available
 GROUP BY tenant,source,event_id
 HAVING COUNT(DISTINCT external_id||'|'||entity_id||'|'||version||'|'||occurred_at||'|'||payload)=1
), dedup AS (
 SELECT a.*,ROW_NUMBER() OVER(PARTITION BY a.tenant,a.source,a.event_id ORDER BY received_at) AS delivery
 FROM available a JOIN unique_ids u USING(tenant,source,event_id)
), mapped AS (
 SELECT d.*,m.load_id FROM dedup d JOIN identity_map m USING(tenant,source,external_id)
 WHERE delivery=1 AND d.source='quickbooks'
), latest AS (
 SELECT *,MAX(version) OVER(PARTITION BY tenant,source,entity_id,load_id) AS current_version
 FROM mapped
), valid_versions AS (
 SELECT tenant,source,entity_id,load_id,version,MIN(payload) AS payload
 FROM latest WHERE version=current_version
 GROUP BY tenant,source,entity_id,load_id,version
 HAVING COUNT(DISTINCT payload)=1
), cents AS (
 SELECT load_id,
 SUM(CASE WHEN json_type(payload,'$.invoice_cents')='integer' AND json_extract(payload,'$.invoice_cents')>=0 THEN json_extract(payload,'$.invoice_cents') ELSE 0 END) AS invoiced,
 SUM(CASE WHEN json_type(payload,'$.payment_cents')='integer' AND json_extract(payload,'$.payment_cents')>=0 THEN json_extract(payload,'$.payment_cents') ELSE 0 END) AS paid
 FROM valid_versions GROUP BY load_id
)
SELECT i.load_id,COALESCE(c.invoiced,0),COALESCE(c.paid,0),COALESCE(c.invoiced,0)-COALESCE(c.paid,0)
FROM (SELECT DISTINCT load_id FROM identity_map WHERE tenant=:tenant) i
LEFT JOIN cents c USING(load_id) ORDER BY i.load_id;
