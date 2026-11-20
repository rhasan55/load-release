# First sprint: one load lifecycle, one accountable release

A proposed allocation for approximately 20 hours of technical PM time. This is a bounded discovery and shadow-mode milestone, not a promise to ship all CENTRIX integrations in one week. Developer implementation time is separate; estimates follow discovery.

| PM work | Hours | Concrete output |
| --- | ---: | --- |
| Operations and accounting walkthrough | 3 | One agreed load lifecycle, field ownership and definition of a verified POD. |
| Existing code, API access and backlog review | 4 | Current architecture, named owners, credentials/scopes inventory and dependency list. |
| Integration contracts and failure reproduction | 4 | Normalized identity/version contract, sandbox fixtures and reproducible issue tickets. |
| Acceptance review and shadow reconciliation | 5 | Entity-level counts/cents comparison, QA evidence, exception queue and rollback rehearsal. |
| Team coordination and owner communication | 4 | Daily blocker updates, scope decisions, a demo and written release decision. |
| **Total** | **20** | **A reviewed shadow-mode slice with explicit blockers.** |

## Backlog slice

| Item | Owner to assign with existing team | Acceptance evidence | Dependency |
| --- | --- | --- | --- |
| Normalize source identity and source version | Integration developer | Tenant-scoped mapping; duplicate/reorder/conflict fixtures; original source references retained. | Vendor sandbox access and actual schema. |
| Resolve invoice-206 conflict | Accounting integration developer + accounting owner | One authoritative newer value; no stale fallback; source export reconciles. | Accounting determines the source record. |
| Map unknown-truck | Operations + integration developer | Verified identity, audit entry and deterministic replay. | Operations confirms vehicle/load association. |
| Gate invoice drafts on evidence | Backend developer + QA | Delivery/POD ownership tests and no duplicate invoice create. | Agreed policy on documents and existing invoices. |
| Restrict AI to supported internal drafts | AI developer + operations reviewer | Labeled supported/unsupported set; unsafe actions blocked; human review required. | Representative operations examples. |
| Reconcile and stage rollout | Technical PM + QA + accounting owner | Ingress-to-projection entity counts and cents; exception counts; restore/replay evidence. | All earlier gates plus vendor source exports. |

## Proposed source contracts to validate

- Alvys: confirm customer API entitlement, scopes, load identifiers and authoritative lifecycle transitions. Authentication documentation describes client credentials; access is not assumed.
- Samsara: verify signed ingress, persist before acknowledging, then process asynchronously. Preserve event identity; do not infer delivery from a geofence. Respect documented rate limits and inspect webhook metrics.
- QuickBooks: hydrate changed entities and reconcile using CDC when notifications are missed. Separate entity snapshots from financial deltas and serialize updates per company realm. Acknowledge promptly; work asynchronously.
- DAT: treat load-board access and licensing as an explicit dependency. No invented public endpoint or automated booking. It is outside this first slice.
- Documents: establish who verifies the POD, how its source is retained, and what to do when a document is missing or disputed.

## Definition of ready

A ticket has a reproducer, input/output examples, business owner, developer owner, dependency, acceptance check and rollback behavior. The current team estimates implementation after reviewing the actual codebase. No invented delivery dates.

## Definition of done

Executed unit and integration checks; reviewer sign-off on source ownership; reconciled vendor snapshots; visible exceptions with owners; observable queue lag and replay behavior; sandbox write controls; rollback exercised. Production release requires the owner's approval after these checks, plus the company's actual security and operational requirements.

## Owner update format

**Decision:** Hold rollout; run shadow mode only. **Evidence:** invoice conflict and unmapped identity remain; vendor reconciliation has not run. **Owners:** accounting integration developer and accounting owner for FIN-02, operations plus integration developer for MAP-03. **Next decision:** review reconciled source snapshots and replay results. **Scope:** one fleet/load lifecycle; no customer messaging or autonomous invoice creation.

## Rollback and monitoring

Keep ingestion durable while disabling downstream writes with a feature flag. Preserve source IDs, payload hashes and mapping versions. Restore the prior read model or rebuild from a known checkpoint, then reconcile source counts and amounts. This repository demonstrates replay in memory; it does not implement the persistent infrastructure.

In shadow mode, inspect queue age, duplicate rate, unknown mappings, revision conflicts, source lag, invoice/payment reconciliation differences and held-agent proposals. Set alert thresholds with the operations team from baseline data. No uptime or performance claim is made from these fixtures.
