# Payment Service (Darwin) - Expert Study Guide

A comprehensive guide to understanding the payment-service repository.

---

## 1. OVERVIEW & TECH STACK

**Project Name:** Darwin (internal name for payment-service)
**Purpose:** Enterprise-grade payment processing microservice handling multi-provider payment orchestration

| Technology | Version | Purpose |
|------------|---------|---------|
| Java | 17 | Runtime |
| Spring Boot | 2.7.14 | Framework |
| Gradle | 7.6 | Build |
| MySQL | - | Primary Database (Master-Replica) |
| DynamoDB | - | Audit/State Storage |
| Redis (Redisson) | 3.19.1 | Distributed Cache |
| Kafka | - | Event Streaming |
| AWS SQS | - | Task Processing |

**Server:** Port 9010, Context Path: `/payments`

---

## 2. PROJECT STRUCTURE

```
payment-service/
├── src/main/java/in/dreamplug/darwin/
│   ├── controller/         # REST API endpoints
│   │   └── v2/             # V2 API controllers (primary)
│   ├── service/            # Business logic services
│   ├── v2/
│   │   ├── service/        # V2 services
│   │   └── workflow/       # Payment workflows (CRITICAL)
│   │       └── create/
│   │           ├── payments/       # Payment creation
│   │           ├── paymentattempts/ # Payment attempt creation
│   │           └── providers/      # Provider adapters (24+)
│   ├── entity/             # JPA entities
│   │   └── v2/             # V2 entities (primary)
│   ├── repository/         # Data access layer
│   ├── statemachine/       # Payment/Order state machines
│   ├── planner/            # Decision tree routing
│   ├── cache/              # Caching layer (Caffeine)
│   ├── client/             # External service clients
│   ├── provider/           # Legacy provider implementations
│   ├── configuration/      # Spring configs
│   │   └── database/       # DB configs (Master/Replica)
│   ├── kafka/              # Kafka producers/consumers
│   ├── sqs/                # SQS message processors
│   ├── dynamo/             # DynamoDB DAOs
│   ├── error/              # Error handling
│   ├── dto/                # Data transfer objects
│   └── commons/spring/filters/  # Auth/Context filters
├── src/main/resources/
│   └── application.properties  # Main config (1300+ lines)
├── codepipeline/           # CI/CD configurations
├── build.gradle            # Dependencies
└── Dockerfile              # Container setup
```

---

## 3. CORE PAYMENT FLOW (CRITICAL)

### 3.1 Payment Lifecycle

```
Order Created → Payments Created → Payment Attempt Created → Provider API Call → Webhook/Status Update
```

**Key Steps:**

1. **Order Creation** - Client creates an order with amount, currency, metadata
2. **Bulk Payment Creation** - Multiple payment records created for the order
   - File: `v2/workflow/create/payments/bulk/BulkPaymentCreateWorkflow.java`
3. **Payment Attempt Creation** - Actual payment attempt with provider routing
   - File: `v2/workflow/create/paymentattempts/PaymentAttemptCreateWorkflow.java`
4. **Provider Processing** - Provider adapter calls external payment gateway
5. **State Machine Updates** - Events trigger state transitions

### 3.2 Workflow Execution Pipeline

```java
// Base workflow pattern (Workflow.java)
1. validateAndEnrichContext()  // Validate inputs, enrich data
2. persistIntent()             // Save entities to MySQL
3. persistNonRelationalIntent() // Save to DynamoDB
4. process()                   // Call provider API
5. postProcess()               // Transform results
6. publishEntityChangeEvents() // Trigger state machines
7. throwErrorIfRequired()      // Handle errors
```

### 3.3 Payment Attempt Data Enrichment

1. **Instrument Validation** - `InstrumentTypeProcessorManager`
2. **Provider Routing** - `ProviderDeciderRouter` → Decision Tree
3. **Auth Type Decision** - `AuthTypeDeciderFactory` (3DS, OTP, None)
4. **Settlement Validation** - `SettlementRouteValidator`

---

## 4. STATE MACHINES

### 4.1 Payment State Machine
**File:** `statemachine/payment/PaymentStateMachine.java`

```
CREATED → PROCESSING → AUTHORIZED → COMPLETED
                   ↘ FAILED
                   ↘ BLOCKED
```

**Terminal States:** COMPLETED, FAILED, FORCE_FAILED, DISCARDED

### 4.2 Order State Machine
**File:** `statemachine/order/OrderStateMachine.java`

- Reacts to payment events
- Updates order status based on payment outcomes

### 4.3 Events (EventBus - Guava)
- `PaymentAttemptCreatedEvent`
- `PaymentAttemptCompletedEvent`
- `PaymentAttemptFailedEvent`
- `PaymentAttemptProcessingEvent`
- `PaymentAttemptAuthorizedEvent`

---

## 5. PROVIDER INTEGRATIONS (24+ Providers)

**Location:** `v2/workflow/create/providers/`

| Provider | Adapter File | Payment Types |
|----------|-------------|---------------|
| Cybersource | `CybersourceProviderAdapter.java` | Cards, 3DS, E-Mandates |
| Cashfree | `CashfreeProviderAdapter.java` + variants | Cards, UPI, NetBanking |
| PayU | `PayuProviderAdapter.java` + variants | Cards, NetBanking |
| Pine Labs | `PineLabsEdgeProviderAdapter.java` | Multiple modes |
| Razorpay | Via webhooks | All payment types |
| Juspay | Via webhooks | Orchestration |
| ICICI UPI | `icici-upi-client` | UPI |
| Axis UPI | `axis-upi-client` | UPI |
| YBL UPI | `ybl-upi-client` | UPI |
| RBL UPI | `rbl-upi-client` | UPI |
| Digio | `DigioMandateRegisterProviderAdapter.java` | E-Mandates |
| Cred Points | `CredPointsProviderAdapter.java` | Reward redemption |

### Provider Selection Flow

```
Request → ProviderDeciderRouter → LCM (if enabled) → Decision Tree → Provider Adapter
```

**Decision Tree:** JSON-based rules cached in `DecisionTreeObjectCache`

---

## 6. KEY ENTITIES (V2 Schema)

### Core Entities
| Entity | File | Purpose |
|--------|------|---------|
| OrderEntity | `entity/OrderEntity.java` | Order records |
| PaymentV2Entity | `entity/v2/PaymentV2Entity.java` | Payment records |
| PaymentAttemptV2Entity | `entity/v2/PaymentAttemptV2Entity.java` | Payment attempts |
| RefundEntity | `entity/v2/RefundEntity.java` | Refunds |
| FeeEntity | `entity/v2/FeeEntity.java` | Fee tracking |

### Configuration Entities
| Entity | Purpose |
|--------|---------|
| ClientEntity | Application clients |
| ProviderAccountEntity | Provider accounts |
| PaymentProviderEntity | Provider configs |
| MasterConfigurationEntity | System configs |

---

## 7. DATABASE ARCHITECTURE

### Master-Replica Pattern

**Master:** Write operations
**Replica:** Read operations (via `@ReplicaRepository`)

**Configuration Files:**
- `configuration/database/MasterDataSourceConfiguration.java`
- `configuration/database/ReplicaDataSourceConfiguration.java`

**Database:** `payments_multi_tenancy`
**Connection Pool:** HikariCP
**ORM:** JPA + Hibernate

---

## 8. CACHING LAYER

### Caffeine (In-Memory)
| Cache | Purpose |
|-------|---------|
| `ClientConfigurationCache` | Client settings |
| `PaymentProviderCache` | Provider configs |
| `ProviderAccountCache` | Provider accounts |
| `DecisionTreeObjectCache` | Routing rules |
| `CardBinCache` | Card BIN data |
| `MerchantCache` | Merchant data |
| `FeeCache` | Fee calculations |

### Redis (Distributed)
- **Client:** Redisson with Kryo5Codec
- **Use:** Distributed locks, rate limiting, shared state

---

## 9. ASYNC PROCESSING

### Kafka Topics
- `payment-attempt-platform-metrics-pinot-out-new-1` (Analytics)
- Events: `PaymentAttemptAnalyticsEvent`, `CardPaymentAttemptAnalyticsEvent`, etc.

### SQS Queues
| Queue | Purpose |
|-------|---------|
| `FORCE_PAYMENT_FAILURE_QUEUE` | Manual failure forcing |
| `MANDATE_EXPIRY_CRON_QUEUE` | Mandate expiry |
| `REFUND_RESCHEDULE_QUEUE` | Refund scheduling |
| `ORDER_EXPIRY_QUEUE` | Order expiration |
| `PENDENCY_AUTOMATION_QUEUE` | Pending transactions |

### Eventi (Internal Events)
- Internal event framework for system events
- Async worker threads (4-16 configurable)

---

## 10. API ENDPOINTS

### Primary Controllers (v2)
| Endpoint | Controller | Purpose |
|----------|------------|---------|
| `/v2/orders/{orderId}/payments` | `PaymentV2Controller` | Bulk payment creation |
| `/v2/payments/{paymentId}/attempts` | `PaymentAttemptV2Controller` | Payment attempts |
| `/v1/webhooks` | `WebhookController` | Provider webhooks |

### Webhook Controllers
- `RazorpayWebhookController`
- `JuspayWebhookController`
- `ICICIWebhookController`
- `YBLWebhookController`
- `RBLUpiWebhookController`
- `DigioWebhookController`

---

## 11. AUTHENTICATION & SECURITY

### Request Filters (Order of Execution)
1. `ApplicationContextBuilderFilter` - Build context from headers
2. `PAMerchantAuthenticationFilter` - Partner merchant auth
3. `PAPartnerAuthorizationFilter` - Partner authorization

### Headers Required
- Client ID (`${CLIENT_HEADER_KEY}`)
- Merchant ID (`${MERCHANT_HEADER_KEY}`)
- Device info (DEVICE_ID, OS, OS_VERSION, APP_VERSION)

### Rate Limiting
- Redisson-based distributed rate limiting
- Config in `ClientRateLimiter.java`

---

## 12. KEY FILES TO STUDY

### Must-Read Files (Priority Order)

1. **Entry Point:**
   - `DarwinApplication.java`

2. **Core Workflows:**
   - `v2/workflow/create/Workflow.java` (base pattern)
   - `v2/workflow/create/paymentattempts/PaymentAttemptCreateWorkflow.java`
   - `v2/workflow/create/payments/bulk/BulkPaymentCreateWorkflow.java`

3. **State Machines:**
   - `statemachine/payment/PaymentStateMachine.java`
   - `statemachine/order/OrderStateMachine.java`

4. **Provider Routing:**
   - `planner/ProviderDeciderRouter.java`
   - `planner/decisiontree/DecisionTreeWorkflow.java`

5. **Provider Adapters:**
   - `v2/workflow/create/providers/` (pick any adapter)

6. **Entities:**
   - `entity/OrderEntity.java`
   - `entity/v2/PaymentV2Entity.java`
   - `entity/v2/PaymentAttemptV2Entity.java`

7. **Configuration:**
   - `application.properties` (1300+ lines - scan for context)

8. **Webhooks:**
   - `controller/WebhookController.java`

---

## 13. INTERNAL SERVICE DEPENDENCIES

| Service | Client Library | Purpose |
|---------|---------------|---------|
| User Service | `user-service-client:4.0.1` | User data |
| Merchant Service | `merchant-service-client:1.0.3` | Merchant info |
| Mandate Service | `mandate-java-client:1.0.4` | Recurring payments |
| Arsenal | - | Instrument vault |
| Falcon | - | Offers/promotions |
| Genie | `genie-java-client` | Configuration |
| Syndicate | - | Authentication |
| LCM | - | Terminal resolution |
| Fee Service | `fees:0.18.0` | Fee calculation |

---

## 14. STUDY PATH RECOMMENDATION

### Week 1: Foundation
- [ ] Understand project structure
- [ ] Read `DarwinApplication.java`
- [ ] Study `application.properties` (key sections)
- [ ] Understand entity relationships

### Week 2: Core Flow
- [ ] Master `PaymentAttemptCreateWorkflow.java`
- [ ] Study state machines
- [ ] Understand provider routing

### Week 3: Integrations
- [ ] Study 2-3 provider adapters
- [ ] Understand webhook handling
- [ ] Learn caching patterns

### Week 4: Advanced
- [ ] Decision tree engine
- [ ] Async processing (Kafka, SQS)
- [ ] Error handling patterns

---

## 15. KEY CONCEPTS

1. **Multi-Provider Orchestration** - Route to optimal provider based on rules
2. **Decision Trees** - JSON-based routing logic
3. **State Machines** - Event-driven entity lifecycle
4. **Master-Replica DB** - Read/write separation
5. **Workflow Pattern** - 7-step execution pipeline
6. **Event-Driven Architecture** - Guava EventBus + Kafka

---

# DATA LAYER DEEP-DIVE

## 16. ENTITY HIERARCHY & INHERITANCE

### Base Classes
```
BaseEntity (id, created_at, updated_at, created_by, updated_by)
    └── BaseExternalEntity (+ external_id UUID, version for optimistic locking)
            ├── OrderEntity
            ├── PaymentV2Entity
            ├── PaymentAttemptV2Entity
            ├── RefundEntity
            ├── ClientEntity
            └── CustomerEntity
```

### Key Entity Files
| Entity | File | Key Fields |
|--------|------|------------|
| OrderEntity | `entity/OrderEntity.java` | clientReferenceId, amount, status, metadata (JSON) |
| PaymentV2Entity | `entity/v2/PaymentV2Entity.java` | orderId, amount, paymentMode, instrumentDetail (JSON) |
| PaymentAttemptV2Entity | `entity/v2/PaymentAttemptV2Entity.java` | paymentId, providerReferenceId, gatewayReferenceId, status |
| RefundEntity | `entity/v2/RefundEntity.java` | orderId, paymentAttemptId, refundType, refundStatus |
| ClientEntity | `entity/ClientEntity.java` | name, merchantId, settings (OneToMany) |

### Entity Relationships
```
ClientEntity (1) ──> (M) OrderEntity
OrderEntity (1) ──> (M) PaymentV2Entity
PaymentV2Entity (1) ──> (M) PaymentAttemptV2Entity
PaymentAttemptV2Entity ──> PaymentProviderEntity
PaymentAttemptV2Entity ──> ProviderAccountEntity
OrderEntity (1) ──> (M) RefundEntity
RefundEntity (1) ──> (M) RefundAttemptEntity
```

---

## 17. MASTER-REPLICA DATABASE ARCHITECTURE

### How Routing Works

**Master (Writes):** `MasterDataSourceConfiguration.java`
- EntityManagerFactory: `MasterEntityManagerFactory`
- TransactionManager: `MasterTransactionManager`
- Excludes beans with `@ReplicaRepository`

**Replica (Reads):** `ReplicaDataSourceConfiguration.java`
- EntityManagerFactory: `ReplicaEntityManagerFactory`
- TransactionManager: `ReplicaTransactionManager`
- Includes ONLY beans with `@ReplicaRepository`
- Connection pool set to `readOnly=true`

### Usage Pattern
```java
// Write to master (default)
@Repository
public interface PaymentRepository extends JpaRepository<...> {}

// Read from replica
@Repository
@ReplicaRepository  // <-- Annotation routes to replica
public class RefundEntityReplicaDAOImpl extends AbstractReplicaDAOImpl<...> {}
```

### HikariCP Connection Pools
| Pool | Config | Purpose |
|------|--------|---------|
| hikari_master | masterMinimumIdle, masterMaximumPoolSize | Write operations |
| hikari_replica | replicaMinimumIdle, replicaMaximumPoolSize, readOnly=true | Read operations |

Both pools have:
- idleTimeout, connectionTimeout, maxLifetime
- leakDetectionThreshold for debugging
- MaintenanceManager integration for graceful shutdown

---

## 18. REPOSITORY & DAO PATTERNS

### JPA Repository Pattern
```java
@Repository
public interface OrderRepository extends JpaRepository<OrderEntity, Long> {
    // FETCH JOIN to prevent N+1 queries
    @Query("SELECT o FROM OrderEntity o "
            + "JOIN FETCH o.customerEntity "
            + "JOIN FETCH o.clientEntity "
            + "WHERE o.externalId = :externalId")
    Optional<OrderEntity> findByExternalId(@Param("externalId") String externalId);

    // Property path navigation
    Optional<OrderEntity> findByClientReferenceIdAndClientEntity_ExternalId(
            String clientReferenceId, String externalId);
}
```

### DAO Pattern (Custom EntityManager)
```java
@Repository
public class PaymentAttemptDAOV2Impl {
    @PersistenceContext
    private EntityManager entityManager;

    public List<PaymentAttemptV2Entity> findByOrderId(Long orderId) {
        // Complex JPQL with manual EntityManager
    }
}
```

### DynamoDB DAO Pattern
```java
@RequiredArgsConstructor
public abstract class AbstractDynamoDBDAO<T> {
    private final DynamoDBMapper dynamoDBMapper;

    public void save(T entity) { dynamoDBMapper.save(entity); }
    public T findByHashKey(Object hashKey) { return dynamoDBMapper.load(tClass, hashKey); }
}
```

---

## 19. JSON COLUMNS & CONVERTERS

**Flexible Attribute Storage:**
| Column | Converter | Entity |
|--------|-----------|--------|
| metadata | ObjectMetadataMapConverter | OrderEntity |
| instrument_detail | PaymentInstrumentConverter | PaymentV2Entity |
| instrument_detail | EnrichedPaymentInstrumentConverter | PaymentAttemptV2Entity |
| routes | RoutesBreakupConverter | PaymentAttemptV2Entity |
| payment_specific_detail | PaymentSpecificDetailConverter | PaymentV2Entity |

```java
@Column(name = "metadata")
@Convert(converter = ObjectMetadataMapConverter.class)
private Map<String, String> metaData;
```

---

## 20. CACHING ARCHITECTURE

### Caffeine Caches (In-Memory)
| Cache Class | What It Caches | TTL |
|-------------|----------------|-----|
| ClientConfigurationCache | Client settings by ID, by externalId, by merchantId | 10-20 min |
| PaymentProviderCache | Provider configurations | 15-25 min |
| ProviderAccountCache | Provider account entities | 15-25 min |
| DecisionTreeObjectCache | Routing decision trees | 180-190 min |
| FeeCache | Fee configurations | 1 day |
| CardBinCache | Card BIN details | Configurable |
| MasterConfigurationCache | Feature flags, system settings | 10-20 min |
| PaymentErrorMessageMappingCache | Error code to message mappings | Long |

### Cache Pattern
```java
@DPCache(cacheName = "client_configuration_cache")
private LoadingCache<Long, Map<ClientSettingKey, String>> idCache;

@Override
public void buildCache() {
    idCache = DPCacheBuilder.getBuilder()
        .refreshAfterWrite(10, MINUTES)  // Lazy refresh
        .build(this::loadClientSettings);  // Loader function
}
```

### Jittered TTLs (Prevent Thundering Herd)
```java
// Returns 15-25 instead of fixed 15
private Long generateRandomCacheRefreshInterval(int base) {
    return base + random.nextInt(10) + 1;
}
```

---

## 21. DYNAMODB USAGE

### What Goes Where
| MySQL | DynamoDB |
|-------|----------|
| Orders, Payments, Attempts | Workflow context (TTL-based) |
| Refunds, Fees | Native OTP details |
| Clients, Customers | Redirect tracking |
| Provider configs | Metadata audit trails |

### DynamoDB Entity Example
```java
@DynamoDBTable(tableName = "darwin_payment_attempt_workflow_context")
public class PaymentAttemptWorkflowContextEntity {
    @DynamoDBHashKey(attributeName = "payment_attempt_external_id")
    private String paymentAttemptExternalId;

    @DynamoDBRangeKey
    @DynamoDBAttribute(attributeName = "workflow_step")
    private WorkflowStep workflowStep;

    @Builder.Default
    private long ttl = LocalDateTime.now().plusDays(1).toEpochSecond(ZoneOffset.UTC);
}
```

### DynamoDB Tables
| Table | Partition Key | Sort Key | Purpose |
|-------|---------------|----------|---------|
| darwin_payment_attempt_workflow_context | payment_attempt_external_id | workflow_step | Workflow state |
| darwin_payment_attempt_native_otp_detail | payment_attempt_external_id | - | OTP auth details |
| darwin_payment_attempt_redirection_detail | payment_attempt_external_id | - | 3DS redirects |
| darwin_payment_attempt_metadata_audit | payment_attempt_external_id | - | Audit trail |

---

## 22. OPTIMISTIC LOCKING & AUDIT

### @Version for Optimistic Locking
```java
@Version
@Column(name = "version")
private Integer version;  // Auto-incremented on each update
```

Prevents concurrent modification - throws `OptimisticLockException` on conflict.

### Audit Columns (Auto-Managed)
```java
@CreationTimestamp
@Column(name = "created_at")
private LocalDateTime createAt;

@UpdateTimestamp
@Column(name = "updated_at")
private LocalDateTime updatedAt;

@PrePersist
public void onCreate() {
    createdBy = ApplicationContext.getApplicationName();
}

@PreUpdate
public void onUpdate() {
    updatedBy = ApplicationContext.getApplicationName();
}
```

---

## 23. DATA LAYER ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                        │
├─────────────────────────────────────────────────────────┤
│ JPA Repositories      │ Custom DAOs      │ DynamoDB DAOs │
├─────────────────────────────────────────────────────────┤
│     Spring Data JPA + Hibernate ORM                     │
├──────────────────────┬──────────────────────────────────┤
│   Master DataSource  │      Replica DataSource          │
│   (Writes)           │      (Reads - @ReplicaRepository)│
├──────────────────────┼──────────────────────────────────┤
│ HikariCP Master Pool │   HikariCP Replica Pool          │
├──────────────────────┴──────────────────────────────────┤
│         MySQL (payments_multi_tenancy)                  │
└─────────────────────────────────────────────────────────┘
         │                              │
┌────────▼────────┐          ┌──────────▼─────────┐
│    DynamoDB     │          │  Caffeine Caches   │
│ (Workflow/Audit)│          │  (Client/Provider) │
└─────────────────┘          └────────────────────┘
```

---

## 24. KEY DATA LAYER FILES TO STUDY

### Entity Classes (Priority)
1. `entity/commons/BaseEntity.java` - Base class pattern
2. `entity/provider/BaseExternalEntity.java` - External ID + versioning
3. `entity/OrderEntity.java` - Main order entity
4. `entity/v2/PaymentAttemptV2Entity.java` - Payment attempt (most complex)

### Database Configuration
1. `configuration/database/MasterDataSourceConfiguration.java`
2. `configuration/database/ReplicaDataSourceConfiguration.java`
3. `configuration/database/annotation/ReplicaRepository.java`

### Repositories
1. `repository/OrderRepository.java` - FETCH JOIN examples
2. `repository/PaymentAttemptRepository.java` - Complex queries

### Caches
1. `cache/ClientConfigurationCache.java` - Cache pattern example
2. `configuration/CacheConfig.java` - Cache configuration

### DynamoDB
1. `dynamo/dao/AbstractDynamoDBDAO.java` - Base DAO pattern
2. `dynamo/domain/PaymentAttemptWorkflowContextEntity.java` - DynamoDB entity

---

# PROVIDER INTEGRATION DEEP-DIVE

## 25. PROVIDER ADAPTER ARCHITECTURE

### Base Adapter Pattern
**File:** `v2/workflow/create/providers/IPaymentProviderAdapter.java`

```java
public abstract class IPaymentProviderAdapter<T, R> implements SelfReferencingBean {
    protected final PaymentProviderKey paymentProviderKey;  // e.g., CASHFREE, CYBERSOURCE
    private final InstrumentType instrumentType;            // e.g., CARD, UPI_APPS
    private final OrderType orderType;                      // e.g., PAY, REFUND

    // Core lifecycle methods
    public abstract ProviderPaymentResponse createPaymentAttempt(context, customerEntity);
    protected abstract Object syncPaymentAttemptWithProviderId(paymentAttemptEntity);
    protected abstract ProviderRefundCreateResponse createRefund(refundAttemptEntity, context);
    protected abstract R getAuthConfig(providerAccountEntity);
}
```

### Factory Pattern for Adapter Selection
**File:** `v2/workflow/create/providers/PaymentProviderFactory.java`

```java
@Component
public class PaymentProviderFactory {
    // Multi-dimensional lookup: OrderType + ProviderKey + InstrumentType → Adapter
    private Map<PaymentWorkflowKey, IPaymentProviderAdapter<?, ?>> paymentProviderMap;

    // Secondary lookup: OrderType + ProviderKey → First adapter
    private Table<OrderType, PaymentProviderKey, IPaymentProviderAdapter<?, ?>> paymentProviderByKey;

    // 3DS variant support
    private ThreeDSType threeDSType;  // 3DS1 vs 3DS2
}
```

### Provider Response Structure
```java
@Data @Builder
public class ProviderPaymentResponse {
    private Object providerResponseObject;     // Raw provider response
    private String providerReferenceId;        // Provider's transaction ID
    private String gatewayReferenceId;         // Gateway ID
    private String providerStatus;             // Raw status ("SUCCESS")
    private PaymentAttemptStatus status;       // Mapped internal status
    private ProviderRequestStatus providerRequestStatus;  // REQUEST_SUCCESS, RETRY_ABLE_FAILURE
    private ProviderError providerError;       // Error details if failed
}
```

---

## 26. DECISION TREE ROUTING

### Router Strategy Pattern
**File:** `planner/providerdecider/ProviderDeciderRouter.java`

```java
@Service
public class ProviderDeciderRouter {
    public ProviderRoutingDecisionResult resolve(PaymentAttemptCreateContext context) {
        // Priority 1: LCM routing (if instrument supported)
        if (isInstrumentTypeSupportedInLCM(clientId, instrumentType)) {
            return providerDeciderViaLCM.decideProvider(context);
        }

        // Priority 2: Decision Tree routing
        if (isDecisionTreeEnabled) {
            return providerDeciderV2.decideProvider(context);
        }
    }
}
```

### Decision Tree Workflow
**File:** `planner/providerdecider/ProviderDeciderV2.java`

```
Request → Fetch Cached Decision Tree → Create DT Context → Execute Tree → Apply Dynamic Routing → Return Provider
```

**Decision Tree Factors:**
- Client configuration
- Instrument type (Card, UPI, NetBanking)
- Card brand/BIN
- Customer attributes
- Order amount
- Provider availability/downtime

### Decision Tree Caching
**File:** `cache/DecisionTreeObjectCache.java`

| Cache | TTL | Content |
|-------|-----|---------|
| decision_tree_object_cache | 180-190 min | Parsed decision tree JSON + workflow |

---

## 27. PROVIDER ADAPTERS (24+ Implementations)

### Adapter Directory Structure
```
v2/workflow/create/providers/
├── IPaymentProviderAdapter.java          # Base abstract class
├── PaymentProviderFactory.java           # Factory for adapter selection
├── CashfreeProviderAdapter.java          # Cashfree base
├── CashfreeCardProviderAdapter.java      # Cashfree cards
├── CashfreeNetBankingProviderAdapter.java
├── CashfreeUPIProviderAdapter.java
├── CashfreeUPIAppsProviderAdapter.java
├── cybersource/
│   ├── CybersourceProviderAdapter.java   # Cybersource base (3DS)
│   ├── CybersourceRequestBuilder.java    # Request construction
│   └── CybersourceAuthorizeRequestBuilder.java
├── PayuProviderAdapter.java
├── PayuCardProviderAdapter.java
├── PineLabsEdgeProviderAdapter.java
├── CredPointsProviderAdapter.java
├── RewardPointsProviderAdapter.java
└── AuthTokenNativeProviderAdapter.java
```

### Cashfree Adapter Example
**File:** `v2/workflow/create/providers/CashfreeProviderAdapter.java`

```java
@Component
public abstract class CashfreeProviderAdapter
        extends IPaymentProviderAdapter<String, CashfreeAuthConfig> {

    // Two-phase payment creation:
    // 1. Create order at Cashfree
    // 2. Create payment for that order

    @Override
    public ProviderPaymentResponse createPaymentAttempt(context, customer) {
        // Phase 1: Create CF Order
        Pair<BaseResponse<CreateOrderResponse>, ProviderError> orderResponse =
            createCFOrder(context, authConfig);

        // Phase 2: Create CF Payment
        Pair<BaseResponse<CreatePaymentResponse>, ProviderError> paymentResponse =
            createCFPayment(context, orderResponse.getLeft().getResponse(), authConfig);

        return mapToProviderPaymentResponse(paymentResponse);
    }
}
```

### Cybersource Adapter (3DS Support)
**File:** `v2/workflow/create/providers/cybersource/CybersourceProviderAdapter.java`

```java
@Component
public abstract class CybersourceProviderAdapter
        extends I3DSPaymentProviderAdapter<String, AuthConfig> {

    // Status code mappings
    private static final List<String> FAILED_STATUSES = Arrays.asList(
        "101", "102", "104", "150", "200", "201", ...  // 43 codes
    );
    private static final List<String> PROCESSING_STATUSES = Arrays.asList(
        "110", "475", "480"
    );

    // 3DS2 redirection flow
    protected void createRedirectionHtml(response, paymentAttemptEntity) {
        if (authInfo.getSpecificationVersion().startsWith("2")) {
            // 3DS2 flow with step-up URL
            html = authenticationService.createAuthenticationPageFor3ds2(
                authInfo.getStepUpUrl(),
                authInfo.getAccessToken(),
                paymentAttemptEntity.getExternalId());
        }
    }
}
```

---

## 28. WEBHOOK HANDLING

### Webhook Architecture
```
Provider → /webhooks/v2/{provider} → Provider-Specific Controller → WebhookService → State Machine Update
```

### Provider Webhook Controllers
| Endpoint | Controller | Provider |
|----------|------------|----------|
| `/webhooks/v2/cashfree` | CashfreeWebhookController | Cashfree |
| `/webhooks/v2/razorpay` | RazorpayWebhookController | Razorpay |
| `/webhooks/v2/payu` | PayuWebhookController | PayU |
| `/webhooks/v2/cybersource` | CybersourceWebhookController | Cybersource |
| `/webhooks/v2/juspay` | JuspayWebhookController | Juspay |
| `/webhooks/v2/ybl` | YBLWebhookController | Yes Bank UPI |
| `/webhooks/v2/icici` | ICICIWebhookController | ICICI UPI |
| `/webhooks/v2/rbl-upi` | RBLUpiWebhookController | RBL UPI |
| `/webhooks/v2/digio` | DigioWebhookController | Digio (eMandate) |

### Webhook Processing Flow
**File:** `controller/v2/CashfreeWebhookController.java`

```java
@PostMapping
public void onWebhookReceive(@RequestBody CashfreeWebhook webhookRequest) {
    switch (webhookRequest.getType()) {
        case PAYMENT_SUCCESS_WEBHOOK:
        case PAYMENT_FAILED_WEBHOOK:
            // 1. Extract provider reference ID
            String providerRefId = paymentWebhook.getData().getCfPaymentId();

            // 2. Fetch payment attempt
            PaymentAttempt attempt = paymentAttemptFetchWorkflow
                .fetchByProviderReferenceId(providerRefId);

            // 3. Audit webhook data
            auditService.auditProviderData(webhookRequest, attempt.getId(), ...);

            // 4. Sync status (triggers state machine)
            break;

        case REFUND_STATUS_WEBHOOK:
            processRefundAttempt(webhookRequest);
            break;
    }
}
```

### Idempotency Handling
```java
// In base adapter - only update if status actually changed
public void syncPaymentAttemptWithProvider(PaymentAttemptV2Entity entity) {
    String currentStatus = entity.getProviderStatus();

    Object providerResponse = syncPaymentAttemptWithProviderId(entity);

    // Only audit and process if status changed
    if (!Objects.equals(currentStatus, entity.getProviderStatus())) {
        auditService.auditProviderData(...);
    }
}
```

---

## 29. PROVIDER CONFIGURATION

### Configuration Entities
**File:** `entity/ProviderAccountEntity.java`

```java
@Entity @Table(name = "provider_accounts")
public class ProviderAccountEntity extends BaseEntity {
    @ManyToOne
    private PaymentProviderEntity paymentProvider;

    private String providerAccountId;     // e.g., "ACC_123456"

    @Lob
    private byte[] accessToken;           // Encrypted credentials

    private String endpoint;              // Provider API endpoint
    private Boolean isProd;               // Production vs Sandbox
    private Boolean active;
    private String additionalConfig;      // JSON configuration
    private String providerMid;           // Merchant ID at provider
    private String settlementCategory;    // Settlement routing
}
```

### Provider-Specific Configurations
```java
// Cashfree
@Data
public class CashfreeProviderAccountConfiguration {
    private String apiClientId;
    private String apiVersion;
    private ShortCircuitConfiguration shortCircuitConfiguration;
}

// Cybersource
@Data
public class CybersourceProviderAccountConfiguration {
    private String apiKey;
    private String merchantId;
    private Boolean enableRetries = false;
    private Boolean enableCaptureWithAuth = true;
    private Boolean enable3DS2 = true;
    private Boolean enableRedirectionFlow = false;
}
```

### Client-Provider Mapping
**File:** `entity/ClientPaymentProviderConfigEntity.java`

```java
@Entity @Table(name = "client_payment_provider_config")
public class ClientPaymentProviderConfigEntity extends BaseEntity {
    @ManyToOne private ClientEntity client;
    @ManyToOne private PaymentProviderEntity paymentProvider;
    private String providerConfig;  // JSON configuration per client
}
```

---

## 30. ERROR HANDLING & RETRY LOGIC

### Error Classification
```java
public enum ProviderRequestStatus {
    REQUEST_SUCCESS,          // Payment processed
    RETRY_ABLE_FAILURE,       // Timeout, rate limit - can retry
    NON_RETRY_ABLE_FAILURE    // Invalid request - cannot retry
}
```

### Provider Error Structure
```java
@Data @Builder
public class ProviderError {
    private String message;           // User-friendly message
    private String code;              // Provider error code
    private Object providerResponse;  // Raw error response
    private Boolean retryable;        // Retry classification
}
```

### Error Code Mapping (Cybersource Example)
```java
// Failure codes (43 codes)
"101", "102", "104", "150", "200", "201", "202", "203", ...

// Processing/Pending codes
"110" (Pending), "475" (Timeout), "480" (Processing)
```

### Retry Pattern
```java
public ProviderPaymentResponse executePaymentAttempt(...) {
    try {
        return pilotMethod.apply(context, providerCustomer);
    } catch (RateLimitException rle) {
        return ProviderPaymentResponse.builder()
            .providerRequestStatus(ProviderRequestStatus.RETRY_ABLE_FAILURE)
            .providerError(ProviderError.builder()
                .retryable(true).build())
            .build();
    } catch (AppException ae) {
        return ProviderPaymentResponse.builder()
            .providerRequestStatus(ProviderRequestStatus.NON_RETRY_ABLE_FAILURE)
            .build();
    }
}
```

---

## 31. ARCHITECTURAL PATTERNS SUMMARY

| Pattern | Usage | File |
|---------|-------|------|
| **Factory** | Adapter selection by (OrderType, Provider, Instrument) | PaymentProviderFactory.java |
| **Strategy** | LCM vs Decision Tree routing | ProviderDeciderRouter.java |
| **Template Method** | Base adapter lifecycle | IPaymentProviderAdapter.java |
| **Builder** | Complex request construction | CybersourceRequestBuilder.java |
| **Decorator** | Provider-specific configuration | *ConfigValueDecoratorImpl.java |

---

## 32. KEY PROVIDER INTEGRATION FILES

### Core Architecture
1. `v2/workflow/create/providers/IPaymentProviderAdapter.java` - Base adapter
2. `v2/workflow/create/providers/PaymentProviderFactory.java` - Factory
3. `planner/providerdecider/ProviderDeciderRouter.java` - Routing strategy

### Decision Tree
1. `planner/providerdecider/ProviderDeciderV2.java` - DT workflow
2. `planner/providerdecider/ProviderDeciderViaLCM.java` - LCM routing
3. `cache/DecisionTreeObjectCache.java` - DT caching

### Webhooks
1. `controller/WebhookController.java` - Generic webhook endpoint
2. `controller/v2/CashfreeWebhookController.java` - Cashfree webhooks
3. `service/WebhookService.java` - Webhook processing

### Provider Implementations
1. `v2/workflow/create/providers/CashfreeProviderAdapter.java`
2. `v2/workflow/create/providers/cybersource/CybersourceProviderAdapter.java`
3. `v2/workflow/create/providers/PayuProviderAdapter.java`

### Configuration
1. `entity/ProviderAccountEntity.java` - Provider credentials
2. `entity/PaymentProviderEntity.java` - Provider definition
3. `entity/ClientPaymentProviderConfigEntity.java` - Client-provider mapping

---

# PAYMENT FLOW DEEP-DIVE

## 33. THE 7-STEP WORKFLOW PIPELINE

### Base Workflow Pattern (Template Method)
**File:** `v2/workflow/create/Workflow.java`

```java
public Response execute(Request request) {
    // STEP 1: Validate inputs and enrich context
    Context context = validateAndEnrichContext(request);

    // STEP 2: Persist to relational DB (transactional)
    persistIntent(context);

    // STEP 3: Pre-persist event hooks
    publishEntityPrePersistEvents(context);

    // STEP 4: Persist to non-relational DB (DynamoDB)
    persistNonRelationalIntent(context);

    // STEP 5: Process (external provider calls)
    process(context);

    // STEP 6: Post-process and save results (transactional)
    Response response = postProcess(context);

    // STEP 7: Post-persist & publish events
    postPersistNonRelationalDataStore(context);
    publishEntityChangeEvents(context);

    throwErrorIfRequired(context);
    return response;
}
```

---

## 34. PAYMENTATTEMPTCREATEWORKFLOW DETAILED

**File:** `v2/workflow/create/paymentattempts/PaymentAttemptCreateWorkflow.java`

### Step 1: Validate & Enrich Context

| Enricher | Purpose | Output |
|----------|---------|--------|
| `InstrumentTypeProcessorManager` | Validate & enrich payment instrument | `InstrumentTypeProcessorResult` |
| `ProviderDeciderRouter.resolve()` | Route to provider via Decision Tree | `ProviderRoutingDecisionResult` |
| `AuthTypeDeciderFactory` | Determine auth type (3DS, OTP, None) | `AuthType` |
| `NativeProviderDecider` | Select native OTP provider | `ProviderAccountEntity` |
| `SettlementRouteValidator` | Validate & enrich settlement routes | `RoutesBreakup` |
| `MandateServiceDataManager` | Register mandate (if eMandate) | `Mandate` |

### Context Object Structure
```java
PaymentAttemptCreateContext {
    // Request/Response
    CreatePaymentAttemptRequest request
    PaymentAttemptResponse response

    // Entities
    PaymentAttemptV2Entity paymentAttemptEntity
    PaymentV2Entity paymentEntity
    OrderEntity orderEntity
    CustomerEntity customerEntity
    ClientEntity clientEntity

    // Enriched Data
    InstrumentTypeProcessorResult instrumentProcessorResult
    ProviderAccountEntity providerAccountEntity
    ProviderRoutingDecisionResult routingDecisionResult
    AuthType authType
    RoutesBreakup routesBreakup
    ProviderPaymentResponse createResponse

    // OTP/Auth Flow
    Boolean isPlatformNativeOtpSupported
    PaymentAttemptNativeOTPDetailEntity nativeOTPDetailEntity

    // Error Collection
    List<WorkflowInternalError> errors
}
```

### Step 2: Persist Intent
```java
@Transactional(transactionManager = "MasterTransactionManager")
public void persistIntent(PaymentAttemptCreateContext context) {
    // Create PaymentAttemptV2Entity
    PaymentAttemptV2Entity entity = PaymentAttemptV2Entity.builder()
        .externalId(PaymentAttemptUUIdGenerator.generate())
        .status(PaymentAttemptStatus.CREATED)
        .paymentEntity(paymentEntity)
        .providerAccountEntity(providerAccountEntity)
        .paymentMethod(instrumentResult.getPaymentMethod())
        .instrumentDetail(instrumentResult.getEnrichedInstrument())
        .routesBreakup(routesBreakup)
        .build();

    // Save to repository
    paymentAttemptRepository.save(entity);

    // Save fees
    feeCreateWorkflow.persistIntent(feeContexts);

    // Add attributes (DT_ID, DT_RESULT, etc.)
    enrichAttributes(entity);
}
```

### Step 5: Process (Provider Call)
```java
public void process(PaymentAttemptCreateContext context) {
    // Find adapter
    IPaymentProviderAdapter adapter = paymentProviderFactory
        .findPaymentProviderAdapter(orderType, providerKey, instrumentType, threeDSType);

    // Execute provider call
    ProviderPaymentResponse response = adapter.executePaymentAttempt(
        context,
        adapter::createPaymentAttempt,
        FlowType.CREATE
    );

    // Check platform OTP capability
    response = checkIfPlatformOtpEnabled(context, response);

    context.setCreateResponse(response);
}
```

### Step 6: Post-Process
```java
@Transactional
public PaymentAttemptResponse postProcess(PaymentAttemptCreateContext context) {
    PaymentAttemptV2Entity entity = context.getPaymentAttemptEntity();
    ProviderPaymentResponse response = context.getCreateResponse();

    // Update from provider response
    entity.setProviderStatus(response.getProviderStatus());
    entity.setProviderReferenceId(response.getProviderReferenceId());
    entity.setGatewayReferenceId(response.getGatewayReferenceId());

    // Determine final status
    if (response.getProviderRequestStatus() == REQUEST_SUCCESS) {
        entity.setStatus(response.getStatus());
    } else if (isEligiblePaymentMode) {
        entity.setStatus(response.getStatus() == FAILED ? FAILED : PROCESSING);
    }

    paymentAttemptRepository.save(entity);
    return mapper.toResponse(entity, response);
}
```

### Step 7: Publish Events
```java
public void publishEntityChangeEvents(PaymentAttemptCreateContext context) {
    // Post to sync EventBus (triggers PaymentStateMachine)
    syncBus.post(PaymentAttemptEventFactory.findEvent(paymentAttemptEntity));

    // Post to async EventBus
    asyncBus.post(PaymentAttemptEventFactory.findEvent(paymentAttemptEntity));

    // Publish to multi-tenant event system
    eventiService.publishEvent(paymentAttemptEntity);

    // Add to sync manager for webhook updates
    syncManager.addEntityForSync(paymentAttemptEntity);
}
```

---

## 35. STATE MACHINE IMPLEMENTATION

### PaymentStateMachine
**File:** `statemachine/payment/PaymentStateMachine.java`

```
Event Subscriptions:
├── @Subscribe onPaymentAttemptCreated
│   └── Payment: FAILED → CREATED
├── @Subscribe onPaymentAttemptFailed
│   └── If all attempts failed: Payment → FAILED
├── @Subscribe onPaymentAttemptCompleted
│   └── Payment → COMPLETED (with optimistic lock retry)
├── @Subscribe onPaymentAttemptAuthorized
│   └── Payment → AUTHORIZED
├── @Subscribe onPaymentAttemptProcessing
│   └── Payment → PROCESSING
├── @Subscribe onPaymentAttemptBlocked
│   └── Payment → BLOCKED
└── @Subscribe onAuthenticationSuccessful/Failed
    └── Payment → AUTHENTICATION_SUCCESSFUL/FAILED
```

### OrderStateMachine
**File:** `statemachine/order/OrderStateMachine.java`

```
Event Subscriptions:
├── @Subscribe onPaymentCreated
│   └── Order → CREATED or AUTHLESS_READY_TO_PROCESS
├── @Subscribe onPaymentFailed
│   └── Order → FAILED
├── @Subscribe onPaymentCompleted
│   └── Order → COMPLETED (if all payments done)
├── @Subscribe onPaymentAuthorized
│   └── Order → AUTHORIZED
└── @Subscribe onPaymentProcessing
    └── Order → PROCESSING
```

### Terminal States
| Entity | Terminal States |
|--------|-----------------|
| PaymentAttempt | COMPLETED, FAILED, FORCE_FAILED |
| Payment | COMPLETED, FAILED, FORCE_FAILED, DISCARDED |
| Order | COMPLETED, FAILED |

### State Transition Guard
```java
private boolean shouldUpdatePaymentStatus(PaymentV2Entity entity) {
    return !Arrays.asList(COMPLETED, FAILED, FORCE_FAILED, DISCARDED)
        .contains(entity.getStatus());
}
```

---

## 36. END-TO-END PAYMENT FLOW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  1. ORDER CREATION                                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ OrderCreateWorkflow.execute()                                       │ │
│  │ ├── validateAndEnrichContext() - Customer lookup, order validation │ │
│  │ ├── persistIntent() - Save OrderEntity (status: CREATED)           │ │
│  │ └── publishEvents() → OrderStateMachine                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. PAYMENT CREATION                                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ BulkPaymentCreateWorkflow.execute()                                 │ │
│  │ ├── validateAndEnrichContext() - Payment mode validation           │ │
│  │ ├── persistIntent() - Save PaymentV2Entity (status: CREATED)       │ │
│  │ └── publishEvents() → PaymentStateMachine                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. PAYMENT ATTEMPT CREATION (Core Flow)                                 │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ PaymentAttemptCreateWorkflow.execute()                              │ │
│  │ ├── validateAndEnrichContext()                                     │ │
│  │ │   ├── InstrumentTypeProcessorManager (Card/UPI/NetBanking)       │ │
│  │ │   ├── ProviderDeciderRouter (Decision Tree routing)              │ │
│  │ │   ├── AuthTypeDeciderFactory (3DS/OTP/None)                      │ │
│  │ │   └── SettlementRouteValidator                                   │ │
│  │ ├── persistIntent() - Save PaymentAttemptV2Entity                  │ │
│  │ ├── persistNonRelationalIntent() - DynamoDB (OTP details)          │ │
│  │ ├── process() - Provider API call via Adapter                      │ │
│  │ ├── postProcess() - Update entity with provider response           │ │
│  │ └── publishEvents() → PaymentStateMachine → OrderStateMachine      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. PROVIDER API RESPONSE                                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ ProviderPaymentResponse contains:                                   │ │
│  │ ├── providerStatus: "SUCCESS" / "PENDING" / "FAILED"               │ │
│  │ ├── providerReferenceId: Provider's transaction ID                 │ │
│  │ ├── status: PaymentAttemptStatus (mapped)                          │ │
│  │ ├── transactionResponse:                                           │ │
│  │ │   ├── authentication: { url, method } (for 3DS redirect)         │ │
│  │ │   └── sdkParams: Native OTP/SDK details                          │ │
│  │ └── providerError: Error details if failed                         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                      ▼
┌─────────────────────────┐                    ┌─────────────────────────┐
│  5A. 3DS/OTP FLOW       │                    │  5B. DIRECT SUCCESS     │
│  ┌───────────────────┐  │                    │  ┌───────────────────┐  │
│  │ Client performs   │  │                    │  │ Status: COMPLETED │  │
│  │ authentication    │  │                    │  │ Payment done!     │  │
│  │ (redirect/native) │  │                    │  └───────────────────┘  │
│  └───────────────────┘  │                    └─────────────────────────┘
│           │             │
│           ▼             │
│  ┌───────────────────┐  │
│  │ Authenticate      │  │
│  │ Workflow called   │  │
│  │ with OTP/callback │  │
│  └───────────────────┘  │
└─────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  6. WEBHOOK / SYNC UPDATE                                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Provider sends webhook OR SyncManager polls status                  │ │
│  │ ├── WebhookController receives update                              │ │
│  │ ├── adapter.syncPaymentAttemptWithWebhook()                        │ │
│  │ ├── Update PaymentAttemptV2Entity status                           │ │
│  │ └── publishEvents() → State machines cascade updates               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  7. FINAL STATE                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ PaymentAttempt: COMPLETED ──► Payment: COMPLETED ──► Order: COMPLETED│
│  │                                                                     │ │
│  │ eventiService.publishEvent() → Client webhook notification          │ │
│  │ eventiService.publishToPinot() → Analytics dashboard               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 37. 3DS / NATIVE OTP AUTHENTICATION

### Native OTP Flow (Card Payments)
```
1. PaymentAttemptCreateWorkflow detects CARD + OTP-capable BIN
2. wspService.isPlatformNativeOtpEnabled() returns true
3. Provider returns redirect URL, but we override with SDK params
4. CardNativeOTPSDKParamDetail created:
   ├── authType: NATIVE_OTP
   ├── challengeId: UUID
   ├── fallbackUrl: Provider's original auth URL
   └── submitOTPAllowed: true

5. PaymentAttemptNativeOTPDetailEntity saved to DynamoDB
6. Client submits OTP via PaymentAttemptAuthenticateWorkflow
7. Provider validates OTP, returns success/failure
8. State machines update payment/order status
```

### 3DS Redirect Flow
```
1. Provider returns authentication URL
2. Client redirects to issuer's 3DS page
3. User completes authentication
4. Callback to return_url
5. ValidateAuthenticationWorkflow processes callback
6. Provider confirms authentication status
7. State machines update accordingly
```

---

## 38. INSTRUMENT PROCESSING

### InstrumentTypeProcessorManager
**File:** `processors/instrumenttype/InstrumentTypeProcessorManager.java`

```java
// Routes to specific processor based on instrument type
IInstrumentTypeProcessor processor = processorByType.get(instrument.getType());
return processor.validatePaymentInstrumentAndEnrich(instrument);
```

### Processor Implementations
| Processor | InstrumentType | Enrichment |
|-----------|----------------|------------|
| `CardInstrumentTypeProcessor` | CARD | BIN lookup, issuer, card type |
| `UPIPayInstrumentTypeProcessor` | UPI_APPS | VPA validation, provider |
| `UPICollectInstrumentTypeProcessor` | UPI_COLLECT | QR code, timeout |
| `NetBankingInstrumentTypeProcessor` | NET_BANKING | Bank code, issuer |
| `EMandateInstrumentTypeProcessor` | NET_BANKING_WITH_PI | Mandate details |

### InstrumentTypeProcessorResult
```java
InstrumentTypeProcessorResult<R, S> {
    PaymentInstrumentGroup paymentMethod;  // CARD, UPI_PAY, etc.
    R paymentSubMethodDetail;              // CardPaymentSubMethodDetail
    S enrichedPaymentInstrument;           // CardEnrichedPaymentInstrument
}
```

---

## 39. DISTRIBUTED LOCKING

### SequentialWorkflow Pattern
**File:** `v2/workflow/create/SequentialWorkflow.java`

```java
public Response execute(Request request) {
    LockSetting lockSetting = fetchLockSetting();
    String lockKey = evaluateLockKey(request, lockSetting.getLockKey());

    // Acquire Redis distributed lock
    Optional<RLock> lock = redisLockUtil.acquireLock(lockKey, flowType);

    if (lock.isPresent() || !lockSetting.getIsLockMandatory()) {
        try {
            return super.execute(request);  // Run workflow
        } finally {
            lock.ifPresent(redisLockUtil::releaseLock);
        }
    }
    throw Error.unable_to_acquire_lock.getBuilder().build();
}
```

**Use Cases:**
- Prevents concurrent payment attempts on same order
- Ensures single webhook processing per transaction
- Avoids race conditions in status updates

---

## 40. KEY PAYMENT FLOW FILES

### Core Workflows
1. `v2/workflow/create/Workflow.java` - Base template
2. `v2/workflow/create/paymentattempts/PaymentAttemptCreateWorkflow.java` - Main flow
3. `v2/workflow/create/payments/bulk/BulkPaymentCreateWorkflow.java` - Payment creation
4. `v2/workflow/authenticate/PaymentAttemptAuthenticateWorkflow.java` - OTP auth

### State Machines
1. `statemachine/payment/PaymentStateMachine.java`
2. `statemachine/order/OrderStateMachine.java`
3. `statemachine/RefundStateMachine.java`

### Instrument Processing
1. `processors/instrumenttype/InstrumentTypeProcessorManager.java`
2. `processors/instrumenttype/CardInstrumentTypeProcessor.java`
3. `processors/instrumenttype/UPIPayInstrumentTypeProcessor.java`

### Context & Events
1. `v2/workflow/create/paymentattempts/PaymentAttemptCreateContext.java`
2. `statemachine/payment/events/PaymentAttemptEventFactory.java`
3. `statemachine/order/events/OrderEventFactory.java`

---

## 41. ARCHITECTURAL PATTERNS SUMMARY

| Pattern | Implementation | Purpose |
|---------|----------------|---------|
| **Template Method** | `Workflow.execute()` 7-step pipeline | Consistent execution flow |
| **Factory** | `PaymentProviderFactory`, `InstrumentTypeProcessorManager` | Dynamic component selection |
| **Strategy** | `AuthTypeDeciderFactory`, `SdkTypeDeciderFactory` | Pluggable algorithms |
| **Observer** | Guava EventBus, State Machines | Decoupled state transitions |
| **Context Object** | `PaymentAttemptCreateContext` | Data flow through pipeline |
| **Distributed Lock** | `SequentialWorkflow` + Redis | Concurrency control |
| **Event Sourcing** | DynamoDB workflow context | Audit trail |

---

## 42. COMPLETE STUDY GUIDE SUMMARY

You now have a **42-section expert study guide** covering:

### Foundation (Sections 1-15)
- Tech stack, project structure, core concepts
- API endpoints, authentication, dependencies

### Data Layer Deep-Dive (Sections 16-24)
- Entity hierarchy, Master-Replica DB
- Repository patterns, caching, DynamoDB

### Provider Integration Deep-Dive (Sections 25-32)
- Adapter architecture, Decision Tree routing
- Webhook handling, provider configuration
- Error handling and retry logic

### Payment Flow Deep-Dive (Sections 33-41)
- 7-step workflow pipeline
- State machine implementation
- End-to-end payment flow
- 3DS/OTP authentication
- Instrument processing
- Distributed locking
