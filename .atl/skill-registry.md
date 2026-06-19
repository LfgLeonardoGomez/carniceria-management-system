# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| Writing, reviewing, or refactoring React/Next.js code; performance optimization; bundle optimization; data fetching | vercel-react-best-practices | C:\Users\pocho\.agents\skills\vercel-react-best-practices\SKILL.md |
| Building web components, pages, artifacts, posters, applications; styling/beautifying any web UI | frontend-design | C:\Users\pocho\.agents\skills\frontend-design\SKILL.md |
| Interacting with and testing local web applications using Playwright; verifying frontend functionality; debugging UI behavior | webapp-testing | C:\Users\pocho\.agents\skills\webapp-testing\SKILL.md |
| Working on `.e2e-spec.ts` files or anything under `test/e2e/`; setting up, writing, reviewing, running, debugging, or optimizing E2E or integration tests | typescript-e2e-testing | C:\Users\pocho\.agents\skills\typescript-e2e-testing\SKILL.md |
| Writing, reviewing, or optimizing Postgres queries, schema designs, or database configurations | supabase-postgres-best-practices | C:\Users\pocho\.agents\skills\supabase-postgres-best-practices\SKILL.md |
| Setting up CI/CD pipelines, containerizing applications, managing infrastructure as code, deploying to Kubernetes, configuring cloud platforms, automating releases, or responding to production incidents | devops-engineer | C:\Users\pocho\.agents\skills\devops-engineer\SKILL.md |
| Building SaaS applications with multiple tenants; tenant isolation, row-level security, data leakage prevention, shared-schema vs schema-per-tenant | saas-multi-tenant | C:\Users\pocho\.agents\skills\saas-multi-tenant\SKILL.md |
| Building retail systems, POS, inventory management, e-commerce, customer analytics, or omnichannel retail strategies | retail-expert | C:\Users\pocho\.agents\skills\retail-expert\SKILL.md |
| Working with FastAPI APIs and Pydantic models; writing new FastAPI code or refactoring/updating old code | fastapi | C:\Users\pocho\.agents\skills\fastapi\SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### vercel-react-best-practices
- Use `Promise.all()` for independent async operations; avoid sequential waterfalls
- Import directly from source files; avoid barrel files to reduce bundle size
- Use `next/dynamic` for heavy components; defer third-party scripts after hydration
- Use `React.cache()` for per-request deduplication; minimize data passed to client components
- Wrap streaming content in `Suspense` boundaries
- Use `startTransition` for non-urgent updates; derive state during render, not in effects
- Use ternary (`?:`) not `&&` for conditional rendering
- Animate wrapper `<div>` elements, not SVG elements directly
- Use `content-visibility` for long lists; hoist static JSX outside components

### frontend-design
- Choose a BOLD aesthetic direction before writing any code
- Avoid generic fonts (Inter, Roboto, Arial) — use distinctive, characterful typography
- Use CSS variables for cohesive color themes; dominant colors with sharp accents
- Prioritize CSS-only animations; use Motion library for React when needed
- Create atmosphere with gradient meshes, noise textures, grain overlays, layered transparencies
- Never use generic "AI slop" aesthetics (purple gradients, predictable layouts, cookie-cutter components)
- Match implementation complexity to aesthetic vision — maximalist needs elaborate code, minimalist needs restraint

### webapp-testing
- Use native Python Playwright scripts for all webapp testing
- Run `python scripts/with_server.py --help` first; treat bundled scripts as black boxes
- Always wait for `page.wait_for_load_state('networkidle')` before inspecting dynamic apps
- Follow reconnaissance-then-action: screenshot/inspect DOM → identify selectors → execute actions
- Always launch chromium in headless mode (`headless=True`)
- Always close the browser when done; use descriptive selectors (`text=`, `role=`, CSS, IDs)

### typescript-e2e-testing
- ALL E2E tests MUST follow Given-When-Then pattern with explicit G/W/T comments
- Use real infrastructure via Docker — never mock databases or message brokers
- Run tests sequentially (`maxWorkers: 1`); redirect ALL output to temp files, never console
- Fix ONE failing test at a time; create `/tmp/e2e-${E2E_SESSION}-failures.md` tracking file
- Clean database state in `beforeEach`; use unique identifiers per test
- Assert exact values with `toMatchObject`, not just `toBeDefined`
- Use pre-subscription + buffer clearing for Kafka tests; never `fromBeginning: true`

### supabase-postgres-best-practices
- Add indexes on frequently queried columns; use partial indexes for filtered queries
- Prefer connection pooling (PgBouncer) for high-concurrency or multi-tenant apps
- Enable Row-Level Security (RLS) for tenant isolation when applicable
- Use `EXPLAIN ANALYZE` to verify query plans before optimizing
- Avoid N+1 queries — prefer JOINs or bulk fetches
- Use appropriate data types (UUID over bigserial for public-facing IDs)
- Monitor slow query logs and set `log_min_duration_statement` appropriately

### devops-engineer
- Use infrastructure as code (Terraform/Pulumi) — never manual changes
- Store secrets in secret managers; never commit secrets to code or CI variables
- Implement health checks and readiness probes in all container definitions
- Use GitOps for Kubernetes deployments (ArgoCD or Flux)
- Enable container image scanning in CI/CD pipelines
- Document rollback procedures before deploying to production
- Never use `latest` tag in production; always pin specific versions

### saas-multi-tenant
- Default to shared-schema with `tenant_id` column on every tenant-scoped table
- Make `tenant_id` NOT NULL and include it as the first column in every composite index
- Enable PostgreSQL RLS as a database-level safety net for tenant isolation
- Set tenant context per request via `SET LOCAL app.current_tenant_id` inside a transaction
- Scope all ORM queries automatically via middleware — never rely on developers remembering manual WHERE clauses
- Use UUIDs for tenant-scoped primary keys; never use auto-incrementing integers
- Separate admin routes with distinct auth mechanism; never reuse tenant user sessions for admin access

### retail-expert
- Ensure 99.9%+ POS uptime; implement offline mode for network outages
- Use barcode scanning and support multiple payment methods
- Implement cycle counting programs and ABC analysis for inventory prioritization
- Maintain FIFO and accurate stock records with appropriate reorder points
- Enable omnichannel support (BOPIS, ship from store, unified inventory)
- Implement loyalty programs, personalized marketing, and abandoned cart recovery
- Never silo online/offline systems or skip inventory tracking

### fastapi
- Always prefer `Annotated` style for parameters (`Path`, `Query`, `Header`, `Body`) and `Depends()`
- Do NOT use Ellipsis (`...`) as default for required parameters or Pydantic `Field(...)`
- Always declare return types or `response_model` to validate, filter, and serialize responses
- Use `fastapi dev` for local development; define entrypoint in `pyproject.toml` when possible
- Add router-level prefix, tags, and dependencies in `APIRouter()`, not in `include_router()`
- Use `async def` only when calling async code; default to `def` for sync/blocking logic
- Do not use Pydantic `RootModel` — use regular type annotations with `Annotated` and `Field`

## Project Conventions

| File | Path | Notes |
|------|------|-------|

No project convention files (AGENTS.md, CLAUDE.md, .cursorrules, GEMINI.md, copilot-instructions.md) found in project root.
