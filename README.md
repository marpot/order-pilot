# OrderPilot

OrderPilot is a B2B order-intake application for wholesalers, manufacturers, and distributors. It turns text, CSV, XLSX, and text-based PDF input into structured orders that an operator can review, edit, approve, or reject. Extraction is conservative: missing values are not invented and uncertain orders are marked `NEEDS_REVIEW`.

## Architecture

- **Frontend:** React 19, TypeScript, Vite, React Router, SCSS
- **Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy 2
- **Database:** PostgreSQL 16 and Alembic
- **Extraction:** deterministic parsers plus an optional validated Langflow/LLM fallback
- **Operations:** Docker Compose, GitHub Actions, Kubernetes manifests, Helm chart, Prometheus/Grafana foundation, and provider-neutral Terraform scaffold

Business logic lives in focused services. PDF text extraction is separate from order interpretation, tabular files share one normalization path, and all AI results pass through Pydantic validation before persistence.

## Run locally

Requirements: Docker with Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Copying `.env.example` is optional for the default local setup. The stack exposes:

- application: <http://localhost:5173>
- API: <http://localhost:8000>
- OpenAPI documentation: <http://localhost:8000/docs>
- health: <http://localhost:8000/health>
- Prometheus metrics: <http://localhost:8000/metrics>

Alembic migrations run automatically when the backend starts. Demo orders are inserted only when the orders table is empty. Stop the stack with `docker compose down`. Add `-v` only when intentionally deleting persisted local data.

Optional services use Compose profiles:

```bash
docker compose --profile ai up -d langflow
docker compose --profile observability up -d prometheus grafana
```

Langflow is optional and disabled by default, so no model key is needed for normal operation. See [langflow/README.md](langflow/README.md) for flow setup and the minimal catalog/RAG foundation. Prometheus is exposed on port `9090` and the provisioned Grafana dashboard on port `3000`.

## Features and workflow

- professional responsive dashboard, order register, filters, details, editing, import UI, loading/error/empty states, and accessible keyboard focus
- text/email, CSV, XLSX, and text-based PDF import
- validation, upload size/page/row limits, and controlled errors for malformed or unsupported files
- deterministic extraction followed by optional Langflow enrichment only for incomplete input
- explicit workflow: `NEW` or `NEEDS_REVIEW` may become `APPROVED` or `REJECTED`; terminal states cannot transition again
- approval requires customer, address, delivery date, and at least one item
- audit trail for `IMPORTED`, `EDITED`, `APPROVED`, and `REJECTED`; no-op edits do not create misleading events
- request/import/AI Prometheus metrics and a small Grafana dashboard
- no authentication, external mailbox, ERP connection, OCR, or paid infrastructure

### CSV/XLSX format

The first row must contain headers. One item is represented by each subsequent row. Required columns are `sku`, `quantity`, `customer`, `delivery_address`, and `delivery_date`; optional columns include `product_name`, `unit`, `customer_email`, and `customer_tax_id`. Common Polish header aliases are accepted. Customer and delivery metadata may be repeated on every row or supplied once, but conflicting values cause a review warning rather than a guess.

Example:

```csv
sku,quantity,unit,customer,delivery_address,delivery_date
FILTR-X100,20,szt.,ABC Sp. z o.o.,ul. Przemysłowa 15 40-001 Katowice,2026-09-30
POMPA-P20,5,szt.,ABC Sp. z o.o.,ul. Przemysłowa 15 40-001 Katowice,2026-09-30
```

CSV is accepted as UTF-8 with comma, semicolon, or tab delimiters. XLSX reads the active sheet. PDF import extracts embedded text and then uses the same text interpretation pipeline; scanned/image-only PDFs return a controlled message explaining that OCR is not available yet. Default limits are 5 MB, 2,000 spreadsheet rows, and 50 PDF pages and are configurable through environment variables.

### API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | service health |
| GET | `/metrics` | Prometheus metrics |
| GET/POST | `/api/orders` | list or create orders |
| GET/PATCH/DELETE | `/api/orders/{id}` | read, edit, or delete an order |
| GET | `/api/orders/{id}/history` | chronological audit history |
| POST | `/api/orders/{id}/approve` | approve a complete non-terminal order |
| POST | `/api/orders/{id}/reject` | reject a non-terminal order |
| POST | `/api/import/text` | import raw text |
| POST | `/api/import/file` | upload CSV, XLSX, or PDF (`multipart/form-data`) |
| GET | `/api/dashboard/stats` | dashboard counters and recent orders |

## Development and verification

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Frontend:

```bash
cd frontend
npm ci
npm run build
```

CI runs Python compilation and tests, the TypeScript production build, Compose configuration validation, and Docker image builds. Infrastructure assets are documented in:

- [Kubernetes manifests](infrastructure/kubernetes/README.md)
- [Helm chart](infrastructure/helm/README.md)
- [Terraform scaffold](infrastructure/terraform/README.md)

Kubernetes and Helm reference a separately managed Secret; no credentials are stored in this repository. Terraform intentionally defines validated deployment inputs and outputs but no cloud resources because a provider has not been selected.

## Current limitations and roadmap

The deterministic text parser targets predictable order messages. The PDF path has no OCR, Langflow needs a user-configured flow and model provider, and the example knowledge catalog is not a production synchronization mechanism. The application also has no authentication or authorization yet.

Next steps are IMAP/email ingestion, OCR where justified, production catalog synchronization, ERP integrations, CSV/XLSX export, authentication and roles, actor attribution, and richer field-level audit metadata.
# order-pilot
