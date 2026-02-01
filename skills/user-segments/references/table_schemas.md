# Table Schemas Reference

## main.dynamodb.uas_entities

User Attribute Store - a denormalized user-level table with JSON columns.

### Identity Columns

| Column      | Type   | Description                                                            |
| ----------- | ------ | ---------------------------------------------------------------------- |
| `id`        | string | User identifier (e.g., `cred:user:uuid` or `cred:phone_number:+91xxx`) |
| `namespace` | string | Entity namespace                                                       |

### Segment Namespace Columns (19 columns)

Each namespace column contains JSON with segment memberships:

```
obelix_legacy
obelix_legacy_citadel
obelix_legacy_MAX
obelix_legacy_referrals
obelix_legacy_track
obelix_legacy_store
obelix_legacy_win
obelix_legacy_data_platform
obelix_legacy_hermes
obelix_legacy_cred_pay
obelix_legacy_shield
obelix_legacy_mint
obelix_legacy_gating
obelix_legacy_fraud
obelix_legacy_concord
obelix_legacy_payments
obelix_legacy_bnpl
obelix_legacy_promotions
```

**JSON Structure (Legacy):**

```json
{
  "segments": "segment1;segment2;segment3",
  "segments_batch": "batch_seg1;batch_seg2"
}
```

**JSON Structure (Newer namespaces):**

```json
{
  "realtime": {
    "segments": "rt_seg1;rt_seg2"
  },
  "batch": {
    "segments": "batch_seg1;batch_seg2"
  },
  "static": {
    "segments": "static_seg1;static_seg2"
  }
}
```

### User Attribute Columns

#### ds_attributes (Data Science Attributes)

| JSON Path                          | Type   | Description                       |
| ---------------------------------- | ------ | --------------------------------- |
| `$.ds_affluence_score`             | float  | Affluence score (1-10)            |
| `$.ds_affluence_score_v3`          | float  | Affluence score v3                |
| `$.monetization_score_v2`          | int    | Monetization score (1-10)         |
| `$.ds_quality_score`               | float  | User quality score                |
| `$.ds_spend_score`                 | float  | Spend propensity score            |
| `$.is_zombie`                      | string | "0" or "1" - zombie status        |
| `$.is_zombie_bom`                  | string | Beginning of month zombie status  |
| `$.ds_zombie_resurrection_score`   | float  | Resurrection probability          |
| `$.churn_propensity`               | object | Churn probability by LOB          |
| `$.gating_monetization_propensity` | float  | Monetization propensity at gating |
| `$.gating_cash_propensity`         | float  | Cash propensity at gating         |
| `$.gating_max_propensity`          | float  | MAX propensity at gating          |
| `$.bounce_prediction_score`        | float  | Bounce prediction                 |
| `$.grm_risk_score`                 | float  | GRM risk score                    |
| `$.bm_risk_score`                  | float  | BM risk score                     |
| `$.long_term_risk_score`           | float  | Long-term risk                    |
| `$.short_term_risk_v2_score`       | float  | Short-term risk v2                |

#### global_attributes

| JSON Path                         | Type    | Description                       |
| --------------------------------- | ------- | --------------------------------- |
| `$.cards_fetched`                 | string  | Card fetch status (MCF, SCF, NCF) |
| `$.fs_v2`                         | string  | Fan segment v2 (e.g., "5. E")     |
| `$.is_zombie`                     | boolean | Zombie status                     |
| `$.is_zombie_rolling`             | boolean | Rolling zombie status             |
| `$.zombie_rfm`                    | string  | RFM-based zombie segment          |
| `$.ntu`                           | boolean | New to CRED flag                  |
| `$.first_payment_ever`            | string  | First payment timestamp           |
| `$.first_transaction_date`        | string  | First transaction timestamp       |
| `$.session_days`                  | float   | Session days count                |
| `$.transactions_in_first_30_days` | float   | M0 transactions                   |
| `$.zero_transaction`              | boolean | Zero transaction flag             |
| `$.lob_first_payment_date`        | object  | First payment by LOB              |
| `$.tpu_lob`                       | object  | TPU by LOB                        |

#### fraud_attributes

| JSON Path                     | Type    | Description         |
| ----------------------------- | ------- | ------------------- |
| `$.referral_abuser`           | boolean | Referral abuse flag |
| `$.p2p_hard_abuser`           | boolean | P2P hard abuse flag |
| `$.p2p_soft_abuser`           | boolean | P2P soft abuse flag |
| `$.bbps_cashback_abuse_flag`  | boolean | BBPS cashback abuse |
| `$.max_block`                 | boolean | MAX blocked         |
| `$.identity_risk_f_flag`      | boolean | Identity risk flag  |
| `$.login_risk_flag`           | boolean | Login risk flag     |
| `$.snp_deemed_risk_flag`      | boolean | SnP deemed risk     |
| `$.store_return_abuse_flag`   | boolean | Store return abuse  |
| `$.first_party_abuse_v1_flag` | boolean | First party abuse   |

#### user_zombie_status

| JSON Path                      | Type   | Description        |
| ------------------------------ | ------ | ------------------ |
| `$.cashback_value`             | float  | Cashback value     |
| `$.latest_payment_date`        | string | Last payment date  |
| `$.list_of_upcoming_due_dates` | string | Upcoming due dates |
| `$.win_alloted_date`           | string | Win allotment date |

#### gating

| JSON Path                             | Type   | Description          |
| ------------------------------------- | ------ | -------------------- |
| `$.vpa_available`                     | string | VPA availability     |
| `$.transition_active_at_epoch_millis` | float  | Transition timestamp |

#### experimentation

| JSON Path     | Type  | Description          |
| ------------- | ----- | -------------------- |
| `$.bucket_id` | float | Experiment bucket ID |

### Product-Specific Columns

| Column     | Description                |
| ---------- | -------------------------- |
| `cash`     | Cash product attributes    |
| `bnpl`     | BNPL product state         |
| `cred_upi` | CRED UPI onboarding status |
| `maxPay`   | MAX Pay attributes         |
| `checkout` | Checkout attributes        |
| `store`    | Store attributes           |
| `travel`   | Travel product state       |
| `garage`   | Garage (motor insurance)   |

---

## main.mysql\_\_segment_store_v2.segments

Segment metadata table.

| Column         | Type      | Description                                                         |
| -------------- | --------- | ------------------------------------------------------------------- |
| `id`           | decimal   | Segment ID                                                          |
| `segment_name` | string    | Unique segment identifier                                           |
| `description`  | string    | Segment description                                                 |
| `owner`        | string    | Owner email                                                         |
| `created_by`   | string    | Creator email                                                       |
| `updated_by`   | string    | Last updater email                                                  |
| `created_at`   | timestamp | Creation time                                                       |
| `updated_at`   | timestamp | Last update time                                                    |
| `expiry_date`  | timestamp | Segment expiry                                                      |
| `client_id`    | int       | Client identifier                                                   |
| `tags`         | string    | JSON tags (secondaryOwner, managerEmail, developerLob, consumerLob) |

---

## main.mysql\_\_segment_store_v2.segment_jobs

Segment job definitions with source queries.

| Column                | Type      | Description                                    |
| --------------------- | --------- | ---------------------------------------------- |
| `id`                  | decimal   | Job ID                                         |
| `segment_id`          | decimal   | Foreign key to segments.id                     |
| `job_name`            | string    | Job name                                       |
| `source_type`         | int       | Source type (0 = SQL)                          |
| `source_details`      | string    | **SQL query used to populate segment**         |
| `job_mode`            | string    | Job mode                                       |
| `status`              | int       | Job status (0=pending, 2=running, 3=completed) |
| `owner`               | string    | Owner email                                    |
| `created_at`          | timestamp | Creation time                                  |
| `job_lifecycle_start` | timestamp | Job start time                                 |
| `job_lifecycle_end`   | timestamp | Job end time                                   |
| `cron_schedule`       | string    | Cron schedule (if recurring)                   |
| `priority`            | int       | Job priority                                   |
| `provider_job_id`     | decimal   | External job ID                                |

---

## Segment Namespaces Reference

| Namespace                     | Use Case                     |
| ----------------------------- | ---------------------------- |
| `obelix_legacy`               | General/legacy segments      |
| `obelix_legacy_citadel`       | Citadel-related segments     |
| `obelix_legacy_MAX`           | MAX product segments         |
| `obelix_legacy_referrals`     | Referral segments            |
| `obelix_legacy_track`         | Tracking segments            |
| `obelix_legacy_store`         | Store segments               |
| `obelix_legacy_win`           | Win/rewards segments         |
| `obelix_legacy_data_platform` | Data platform segments       |
| `obelix_legacy_hermes`        | Hermes (comms) segments      |
| `obelix_legacy_cred_pay`      | CRED Pay/Pay Online segments |
| `obelix_legacy_shield`        | Shield (fraud) segments      |
| `obelix_legacy_mint`          | Mint segments                |
| `obelix_legacy_gating`        | Gating segments              |
| `obelix_legacy_fraud`         | Fraud segments               |
| `obelix_legacy_concord`       | Concord segments             |
| `obelix_legacy_payments`      | Payments segments            |
| `obelix_legacy_bnpl`          | BNPL segments                |
| `obelix_legacy_promotions`    | Promotions segments          |

---

## Common Cohort Values

| Cohort           | Description                             |
| ---------------- | --------------------------------------- |
| `ETU`            | Eligible To Use - active eligible users |
| `ANP`            | Activated Not Paying                    |
| `NTC`            | New To CRED                             |
| `Zombie`         | Inactive users                          |
| `Zombie w App`   | Inactive users with app installed       |
| `Zombie w/o App` | Inactive users without app              |
| `Non Eligible`   | Users not eligible                      |
| `Non Activated`  | Users who haven't activated             |

## Fan Segment Values

| Segment                 | Description           |
| ----------------------- | --------------------- |
| `1. A`                  | Highest tier          |
| `2. B`                  | High tier             |
| `3. C` / `3. E`         | Mid tier              |
| `4. D`                  | Lower-mid tier        |
| `5. E`                  | Lower tier            |
| `NCF`                   | No Cards Fetched      |
| `Non Transacting Users` | Never transacted      |
| `Only Max/Cash`         | Only used MAX or Cash |
