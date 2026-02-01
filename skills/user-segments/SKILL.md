---
name: user-segments
description: Query user attributes and segment data from Databricks. This skill should be used when the user asks about user segments, segment sizes, user attributes (like affluence scores, fraud flags, zombie status), or needs to look up which segments a user belongs to. Trigger phrases include "segment size", "users in segment", "user attributes", "is user in segment", "segment metadata", "list segments".
---

# User Segments & Attributes

Query user attributes and segment membership data from Databricks tables.

## Prerequisites

This skill depends on the `databricks-sql` skill. Ensure it is configured with valid credentials.

## Data Sources

### 1. User Attribute Store (UAS)

**Table:** `main.dynamodb.uas_entities`

A denormalized user-level table containing:

- User segments (across 19 namespaces)
- ML/DS scores (affluence, monetization, churn propensity)
- Fraud attributes
- Product adoption flags
- Zombie status

### 2. Segment Metadata

**Table:** `main.mysql__segment_store_v2.segments`

Segment definitions with owner, description, expiry dates.

### 3. Segment Jobs

**Table:** `main.mysql__segment_store_v2.segment_jobs`

Segment creation jobs with source SQL queries.

## Common Operations

### Get Segment Size

To get the user count for a segment, first check the segment metadata to find the source query:

```bash
uv run ~/.claude/skills/databricks-sql/scripts/databricks-sql-cli.py query --sql "
SELECT segment_name, description, owner, created_at, expiry_date
FROM main.mysql__segment_store_v2.segments
WHERE segment_name = 'SEGMENT_NAME'
" --wait
```

Then check segment_jobs for the source SQL:

```bash
uv run ~/.claude/skills/databricks-sql/scripts/databricks-sql-cli.py query --sql "
SELECT segment_id, source_details, created_at
FROM main.mysql__segment_store_v2.segment_jobs
WHERE segment_id = (
  SELECT id FROM main.mysql__segment_store_v2.segments
  WHERE segment_name = 'SEGMENT_NAME'
)
ORDER BY created_at DESC LIMIT 1
" --wait
```

The `source_details` column contains the SQL query used to populate the segment. Execute that query with COUNT(\*) to get the segment size.

### Count Users in Segment from UAS

For segments already synced to UAS, query directly:

```bash
uv run ~/.claude/skills/databricks-sql/scripts/databricks-sql-cli.py query --sql "
SELECT COUNT(DISTINCT id) as user_count
FROM main.dynamodb.uas_entities
WHERE array_contains(
  split(get_json_object(obelix_legacy_cred_pay, '\$.static.segments'), ';'),
  'SEGMENT_NAME'
)
" --wait
```

**Note:** Replace `obelix_legacy_cred_pay` with the appropriate namespace. Common namespaces:

- `obelix_legacy` - General segments
- `obelix_legacy_cred_pay` - Pay Online segments
- `obelix_legacy_MAX` - MAX segments
- `obelix_legacy_win` - Win/rewards segments

Segment types within each namespace:

- `$.static.segments` - Static/batch segments
- `$.batch.segments` - Batch-computed segments
- `$.realtime.segments` - Real-time segments

### Get User Attributes

To get attributes for a specific user:

```bash
uv run ~/.claude/skills/databricks-sql/scripts/databricks-sql-cli.py query --sql "
SELECT
  id,
  get_json_object(ds_attributes, '\$.ds_affluence_score') as affluence_score,
  get_json_object(ds_attributes, '\$.monetization_score_v2') as monetization_score,
  get_json_object(ds_attributes, '\$.is_zombie') as is_zombie,
  get_json_object(global_attributes, '\$.cards_fetched') as cards_fetched,
  get_json_object(global_attributes, '\$.fs_v2') as fan_segment,
  get_json_object(fraud_attributes, '\$.referral_abuser') as referral_abuser
FROM main.dynamodb.uas_entities
WHERE id = 'cred:user:USER_UUID'
" --wait
```

### List User's Segments

To see all segments a user belongs to:

```bash
uv run ~/.claude/skills/databricks-sql/scripts/databricks-sql-cli.py query --sql "
SELECT
  id,
  get_json_object(obelix_legacy, '\$.segments') as legacy_segments,
  get_json_object(obelix_legacy_cred_pay, '\$.static.segments') as credpay_static,
  get_json_object(obelix_legacy_cred_pay, '\$.batch.segments') as credpay_batch
FROM main.dynamodb.uas_entities
WHERE id = 'cred:user:USER_UUID'
" --wait
```

### List Available Segments (Sample)

To discover segments in a namespace:

```bash
uv run ~/.claude/skills/databricks-sql/scripts/databricks-sql-cli.py query --sql "
SELECT segment, COUNT(*) as cnt
FROM (
  SELECT explode(split(get_json_object(obelix_legacy_cred_pay, '\$.static.segments'), ';')) AS segment
  FROM main.dynamodb.uas_entities
  WHERE get_json_object(obelix_legacy_cred_pay, '\$.static.segments') IS NOT NULL
  LIMIT 100000
)
WHERE segment != ''
GROUP BY segment
ORDER BY cnt DESC
LIMIT 20
" --wait
```

### Get Segment Metadata

```bash
uv run ~/.claude/skills/databricks-sql/scripts/databricks-sql-cli.py query --sql "
SELECT segment_name, description, owner, created_at, expiry_date, tags
FROM main.mysql__segment_store_v2.segments
WHERE segment_name LIKE '%SEARCH_TERM%'
ORDER BY created_at DESC
LIMIT 20
" --wait
```

## Reference

For detailed table schemas and column descriptions, see `references/table_schemas.md`.
