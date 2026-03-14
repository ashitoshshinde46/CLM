<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# GCC Lightweight CLM - Module-wise Technical Documentation

This document provides detailed technical specifications for each of the 12 core modules. Each module includes database schema, API endpoints, frontend components, business logic, and GitHub Copilot implementation prompts. The system uses Python FastAPI backend, React frontend, PostgreSQL database, and Redis for caching.

Tech Stack: FastAPI, SQLAlchemy, React 18, Tailwind CSS, PostgreSQL 16, Redis, JWT auth.[^1][^2][^3]

## Authentication Module

Handles user login, roles (Admin, Legal, Finance, Vendor), JWT tokens, and session management.

**Database Schema:**

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'legal', 'finance', 'vendor') NOT NULL,
    department VARCHAR(100),
    gcc_location VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    jwt_token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**

```
POST /api/auth/login - {email, password} → {access_token, refresh_token}
POST /api/auth/refresh - {refresh_token} → {access_token}
GET /api/auth/profile - Returns user profile (JWT protected)
POST /api/auth/logout - Invalidate session
```

**React Components:** `LoginForm.jsx`, `ProtectedRoute.jsx`, `RoleGuard.jsx`

**GitHub Copilot Prompt:**

```
Create FastAPI authentication module with JWT, role-based access control for CLM system. Include login, refresh token, logout endpoints. Use SQLAlchemy for PostgreSQL users table with roles (admin,legal,finance,vendor). Add middleware for protected routes. React login form with Tailwind CSS.
```


## Contract Repository Module

Central storage for all contracts with metadata indexing and full-text search.

**Database Schema:**

```sql
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    contract_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    status ENUM('draft','sent','negotiating','signed','active','expired','terminated') DEFAULT 'draft',
    contract_type ENUM('vendor','employee','service','lease','nda') NOT NULL,
    vendor_name VARCHAR(255),
    amount DECIMAL(15,2),
    start_date DATE,
    end_date DATE,
    created_by INT REFERENCES users(id),
    assigned_to INT REFERENCES users(id),
    metadata JSONB,
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_vendor ON contracts(vendor_name);
CREATE FULLTEXT INDEX idx_contracts_fts ON contracts USING GIN(to_tsvector('english', title || ' ' || vendor_name));
```

**API Endpoints:**

```
GET /api/contracts - Query params: status, vendor, type, page, limit → Paginated contracts
POST /api/contracts - Create new contract {title, type, vendor_name, amount, dates, file}
GET /api/contracts/{id} - Get single contract details
PUT /api/contracts/{id} - Update contract metadata
DELETE /api/contracts/{id} - Soft delete
POST /api/contracts/search - Full-text search {query}
```

**Key Features:** Drag-drop file upload, metadata auto-extraction, contract numbering auto-generation.[^1]

**React Components:** `ContractList.jsx`, `ContractCard.jsx`, `ContractSearch.jsx`, `FileUpload.jsx`

**GitHub Copilot Prompt:**

```
Build FastAPI contract repository module. PostgreSQL schema with full-text search, JSONB metadata, status workflow. Include CRUD APIs with pagination, search endpoint using GIN index. React components: searchable contract list with filters, drag-drop upload, contract detail view with Tailwind.
```


## Workflow \& Approval Module

Multi-stage approval workflows with notifications and audit trail.

**Database Schema:**

```
CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    contract_id INT REFERENCES contracts(id),
    workflow_type VARCHAR(100),
    current_stage VARCHAR(50),
    approvers JSONB,  -- [{"user_id":1, "stage":"legal_review", "status":"pending"}]
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE workflow_events (
    id SERIAL PRIMARY KEY,
    workflow_id INT REFERENCES workflows(id),
    user_id INT REFERENCES users(id),
    action VARCHAR(50),  -- approve, reject, comment
    comments TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**

```
POST /api/workflows/{contract_id}/start - Initialize workflow
GET /api/workflows/{contract_id} - Get workflow status
POST /api/workflows/{workflow_id}/approve - User approves stage
POST /api/workflows/{workflow_id}/reject - User rejects with comments
GET /api/my-tasks - Pending approvals for current user
```

**React Components:** `ApprovalQueue.jsx`, `WorkflowStepper.jsx`, `ApprovalModal.jsx`

**Business Logic:** Sequential/parallel approvals, auto-escalation after 48hrs, email/SMS notifications.

**GitHub Copilot Prompt:**

```
FastAPI workflow engine for contract approvals. Schema for workflows, events, approvers. APIs for starting workflow, approving/rejecting, my pending tasks. Include business rules: auto-escalation, notifications. React stepper component showing workflow stages, approval modals.
```


## Document Management Module

Version control, redlining, clause library, and document generation.

**Database Schema:**

```
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    contract_id INT REFERENCES contracts(id),
    version_number INT NOT NULL,
    file_path VARCHAR(500),
    changes_summary TEXT,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE clause_library (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    content TEXT NOT NULL,
    tags JSONB,
    usage_count INT DEFAULT 0
);
```

**API Endpoints:**

```
POST /api/documents/{contract_id}/version - Upload new version
GET /api/documents/{contract_id}/versions - Version history
POST /api/clauses/generate - Generate contract from template + clauses
GET /api/clauses?category=... - Clause library search
POST /api/clauses/{id}/use - Track clause usage in contract
```

**Key Features:** Compare versions, clause drag-drop insertion, template builder.[^4][^1]

**React Components:** `DocumentEditor.jsx`, `VersionCompare.jsx`, `ClauseLibrary.jsx`

**GitHub Copilot Prompt:**

```
Document management module: version control, clause library. Schema for versions, clauses. APIs for version upload/compare, clause search/usage. React rich text editor with clause insertion, side-by-side version compare using diff library.
```


## Obligation Management Module

Tracks post-signature obligations, milestones, and renewal alerts.

**Database Schema:**

```
CREATE TABLE obligations (
    id SERIAL PRIMARY KEY,
    contract_id INT REFERENCES contracts(id),
    description TEXT NOT NULL,
    due_date DATE,
    responsible_user INT REFERENCES users(id),
    status ENUM('pending','completed','overdue') DEFAULT 'pending',
    recurrence VARCHAR(50),  -- monthly, quarterly
    created_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**

```
GET /api/obligations?status=pending&due_before=2026-04-01 - Dashboard view
POST /api/obligations - Create obligation from contract
PUT /api/obligations/{id}/complete - Mark complete
GET /api/obligations/contract/{contract_id} - Contract-specific obligations
```

**React Components:** `ObligationDashboard.jsx`, `CalendarView.jsx`, `MilestoneTracker.jsx`

**Business Logic:** Auto-create obligations from contract clauses, renewal alerts 90/60/30 days prior.[^5]

**GitHub Copilot Prompt:**

```
Obligation tracking module. Extract obligations from contracts automatically. Schema with recurrence, status. APIs for dashboard (overdue/pending), completion. React calendar view, obligation list with due date filters, auto-reminders.
```


## Risk \& Compliance Module

AI-powered risk scoring, clause analysis, regulatory compliance checks.

**Database Schema:**

```
CREATE TABLE risk_assessments (
    id SERIAL PRIMARY KEY,
    contract_id INT REFERENCES contracts(id),
    risk_score DECIMAL(3,2),  -- 0.00 to 1.00
    high_risk_clauses JSONB,
    compliance_status VARCHAR(50),
    assessed_by INT REFERENCES users(id),
    assessed_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**

```
POST /api/risk/assess/{contract_id} - Run AI risk analysis
GET /api/risk/dashboard - Risk summary by vendor/type
GET /api/risk/{contract_id} - Detailed risk report
```

**React Components:** `RiskDashboard.jsx`, `ComplianceReport.jsx`, `RiskHeatmap.jsx`

**Integration:** Basic NLP for clause risk scoring using spaCy/textblob (lightweight).[^6]

**GitHub Copilot Prompt:**

```
Risk assessment module with simple NLP. Schema for risk scores, high-risk clauses. API to analyze contract text for risks (liability, indemnity, termination). React risk heatmap dashboard by vendor, contract type.
```


## Reporting \& Analytics Module

Custom reports, dashboards, contract portfolio analytics.

**Database Schema:** Uses existing tables + reporting views.

**Key Reports:**

- Contract aging by status/vendor
- Spend analysis by vendor/category
- Compliance/risk overview
- Renewal pipeline

**API Endpoints:**

```
GET /api/reports/contracts-aging - CSV/PDF export
GET /api/analytics/spend?vendor=...&year=2026
POST /api/reports/custom - Dynamic report builder
```

**React Components:** `ReportBuilder.jsx`, `Dashboard.jsx`, `ChartGallery.jsx`

**GitHub Copilot Prompt:**

```
Analytics module with SQL views for contract aging, spend analysis. APIs returning JSON for charts. React dashboard with Recharts: pie charts (status), bar charts (vendor spend), line charts (renewals pipeline). Export CSV/PDF.
```


## Integration Module

Connects with ERP, HRIS, procurement systems via APIs/webhooks.

**Database Schema:**

```
CREATE TABLE integrations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),  -- Oracle, SAP, Workday
    config JSONB,
    status VARCHAR(50),
    last_sync TIMESTAMP
);
```

**API Endpoints:**

```
POST /api/integrations/webhook - Incoming webhooks
GET /api/integrations/sync/{integration_id} - Manual sync
```

**Supported:** REST APIs, CSV import/export, SFTP.[^7]

**GitHub Copilot Prompt:**

```
Integration framework: webhook receiver, scheduled syncs. Configurable API connectors for ERP/HR systems. Schema for integration configs. Handle contract data import/export CSV, REST APIs.
```


## Mobile \& Notifications Module

Push notifications, mobile-responsive UI, SMS/email alerts.

**API Endpoints:**

```
POST /api/notifications/send - Internal notification
POST /api/notifications/push - Mobile push via FCM
GET /api/notifications/user/{user_id} - User notification center
```

**React Components:** `NotificationBell.jsx`, `MobileAppLayout.jsx`

**GitHub Copilot Prompt:**

```
Notification system with FCM push, email/SMS. React notification center dropdown. Mobile-responsive Tailwind components. Real-time updates using WebSockets.
```


## Admin \& Configuration Module

User management, role permissions, system settings, audit logs.

**Database Schema:**

```
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id INT,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

**GitHub Copilot Prompt:**

```
Admin panel: user CRUD, role permissions, audit logs, system settings. React admin dashboard with tables, permissions matrix.
```


## AI Assistant Module

Chatbot for contract queries, clause suggestions, risk Q\&A.

**Integration:** OpenAI API or local Llama model for lightweight deployment.

**API Endpoints:**

```
POST /api/ai/ask - {question, contract_id} → AI response
POST /api/ai/summarize/{contract_id} - Contract summary
```

**React Components:** `AIChat.jsx`, `SmartSearch.jsx`

**GitHub Copilot Prompt:**

```
AI assistant using OpenAI API. Contract Q&A, summarization, clause suggestions. React chat interface integrated in contract view.
```


## Deployment \& DevOps Module

Docker containers, CI/CD pipeline, monitoring.

**Docker Compose Structure:**

```
services:
  - postgres:16
  - redis:7
  - fastapi-backend
  - react-frontend
  - nginx
```

**GitHub Copilot Prompt:**

```
Docker-compose for FastAPI+React+Postgres+Redis. GitHub Actions CI/CD pipeline. Health checks, auto-scaling config.
```

This documentation provides complete technical blueprints for GitHub Copilot implementation. Each module can be developed independently with clear schemas, APIs, and frontend specs. Start with Authentication → Contract Repository → Workflow modules for MVP.[^2][^3][^8]

<div align="center">⁂</div>

[^1]: https://www.mdclarity.com/blog/healthcare-contract-lifecycle-management

[^2]: https://www.focussoftnet.com/in/contract-management-erp-software

[^3]: https://www.tristatetechnology.com/blog/react-with-python

[^4]: https://www.volody.com/resource/what-is-contract-lifecycle-management-clm

[^5]: https://www.contractlogix.com/contract-management/contract-lifecycle-management-software-for-healthcare/

[^6]: https://www.summize.com/clm-hub/best-clm-software

[^7]: https://www.contractlogix.com/contract-management/contract-management-system-in-healthcare/

[^8]: https://www.geeksforgeeks.org/dbms/how-to-design-a-database-for-healthcare-management-system/

