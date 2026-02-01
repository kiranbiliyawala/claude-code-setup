# Transaction Fetching Flow - Settlement Service

## Table of Contents

- [Overview](#overview)
- [Flow Trigger](#flow-trigger)
- [Pre-Processing Validations](#pre-processing-validations)
- [Workflow Activities](#workflow-activities)
- [Query Providers](#query-providers)
- [Database Tables & Data Points](#database-tables--data-points)
- [Scheduler & Schedule Config](#scheduler--schedule-config)
- [Transaction Processing Logic](#transaction-processing-logic)
- [Memory Considerations](#memory-considerations)
- [Sequence Diagram](#sequence-diagram)
- [Key Files Reference](#key-files-reference)

---

## Overview

The **Transaction Fetching** flow is a critical step in the settlement workflow responsible for:

1. Querying eligible transactions from data platforms (Databricks/BatchPlatform)
2. Fetching query results from S3
3. Parsing and validating transactions
4. Creating settlement records with associated transactions

### High-Level Flow

```
Trigger (gRPC API)
    │
    ▼
Pre-Processing Validations
    │
    ▼
┌─────────────────────────────────────────────────────┐
│           InitializeSettlementWorkflow              │
│                                                     │
│  1. AcquireOperationLock                            │
│  2. ExecuteQueryAsyncToFetchTransactions            │
│  3. PollQueryStatus                                 │
│  4. ProcessTransactions                             │
│  5. ProcessCreatedSettlement (Sub-workflows)        │
│  6. Cleanup & Release Lock                          │
└─────────────────────────────────────────────────────┘
```

---

## Flow Trigger

### Primary Entry Point

**Endpoint:** `SettleViaWorkflow` (gRPC)
**File:** `internal/settlement/server.go:60-96`

```go
func (s *Server) SettleViaWorkflow(
    ctx context.Context,
    req *settlementpb.SettleViaWorkflowRequest,
) (*settlementpb.SettleViaWorkflowResponse, error)
```

### Request Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ScheduleId` | Yes | Unique identifier for this settlement run |
| `DbkAccountNumber` | Yes | Account number format: `{partnerType}:{partnerID}:{accountType}` |
| `ScheduleAttributes.TransactionTimeFrom` | No | Custom start time (Unix timestamp) |
| `ScheduleAttributes.TransactionTimeUpto` | No | Custom end time (Unix timestamp) |

### Who Triggers This Flow?

The settlement service **does not contain internal schedulers**. It exposes a gRPC API that must be called by:

1. **External Scheduler Service** - Calls API at configured intervals per partner
2. **Admin Operations** - Manual trigger via admin tooling
3. **Batch Jobs** - External batch processing systems

---

## Pre-Processing Validations

**File:** `internal/settlement/service.go:345-427`

Before initiating the workflow, the system performs these validations:

| Validation | Description | Failure Behavior |
|------------|-------------|------------------|
| **Lock Check** | Ensures no concurrent settlement for same partner | Returns error |
| **Settlement Allowed Check** | Verifies settlement allowed on current day | Returns error |
| **Holiday Check** | Checks bank holiday calendar | Returns error if holiday and not allowed |
| **Mode Enabled Check** | Verifies settlement is enabled for partner | Returns error |
| **On-Hold Check** | Verifies partner settlement is not on hold | Returns error |

---

## Workflow Activities

The workflow is orchestrated using Temporal/DTFX workflow engine.

**File:** `internal/settlement/init_settlement.go:26-181`

### Activity Summary

| # | Activity | Retry Policy | Purpose |
|---|----------|--------------|---------|
| 0 | `AcquireOperationLock` | 1 attempt | Distributed lock for partner |
| 1 | `ExecuteQueryAsyncToFetchTransactions` | 5 attempts, 1s interval | Submit async query |
| 2 | `PollQueryStatus` | 30 attempts, 1min interval (~30min max) | Wait for query completion |
| 3 | `ProcessTransactions` | 5 attempts, 1s interval | Fetch S3, parse, create settlements |
| 4 | `ProcessCreatedSettlement` | Sub-workflow per settlement | Post to ledger, trigger payout |
| 5 | `Cleanup` | 2 attempts | Release lock, mark skipped if failed |
| 6 | `CleanupDatabricksTempSchema` | 2 attempts | Drop temp Databricks table |

### Activity 1: ExecuteQueryAsyncToFetchTransactions

**File:** `internal/settlement/init_settlement.go:183-217`

```go
func (a *InitializeSettlementActivity) ExecuteQueryAsyncToFetchTransactions(
    ctx context.Context, req string,
) (string, error)
```

**Steps:**
1. Determines query provider based on tenant config (Databricks or BatchPlatform)
2. Gets schedule config to calculate transaction time range
3. Builds and executes async query
4. Returns `StatementID` for polling

### Activity 2: PollQueryStatus

**File:** `internal/settlement/init_settlement.go:219-240`

```go
func (a *InitializeSettlementActivity) PollQueryStatus(
    ctx context.Context, req string,
) (string, error)
```

**Behavior:**
- Polls query provider for status
- **Success** → Proceeds to ProcessTransactions
- **Non-Terminal** → Retries (up to 30 times, 1min apart)
- **Failure** → Workflow may restart with `ContinueAsNew` if retries remain

### Activity 3: ProcessTransactions

**File:** `internal/settlement/init_settlement.go:242-264`

```go
func (a *InitializeSettlementActivity) ProcessTransactions(
    ctx context.Context, req string,
) (string, error)
```

**Steps:**
1. Fetch CSV from S3
2. Parse transactions
3. Cancel pending settlements
4. Create initiated settlement
5. Process transactions in batches
6. Update settlement to Created status

---

## Query Providers

The system supports multiple query providers selected per tenant.

**File:** `internal/settlement/factory.go`

### Provider Selection

```go
func (c *Service) GetWorkflowActivityServices(tenantID string) WorkflowActivityServices {
    tenantConfig := c.workflow.tenantConfigs.GetOrDefault(tenantID)
    switch tenantConfig.QueryProvider {
    case commons.Databricks:
        return c.databricksWorkflowActivityServices
    case commons.BatchPlatform:
        return c.batchPlatformWorkflowActivityServices
    default:
        return c.databricksWorkflowActivityServices
    }
}
```

### Databricks Provider

**File:** `internal/settlement/core.go:33-80`

| Step | Action |
|------|--------|
| 1 | Get schedule config for time range |
| 2 | Drop existing temp table (cleanup from previous runs) |
| 3 | Build CREATE TABLE query with S3 output |
| 4 | Execute async via Databricks SQL API |
| 5 | Return StatementID |

**Temp Table:** `backend.temp_settlement.{md5(tenantID_partnerID_workflowID)}`
**S3 Output:** `s3://{bucket}/{tenantID}/{partnerID}/{workflowRunID}/`

### BatchPlatform Provider

**File:** `internal/settlement/core.go:105-137`

| Step | Action |
|------|--------|
| 1 | Get schedule config for time range |
| 2 | Build request with query parameters |
| 3 | Execute pipeline via BatchPlatform API |
| 4 | Return RunId |

**S3 Output:** `s3://{bucket}/bp/finhq/transaction_data/{pipelineName}/run_id={runId}/`

---

## Database Tables & Data Points

### Query Structure

**File:** `internal/databricks/query.go`

```sql
SELECT
    t_main.transaction_group_id,
    MAX(gl.id) AS order_field,
    to_json(collect_list(DISTINCT STRUCT(...))) as json_field
FROM main.{settlementDBName}.transactions t_main
JOIN main.{bookkeepingDBName}.general_ledgers gl
    ON gl.source_transaction_id = t_main.transaction_id
    AND gl.transaction_time BETWEEN '{txnStartTime}' AND '{txnEndTime}'
JOIN main.{settlementDBName}.transaction_groups tg
    ON tg.transaction_group_id = t_main.transaction_group_id
LEFT JOIN main.{settlementDBName}.settlement_transactions st
    ON st.dbk_transaction_id = t_main.transaction_id
    AND st.dbk_account_number = '{dbkAccountNo}'
LEFT JOIN main.{settlementDBName}.settlements s
    ON s.settlement_id = st.settlement_id
WHERE gl.account_no = '{dbkAccountNo}'
    AND tg.settlement_eligibility = 'eligible'
    AND t_main.tenant_id = '{tenantId}'
    AND gl.transaction_code <> 'SETTLEMENT'
GROUP BY t_main.transaction_group_id
HAVING (reconsiderable conditions) OR (never settled)
ORDER BY order_field ASC
```

### Table Descriptions

| Table | Database | Purpose |
|-------|----------|---------|
| **transactions** | Settlement DB | Core transaction records with grouping info |
| **general_ledgers** | Bookkeeping DB | Financial ledger entries with amounts |
| **transaction_groups** | Settlement DB | Settlement eligibility control |
| **settlement_transactions** | Settlement DB | Links transactions to settlements |
| **settlements** | Settlement DB | Settlement status tracking |

### Data Points by Table

#### transactions (t_main)
| Column | Usage |
|--------|-------|
| `transaction_id` | Primary identifier, joins to general_ledgers |
| `transaction_group_id` | Groups related transactions |
| `metadata` | Transaction metadata (JSON) |
| `tenant_id` | Multi-tenant filtering |

#### general_ledgers (gl)
| Column | Usage |
|--------|-------|
| `transaction_time` | Time filtering, output field |
| `amount` | Monetary amount (output) |
| `amount_nature` | CREDIT/DEBIT indicator (output) |
| `account_no` | Account filtering |
| `transaction_code` | Sub-type: PAYMENT, MDR_FEE, TAX, etc. (output) |
| `currency_code` | Currency (output) |
| `metadata` | Bookkeeping metadata (output) |
| `id` | Ordering field |
| `source_transaction_id` | Joins to transactions table |

#### transaction_groups (tg)
| Column | Usage |
|--------|-------|
| `transaction_group_id` | Joins to transactions |
| `settlement_eligibility` | Filter: only 'eligible' transactions |

#### settlement_transactions (st)
| Column | Usage |
|--------|-------|
| `dbk_transaction_id` | Links to transactions |
| `settlement_id` | Links to settlements |
| `dbk_account_number` | Account filtering |

#### settlements (s)
| Column | Usage |
|--------|-------|
| `settlement_id` | Links from settlement_transactions |
| `status` | Filter: skip already processed settlements |

### HAVING Clause Logic

The query filters transactions based on settlement history:

```sql
HAVING
    -- Case 1: Previous settlement failed and can be retried
    (COUNT(DISTINCT s.status) = 1
     AND MAX(CASE WHEN s.status IN ('failed','retryable_failure') THEN 1 ELSE 0 END) = 1
     AND COUNT(DISTINCT CASE WHEN s.status IN ('created','processing','payout','processed')
               THEN s.settlement_id ELSE NULL END) = 0)

    -- Case 2: Transaction was never part of any settlement
    OR COUNT(DISTINCT st.settlement_id) = 0
```

---

## Scheduler & Schedule Config

### Schedule Config Structure

**File:** `internal/config/service.go:261-273`

```go
type ScheduleConfig struct {
    Cycle       Cycle   // TPLUS0, TPLUS1, TPLUS2, TPLUSN
    CycleOffset int32   // Days offset for TPLUSN
    Interval    string  // Settlement frequency
}
```

### Cycle Types

**File:** `internal/settlement/workflow.go:312-351`

| Cycle | Description | End Time Calculation |
|-------|-------------|---------------------|
| `TPLUS0` | Same-day settlement | Now (or custom if provided) |
| `TPLUS1` | Next-day settlement | Today - 24 hours |
| `TPLUS2` | T+2 settlement | Today - 48 hours |
| `TPLUSN` | Custom offset | Today - (24 × CycleOffset) hours |

**Start Time:** Always 30 days before end time (lookback window)

### Schedule ID Usage

| Usage | Location | Purpose |
|-------|----------|---------|
| Deduplication | `repo.go:233` | Find existing settlement for same schedule |
| Cancel Pending | `core.go:584` | Cancel Draft/Initiated settlements |
| Settlement Entity | `helper.go:111` | Store in Settlement record |
| Querying | `repo.go` | Filter settlements by schedule |

### Time Range Calculation

```go
func getTransactionTimeRange(config *ScheduleConfig, startTimeUnix, endTimeUnix int64) (time.Time, time.Time) {
    // For TPLUS1:
    // endTime = today 23:59:59 IST - 24 hours
    // startTime = endTime - 30 days

    // If custom times provided, use those instead
}
```

---

## Transaction Processing Logic

**File:** `internal/settlement/core.go:222-301`

### Process Flow

```
┌─────────────────────────────────────┐
│  1. Fetch CSV from S3               │
│     - List objects in S3 prefix     │
│     - Filter .csv files             │
│     - Create MultiReader            │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  2. Parse Transactions              │
│     - gocsv.Unmarshal to memory     │
│     - Returns []*TransactionGroup   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  3. Cancel Pending Settlements      │
│     - Find Draft/Initiated          │
│     - Mark as Cancelled             │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  4. Create Initiated Settlement     │
│     - Generate SettlementID         │
│     - Status = Initiated            │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  5. Batch Processing Loop           │
│     For each chunk (BatchSize):     │
│     - Filter already-settled txns   │
│     - Validate group constraints    │
│     - Calculate amount breakup      │
│     - Create Transaction records    │
│     - Split if max amount reached   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  6. Update Settlement to Created    │
│     - Status = Created              │
│     - Ready for payout processing   │
└─────────────────────────────────────┘
```

### Amount Calculation

```
Net Amount = Total Amount - Fee Amount - Tax Amount

Where:
- Total Amount = Sum of PAYMENT, REFUND transactions (CREDIT adds, DEBIT subtracts)
- Fee Amount = Sum of MDR_FEE, MDR_REVERT transactions (negated)
- Tax Amount = Sum of TAX, TAX_REVERT transactions (negated)
```

### Batch Processing Rules

| Rule | Threshold | Action |
|------|-----------|--------|
| Batch Size | `TransactionsBatchSize` config | Persist batch, start new |
| Max Amount | `MaxAmountPerSettlement` config | Create new Settlement |
| Group Validation | Group size < BatchSize | Error if exceeded |
| Group Validation | Group amount < MaxAmount | Error if exceeded |

---

## Memory Considerations

### Current Implementation: Full In-Memory Load

| Step | Memory Behavior |
|------|-----------------|
| S3 GetObject | Streaming (good) |
| S3 Reader | Opens ALL streams upfront |
| parseTransactions | **Loads ENTIRE CSV into memory** |
| Batch Processing | Processes in chunks, but data already in memory |

### Code Path

```go
// 1. S3 Fetching - Returns streaming reader
func (c clientImpl) GetObject(ctx context.Context, key string) (io.ReadCloser, error) {
    output, _ := c.Client.GetObject(ctx, &s3.GetObjectInput{...})
    return output.Body, nil  // Streaming
}

// 2. S3 Reader - Opens ALL files upfront
func NewS3CSVPartsReader(ctx context.Context, client s3.Client, prefix string) (io.Reader, error) {
    for _, key := range keys {
        readers = append(readers, client.GetObject(ctx, key))  // All streams open
    }
    return io.MultiReader(readers...), nil
}

// 3. CSV Parsing - FULL MEMORY LOAD
func parseTransactions(r io.Reader) ([]*TransactionGroup, error) {
    var transactionGroups = make([]*TransactionGroup, 0)
    gocsv.Unmarshal(r, &transactionGroups)  // Entire CSV in memory
    return transactionGroups, nil
}
```

### Potential Issue

For partners with large transaction volumes, memory pressure may occur. The `BatchSize` configuration only controls database write batches, not initial memory load.

---

## Sequence Diagram

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ External │ │ gRPC     │ │ Workflow │ │ Query    │ │ S3       │ │ Database │
│ Caller   │ │ Server   │ │ Engine   │ │ Provider │ │          │ │          │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │            │            │
     │ SettleViaWorkflow       │            │            │            │
     │──────────────────────>│            │            │            │
     │            │            │            │            │            │
     │            │ Pre-Processing Validations          │            │
     │            │ (Lock, Holiday, Mode checks)        │            │
     │            │──────────────────────────────────────────────────>│
     │            │            │            │            │            │
     │            │ Start Workflow          │            │            │
     │            │──────────>│            │            │            │
     │            │            │            │            │            │
     │            │            │ AcquireOperationLock   │            │
     │            │            │──────────────────────────────────────>│
     │            │            │            │            │            │
     │            │            │ ExecuteQueryAsync      │            │
     │            │            │──────────>│            │            │
     │            │            │            │            │            │
     │            │            │            │ Build & Execute Query   │
     │            │            │            │ (CREATE TABLE → S3)     │
     │            │            │            │──────────────────────────>
     │            │            │            │            │            │
     │            │            │<───────────│            │            │
     │            │            │ StatementID            │            │
     │            │            │            │            │            │
     │            │            │ PollQueryStatus (loop) │            │
     │            │            │──────────>│            │            │
     │            │            │            │ Check Status            │
     │            │            │            │────────────>            │
     │            │            │            │<────────────            │
     │            │            │<───────────│            │            │
     │            │            │ (Retry until SUCCESS)  │            │
     │            │            │            │            │            │
     │            │            │ ProcessTransactions    │            │
     │            │            │─────────────────────────>            │
     │            │            │            │            │ List CSVs  │
     │            │            │            │            │<───────────│
     │            │            │            │            │            │
     │            │            │            │            │ Get Objects│
     │            │            │            │            │<───────────│
     │            │            │            │            │            │
     │            │            │ Parse CSV (in memory)  │            │
     │            │            │            │            │            │
     │            │            │ Cancel Pending Settlements          │
     │            │            │──────────────────────────────────────>│
     │            │            │            │            │            │
     │            │            │ Create Settlement (Status=Initiated) │
     │            │            │──────────────────────────────────────>│
     │            │            │            │            │            │
     │            │            │ Batch Process Transactions           │
     │            │            │──────────────────────────────────────>│
     │            │            │            │            │            │
     │            │            │ Update Settlement (Status=Created)   │
     │            │            │──────────────────────────────────────>│
     │            │            │            │            │            │
     │            │            │ Sub-workflows (Payout) │            │
     │            │            │───────────...          │            │
     │            │            │            │            │            │
     │            │            │ Cleanup    │            │            │
     │            │            │──────────────────────────────────────>│
     │            │            │            │            │            │
     │<───────────────────────│            │            │            │
     │ WorkflowResponse       │            │            │            │
     │            │            │            │            │            │
```

---

## Key Files Reference

### Core Flow Files

| File | Purpose |
|------|---------|
| `internal/settlement/server.go` | gRPC API endpoint (`SettleViaWorkflow`) |
| `internal/settlement/service.go` | Pre-processing validations |
| `internal/settlement/init_settlement.go` | Workflow definition & activities |
| `internal/settlement/core.go` | Query execution & transaction processing |
| `internal/settlement/factory.go` | Query provider selection |
| `internal/settlement/workflow.go` | Time range calculation |

### Query & Data Files

| File | Purpose |
|------|---------|
| `internal/databricks/query.go` | SQL query templates |
| `internal/databricks/dao.go` | Query builder, transaction parsing |
| `internal/s3/reader.go` | S3 CSV reading |
| `internal/settlement/databricks.go` | CSV to TransactionGroup parsing |

### Model & Helper Files

| File | Purpose |
|------|---------|
| `internal/settlement/model.go` | Settlement entity |
| `internal/settlement/dto.go` | Request/Response DTOs, TransactionGroup |
| `internal/settlement/helper.go` | Amount calculation, S3 paths |
| `internal/transactiongroup/model.go` | TransactionGroup entity |
| `internal/config/service.go` | Schedule config retrieval |

### Configuration

| File | Purpose |
|------|---------|
| `internal/boot/config/` | Application configuration structures |
| `internal/commons/constant.go` | Constants (Databricks, BatchPlatform, etc.) |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Query execution failure | Retry up to 5 times |
| Query timeout (30min) | Workflow restarts with `ContinueAsNew` if retries remain |
| S3 fetch failure | Retry up to 5 times |
| Transaction group exceeds batch size | NonRetryable error, workflow fails |
| Transaction group exceeds max amount | NonRetryable error, workflow fails |
| Workflow failure | Cleanup activity marks settlements as Skipped |

---

## Configuration Parameters

| Parameter | Location | Purpose |
|-----------|----------|---------|
| `QueryProvider` | Tenant Config | Databricks or BatchPlatform |
| `PipelineName` | Tenant Config | BatchPlatform pipeline name |
| `TransactionsBatchSize` | Processor Config | DB write batch size |
| `MaxAmountPerSettlement` | Config Service | Split threshold for settlements |
| `Cycle` | Schedule Config | T+0, T+1, T+2, T+N |
| `CycleOffset` | Schedule Config | Days offset for T+N |
