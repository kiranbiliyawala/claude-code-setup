# Deep Study Guide: finhq-verse Repository

**For:** Experienced Java Developer (10+ years) | **New to:** finhq domain

---

## What's Different Here (Skip-the-Basics Summary)

As an experienced Java dev, focus on these **finhq-specific patterns** that differ from typical Spring apps:

| Pattern | Standard Spring | finhq-verse |
|---------|-----------------|-------------|
| **Tenant Context** | Spring Security | Custom `Passport` via thread-local |
| **Repository** | Spring Data JPA | Custom `Repository<T>` interface |
| **Pagination** | `Pageable` (offset) | `CursorPageRequest` (cursor-based) |
| **DataSource** | Single | Dual (LIVE/SANDBOX routing) |
| **External ID** | UUID | ULID (time-sortable) |
| **API Layer** | Hand-written | OpenAPI-generated controllers |

---

## Quick Start: 5 Files to Read First

1. **`README_LLM.md`** - Complete conventions guide
2. **`Passport.java`** - Multi-tenancy context carrier
3. **`Repository.java`** - Custom data access interface
4. **`AbstractService.java`** - Service layer template
5. **`OrganizationService.java`** - Concrete example tying it all together

---

## Study Path (Experienced Dev Track)

| Phase | Focus | Priority |
|-------|-------|----------|
| 1 | Custom Framework Patterns | **Must Know** |
| 2 | Domain Model & Entities | **Must Know** |
| 3 | Service Implementation Pattern | **Must Know** |
| 4 | OpenAPI Code Generation | Important |
| 5 | Infrastructure & DevOps | Reference |

---

## Phase 1: Custom Framework Patterns (Must Know)

### 1.1 The Passport Pattern (Multi-Tenancy)

**File:** `finhq-commons-java/finhq-context/src/main/java/io/finhq/commons/context/Passport.java`

Every HTTP request carries tenant context via headers → `Passport` object → Thread-local:

```
HTTP Headers                    Passport Fields
─────────────────              ────────────────
X-Finhq-Mode           →       mode (LIVE/SANDBOX)
X-Finhq-Org-Id         →       orgId
X-Finhq-Namespace-Id   →       namespaceId
X-Finhq-Request-Id     →       requestId
```

**How it flows:**
```
Request → PassportContextFilter → Passport.builder()... → PassportContext.set()
                                                              ↓
                                                    Thread-local (InheritableThreadLocal)
                                                              ↓
Service → RepositoryScope.create() → Reads from PassportContext
```

**Key Methods:**
- `getModeOrFail()` / `getModeOrDefault()` - Get mode with fail-fast or default
- `getOrgIdOrFail()` - Required for scoped queries

### 1.2 Custom Repository Pattern

**File:** `finhq-commons-spring/finhq-entity/src/main/java/io/finhq/commons/spring/entity/repository/Repository.java`

**NOT** Spring Data JPA's `JpaRepository` directly. Custom interface that:

1. **Enforces tenant scoping** via `RepositoryScope` on every method
2. **Uses cursor pagination** instead of offset
3. **Provides audit revision queries** via Hibernate Envers

```java
// Every query is scoped
Optional<T> findOne(RepositoryScope scope, Specification<T> spec);
T findByExternalIdOrFail(RepositoryScope scope, String id);  // Throws ApplicationException

// Cursor-based pagination
CursorPage<T> findAll(RepositoryScope scope, Specification<T> spec, CursorPageRequest req);

// Audit history
T findRevision(RepositoryScope scope, String externalId, int revisionId);
```

### 1.3 Cursor-Based Pagination

**Why not offset?** Offset pagination breaks when data is inserted/deleted between pages.

```java
// First page
CursorPageRequest.first(20);

// Next page (cursor = last item's externalId)
new CursorPageRequest(cursor, 20, CursorDirection.NEXT);

// Response
CursorPage<T> {
    content: List<T>,
    nextCursor: String,      // For "Load More"
    previousCursor: String   // For "Back"
}
```

### 1.4 Dual DataSource Routing

**File:** `finhq-commons-spring/finhq-entity/src/main/java/io/finhq/commons/spring/entity/datasource/`

Routes to different databases based on `Passport.mode`:
- `LIVE` → Production database
- `SANDBOX` → Sandbox database

```yaml
spring:
  datasource:           # Primary (LIVE)
    url: jdbc:mysql://...
  sandbox-datasource:   # Sandbox
    url: jdbc:mysql://...sandbox
```

---

## Phase 2: Domain Model & Entities (Must Know)

### 2.1 Entity Hierarchy

**File:** `finhq-commons-spring/finhq-entity/src/main/java/io/finhq/commons/spring/entity/entity/AbstractEntity.java`

```java
AbstractEntity                    // Base for all entities
├── id: Long                      // DB primary key (auto-gen)
├── externalId: String            // ULID for API (auto-gen via @PrePersist)
├── version: Integer              // Optimistic locking (@Version)
├── createdAt/updatedAt           // Audit timestamps
├── createdBy/updatedBy           // Audit user (default: "SYSTEM")
│
├── AbstractOrgScopedEntity       // + orgId (org-level tenant)
│
└── AbstractNamespaceScopedEntity // + namespaceId (namespace-level tenant)
```

**Key Annotations:**
- `@Audited` (Hibernate Envers) - All changes tracked in `*_aud` tables
- `@PrePersist` - Auto-generates `externalId` if not set
- `@PreUpdate` - Auto-updates `updatedAt`

### 2.2 Error Handling Pattern

**File:** `finhq-commons-java/finhq-errors/src/main/java/io/finhq/commons/errors/ApplicationException.java`

```java
// Throwing errors
throw new ApplicationException(GenericErrorCode.NOT_FOUND)
    .withDetail("entityType", "Organization")
    .withDetail("id", id);

// Service-specific error codes (each service defines its own enum)
public enum BookkeepingErrorCode implements ErrorDescriptor {
    ACCOUNT_NOT_FOUND(HttpStatusCode.NOT_FOUND, "Account not found", Level.INFO),
    INSUFFICIENT_BALANCE(HttpStatusCode.BAD_REQUEST, "Insufficient balance", Level.INFO);
    // ...
}
```

**GlobalExceptionHandler** converts to standard API response:
```json
{
  "code": "NOT_FOUND",
  "message": "Account not found",
  "details": { "id": "01H..." }
}
```

### 2.3 Domain Entities Overview

| Service | Key Entities | Scoping |
|---------|-------------|---------|
| **Foundation** | Organization, Namespace, Partner, Module | System/Org-level |
| **Bookkeeping** | Account, Transaction, TransactionLeg, Spec | Org+Namespace |
| **Calendar** | Calendar, CalendarEvent, CalendarEventType | Org+Namespace |
| **Configuration** | ConfigurationType, Configuration, Profile | Org+Namespace |
| **Consumer** | Consumer, ConsumerEventHandler | Org+Namespace |
| **Settlement** | Settlement, SettlementConfig | Org+Namespace |

---

## Phase 3: Service Implementation Pattern (Must Know)

### 3.1 The Service Template

**File:** `finhq-commons-spring/finhq-entity/src/main/java/io/finhq/commons/spring/entity/AbstractService.java`

```java
public class AbstractService<
    E extends AbstractEntity,    // Entity type
    R extends Repository<E>,     // Repository type
    M,                           // API Model (response)
    C,                           // Create Request
    U,                           // Update Request
    L                            // List Response
> {
    protected M createEntity(C request);           // Validates, maps, saves
    protected M getEntity(String id);              // By externalId
    protected L listEntities(...);                 // Cursor pagination
    protected M updateEntity(String id, U request);// Validates, maps, updates
}
```

### 3.2 Complete Service Implementation (Study This)

**File:** `finhq-foundation/src/main/java/io/finhq/foundation/organization/OrganizationService.java`

```java
@Service
@Validated
public class OrganizationService
        extends AbstractService<
                OrganizationEntity,          // E
                OrganizationRepository,      // R
                Organization,                // M (API model from OpenAPI)
                CreateOrganizationRequest,   // C
                UpdateOrganizationRequest,   // U
                OrganizationListResponse>    // L
        implements OrganizationApiDelegate { // Generated from OpenAPI

    public OrganizationService(
            OrganizationRepository repository,
            OrganizationMapper mapper,
            OrganizationValidator validator) {
        super(repository, mapper, validator);
    }

    @Override
    public Organization createOrganization(CreateOrganizationRequest request) {
        return createEntity(request);  // That's it!
    }

    @Override
    public OrganizationListResponse listOrganizations(
            Optional<String> pageAfter,
            Optional<String> pageBefore,
            Optional<Integer> pageSize) {
        return listEntities(pageAfter, pageBefore, pageSize, null,
                OrganizationListResponse::new);
    }
}
```

### 3.3 The 4 Components Per Entity

For each domain entity, you need:

| Component | Purpose | Example File |
|-----------|---------|--------------|
| `*Entity.java` | JPA entity extending AbstractEntity | `OrganizationEntity.java` |
| `*Repository.java` | Interface extending Repository<T> | `OrganizationRepository.java` |
| `*Mapper.java` | Converts Request ↔ Entity ↔ Model | `OrganizationMapper.java` |
| `*Validator.java` | Validates create/update requests | `OrganizationValidator.java` |

### 3.4 EntityUpdates Pattern (Partial Updates)

For PATCH-style updates where `null` could mean "set to null" or "don't change":

```java
public class EntityUpdates<E> {
    E entity;                           // Entity with new values
    Set<String> presentNullableProperties;  // Fields explicitly set to null
}

// In Mapper
@Override
public EntityUpdates<E> mapUpdateRequestToEntityUpdates(E entity, U request) {
    Set<String> nullableProps = new HashSet<>();

    if (request.getName() != null) {
        entity.setName(request.getName());
    }
    if (request.isDescriptionPresent()) {  // OpenAPI nullable field
        entity.setDescription(request.getDescription());
        if (request.getDescription() == null) {
            nullableProps.add("description");
        }
    }
    return new EntityUpdates<>(entity, nullableProps);
}
```

---

## Phase 4: OpenAPI Code Generation Flow (Important)

### 4.1 How It Works

```
finhq-openapi/specs/*.yaml          # You write OpenAPI specs here
         ↓
    openapi-generator
         ↓
finhq-openapi-java/                 # Generated: Models + ApiDelegate interfaces
         ↓
finhq-*/src/main/java/              # You implement ApiDelegate in your service
```

### 4.2 OpenAPI Specs Location

**Directory:** `finhq-openapi/specs/`

| File | Service |
|------|---------|
| `foundation.yaml` | Organization, Namespace, Partner APIs |
| `bookkeeping.yaml` | Account, Transaction APIs |
| `calendar.yaml` | Calendar, Event APIs |
| `configuration.yaml` | Config management APIs |
| `consumer.yaml` | Event consumer APIs |
| `settlement.yaml` | Settlement APIs |
| `shared.yaml` | Common schemas (Error, ListResponseMeta) |

### 4.3 Generated Code

After running `npx nx build finhq-openapi-java`:

```java
// Generated interface (you implement this)
public interface OrganizationApiDelegate {
    Organization createOrganization(CreateOrganizationRequest request);
    Organization getOrganization(String id);
    OrganizationListResponse listOrganizations(...);
}

// Generated models
public class Organization { ... }
public class CreateOrganizationRequest { ... }
```

### 4.4 Adding a New API

1. Edit `finhq-openapi/specs/<service>.yaml`
2. Run `npx nx build finhq-openapi-java`
3. Implement the generated `*ApiDelegate` interface in your service

---

## Phase 5: Infrastructure & DevOps (Reference)

### 5.1 Service Ports

| Service | Port |
|---------|------|
| Foundation | 7080 |
| Bookkeeping | 7081 |
| Consumer | 7082 |
| Configuration | 7084 |
| Calendar | 7085 |
| Settlement | 7086 |
| OpenAPI Docs | 7090 |
| MySQL | 3306 |
| Redis | 6379 |
| Temporal | 8080 |
| Jaeger | 16686 |

### 5.2 Development Commands

```bash
# Docker
make up         # Start all infra
make refresh    # Build affected
make restart    # Full rebuild

# Nx
npx nx build finhq-foundation     # Build one
npx nx test finhq-foundation      # Test one
npx nx affected --target=build    # Build changed
npx nx graph                       # View dependency graph
```

### 5.3 Testing

- **Framework:** JUnit 5 with TestContainers (MySQL)
- **Style:** Given-When-Then with `assertAll()`
- **MockMvc:** Use `FinhqMockMvc` (includes passport headers)

---

## Quick Reference: Key Files

| What | Path |
|------|------|
| **Conventions** | `README_LLM.md` |
| **Passport** | `finhq-commons-java/finhq-context/src/main/java/io/finhq/commons/context/Passport.java` |
| **Repository** | `finhq-commons-spring/finhq-entity/src/main/java/io/finhq/commons/spring/entity/repository/Repository.java` |
| **AbstractEntity** | `finhq-commons-spring/finhq-entity/src/main/java/io/finhq/commons/spring/entity/entity/AbstractEntity.java` |
| **AbstractService** | `finhq-commons-spring/finhq-entity/src/main/java/io/finhq/commons/spring/entity/AbstractService.java` |
| **Exception Handler** | `finhq-commons-spring/finhq-spring/src/main/java/io/finhq/commons/spring/exceptions/GlobalExceptionHandler.java` |
| **Example Service** | `finhq-foundation/src/main/java/io/finhq/foundation/organization/OrganizationService.java` |
| **OpenAPI Specs** | `finhq-openapi/specs/` |

---

## Architecture Principles Summary

1. **Multi-tenancy** - All data scoped by `orgId` + `namespaceId` via `Passport`
2. **API-First** - OpenAPI specs → Generated code → Implement delegates
3. **Audit Trail** - Hibernate Envers on all entities (`*_aud` tables)
4. **Cursor Pagination** - Stable pagination via `externalId` cursors
5. **Error Standardization** - `ApplicationException` + `ErrorDescriptor` enums
6. **Dual DataSource** - LIVE/SANDBOX routing based on mode
7. **ULID** - Time-sortable external IDs (better than UUID for DB indexes)

---

## Hands-On Learning Path

**Day 1:** Read `README_LLM.md` + understand `Passport` flow

**Day 2:** Study `AbstractEntity` → `Repository` → `AbstractService` chain

**Day 3:** Deep-dive into `OrganizationService` as complete example

**Day 4:** Explore `finhq-bookkeeping` (most complex service)

**Day 5:** Try adding a simple field to an existing entity end-to-end
