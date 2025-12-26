# Rule Engine Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RosteredAI Platform                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        ETL Pipeline (Python)                         │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌───────────┐    ┌──────────┐                     │
│  │ Extract  │ => │ Transform │ => │   Load   │                     │
│  │(FWC API) │    │  (Pandas) │    │ (MSSQL)  │                     │
│  └──────────┘    └───────────┘    └──────────┘                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Populates Staging Tables
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MS SQL Server Database                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Staging Tables (ETL Output)                     │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  • Stg_TblAwards                                            │   │
│  │  • Stg_TblClassifications                                   │   │
│  │  • Stg_TblPayRates                                          │   │
│  │  • Stg_TblExpenseAllowances                                 │   │
│  │  • Stg_TblWageAllowances                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           │ Read by Stored Procedures                │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Stored Procedures (Business Logic)              │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  • sp_CompileAwardsSummary                                  │   │
│  │  • sp_InitializeBasicRules                                  │   │
│  │  • sp_ApplyRuleToAward                                      │   │
│  │  • sp_GenerateAwardRulesJSON                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           │ Write to Rules Tables                    │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Rules Engine Tables (Output)                    │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  • TblAwardsSummary                                         │   │
│  │  • TblRules                                                 │   │
│  │  • TblAwardRules                                            │   │
│  │  • TblCustomAwards                                          │   │
│  │  • TblRuleExecutionLog                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Accessed via Dapper
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Rule Engine (.NET 10)                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  API Layer (Controllers)                     │   │
│  │  • AwardsController                                         │   │
│  │  • RulesController                                          │   │
│  │  • RuleEngineController                                     │   │
│  │  • Swagger/OpenAPI Documentation                            │   │
│  └───────────────────────┬─────────────────────────────────────┘   │
│                          │ MediatR                                  │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Application Layer (CQRS)                        │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  Commands:                    Queries:                      │   │
│  │  • CompileAwardsSummary       • GetAwards                   │   │
│  │  • ApplyRule                  • GetRules                    │   │
│  │                               • GetAwardRulesJson           │   │
│  └───────────────────────┬─────────────────────────────────────┘   │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 Domain Layer (Entities)                      │   │
│  │  • Award                      • AwardRule                   │   │
│  │  • Rule                       • CustomAward                 │   │
│  │  • RuleExecutionLog           • Enums                       │   │
│  └───────────────────────┬─────────────────────────────────────┘   │
│                          │                                          │
│                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │           Infrastructure Layer (Data Access)                 │   │
│  │  • DatabaseContext                                          │   │
│  │  • RuleEngineRepository (Dapper)                            │   │
│  │  • Connection Pooling                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ REST API (JSON)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Clients                                     │
├─────────────────────────────────────────────────────────────────────┤
│  • Next.js UI (React)                                               │
│  • External Systems (via JSON API)                                  │
│  • Mobile Apps                                                      │
│  • Third-party Integrations                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. ETL Pipeline Flow
```
FWC API → Extract → Transform → Load → Staging Tables
```

### 2. Rule Engine Compilation Flow
```
Staging Tables → sp_CompileAwardsSummary → TblAwardsSummary
                                         ↓
                                  Statistics & Aggregates
```

### 3. Rules Management Flow
```
API Request → MediatR Command → Repository → Stored Procedure → Database
                             ↓
                        Response (JSON)
```

### 4. Rule Application Flow
```
Apply Rule Request → sp_ApplyRuleToAward → TblAwardRules
                                         ↓
                                  TblRuleExecutionLog
                                         ↓
                                  Audit Trail
```

## Component Interactions

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Controllers (API Endpoints)                           │ │
│  │  • Swagger UI                                          │ │
│  │  • Request/Response DTOs                               │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ Dependency: Application
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CQRS (MediatR)                                        │ │
│  │  • Commands (Write Operations)                         │ │
│  │  • Queries (Read Operations)                           │ │
│  │  • Handlers                                            │ │
│  │  • Interfaces                                          │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ Dependency: Domain
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       Domain Layer                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Business Logic (Pure)                                 │ │
│  │  • Entities                                            │ │
│  │  • Enums                                               │ │
│  │  • Domain Events                                       │ │
│  │  • No External Dependencies                            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         ▲
                         │ Implements Interfaces
                         │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  External Concerns                                     │ │
│  │  • Database Context (Dapper)                           │ │
│  │  • Repository Implementation                           │ │
│  │  • Configuration                                       │ │
│  │  • External Services                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## CQRS Pattern Implementation

### Commands (Write Operations)

```
┌────────────────────────────────────────────────┐
│          CompileAwardsSummaryCommand           │
├────────────────────────────────────────────────┤
│  Request                                       │
│  • AwardCode (optional)                        │
│                                                │
│  Handler                                       │
│  • Calls sp_CompileAwardsSummary               │
│  • Returns CompileAwardsSummaryResult          │
│                                                │
│  Response                                      │
│  • Status                                      │
│  • RecordsCompiled                             │
│  • ErrorMessage                                │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│              ApplyRuleCommand                  │
├────────────────────────────────────────────────┤
│  Request                                       │
│  • RuleCode                                    │
│  • AwardCode                                   │
│                                                │
│  Handler                                       │
│  • Calls sp_ApplyRuleToAward                   │
│  • Returns ApplyRuleResult                     │
│                                                │
│  Response                                      │
│  • Status                                      │
│  • ExecutionId                                 │
│  • ErrorMessage                                │
└────────────────────────────────────────────────┘
```

### Queries (Read Operations)

```
┌────────────────────────────────────────────────┐
│              GetAwardsQuery                    │
├────────────────────────────────────────────────┤
│  Request                                       │
│  • AwardCode (optional)                        │
│  • IndustryType (optional)                     │
│  • IsActive (optional)                         │
│                                                │
│  Handler                                       │
│  • Queries TblAwardsSummary                    │
│  • Returns IEnumerable<Award>                  │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│              GetRulesQuery                     │
├────────────────────────────────────────────────┤
│  Request                                       │
│  • RuleType (optional)                         │
│  • RuleCategory (optional)                     │
│  • IsActive (optional)                         │
│                                                │
│  Handler                                       │
│  • Queries TblRules                            │
│  • Returns IEnumerable<Rule>                   │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│          GetAwardRulesJsonQuery                │
├────────────────────────────────────────────────┤
│  Request                                       │
│  • AwardCode (optional)                        │
│  • RuleType (optional)                         │
│                                                │
│  Handler                                       │
│  • Calls sp_GenerateAwardRulesJSON             │
│  • Returns JSON string                         │
└────────────────────────────────────────────────┘
```

## Technology Stack

### Backend (.NET)
- **Framework**: .NET 10.0
- **Pattern**: CQRS (MediatR)
- **Database**: MS SQL Server
- **ORM**: Dapper (micro-ORM)
- **API**: ASP.NET Core Web API
- **Documentation**: Swagger/OpenAPI
- **Testing**: xUnit, Moq, FluentAssertions

### Database
- **Engine**: MS SQL Server
- **Approach**: Database-first with stored procedures
- **Performance**: Indexed queries, connection pooling
- **Features**: JSON support, aggregation functions

### ETL Pipeline (Existing)
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Libraries**: httpx, pandas, tenacity
- **Database**: pymssql, pyodbc

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Environment                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Nginx      │→│  Next.js UI  │  │  Rule Engine    │  │
│  │ (Port 8081)  │  │  (Port 3000) │  │  API (Port 5000)│  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│         │                                      │            │
│         │                                      │            │
│         ▼                                      ▼            │
│  ┌──────────────┐                    ┌─────────────────┐  │
│  │  FastAPI     │                    │   MS SQL Server │  │
│  │  Backend     │──────────────────→│   Database      │  │
│  │  (Port 8000) │                    │   (Port 1433)   │  │
│  └──────────────┘                    └─────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Security Layers

```
┌────────────────────────────────────────────────────────────┐
│                      Security Measures                      │
├────────────────────────────────────────────────────────────┤
│  1. Input Validation                                       │
│     • MediatR pipeline behaviors                           │
│     • Data type validation                                 │
│     • Required field validation                            │
│                                                             │
│  2. Database Security                                      │
│     • Parameterized queries (SQL injection protection)     │
│     • Stored procedures (pre-compiled)                     │
│     • Principle of least privilege                         │
│                                                             │
│  3. Connection Security                                    │
│     • TLS/SSL encryption                                   │
│     • Connection string in config (not code)               │
│     • Connection pooling                                   │
│                                                             │
│  4. Audit & Logging                                        │
│     • TblRuleExecutionLog (complete audit trail)           │
│     • Execution timing                                     │
│     • Error logging                                        │
│                                                             │
│  5. API Security (Future)                                  │
│     • Authentication (JWT)                                 │
│     • Authorization (Role-based)                           │
│     • Rate limiting                                        │
└────────────────────────────────────────────────────────────┘
```
