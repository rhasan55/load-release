# Methods and boundaries

## Decision and source ownership

The sample asks whether a load is eligible for human invoice review at 18:00 UTC on November 16, 2026. A previously created invoice is always routed to review of that existing record, not another create. Any unresolved hold remains visible even when an invoice exists.

For this sample only, Alvys owns delivery status; Samsara supplies a location observation; a document-verification service supplies a POD decision; QuickBooks supplies invoice and payment snapshots. These responsibilities need confirmation with the real operations team. A verified POD is a supplied fixture boolean, not an OCR or authenticity claim.

## Event contract

Events are normalized local fixtures. `tenant`, `source`, `event_id`, `external_id`, `entity_id`, positive integer `version`, `occurred_at`, `received_at` and `payload` are required. UTC timestamps use a consistent precision. Receipt time is availability time. Occurrence may not be later than receipt. Source names are allowlisted. Mapping is scoped by tenant and source; a source ID from another fleet cannot join into this fleet.

The code assumes structurally valid fixture objects. It does not implement an HTTP ingress schema, authentication, signature verification, persistent queue, rate limiter or a transactional outbox. A production service must reject malformed envelopes before this projection and persist accepted ingress before acknowledging it.

The version field is an internal adapter contract, not a claim that every vendor exposes this exact sequence number. Real adapters should fetch the authoritative entity, retain its actual version/time fields, define conflicts and deletes, and preserve source payload hashes. Identical revisions with different payloads require reconciliation. Notifications without complete entities must be hydrated before this model.

## Deduplication and ordering

First filter receipt time and tenant. Group by tenant, source and event ID. Repeated deliveries with identical content, except receipt time, collapse. A conflicting use of the same event ID is quarantined and holds the mapped load. Resolve an unmapped identity before projecting it.

Within each mapped load, source and entity, select the largest revision. Conflicting payloads at that revision are excluded and held; the code does not fall back to an older value. Older revisions are retained in the trace but do not overwrite state. Equal revisions with identical payloads are equivalent. This makes projection independent of delivery order and safe to replay in this fixture.

## Accounting

An invoice snapshot and a payment snapshot are distinct entities. Select their current versions before summing money. Amounts use integer USD cents; floats and negative snapshots are held. L-104 has two deliveries of a $2,400 invoice, a $2,400 obsolete payment snapshot and a $500 corrected payment. An incorrect additive consumer reports $4,800 invoiced and $2,900 paid. Their difference happens to equal the correct $1,900 balance, concealing both errors.

The payment correction is illustrative, not an implementation of the QuickBooks payment API. Partial allocations, credits, voids, deleted invoices, unapplied cash, multiple invoices per load, currency, tax and rounding policy need explicit production contracts. The SQL ledger reproduces valid fixture accounting and conflict exclusion; it is not a production warehouse model or a full schema validator.

## Evidence and AI

The validator accepts only an internal draft action and an exact structured schema. Claims must cite current evidence for the same load and fleet. A delivery-status claim must match the selected TMS status; POD must match selected document evidence. A geofence cannot substitute for either. Post-decision documents are unavailable. Sending a message is not an allowed action.

The five candidate notes are authored adversarial fixtures. They do not establish LLM performance, prompt injection resistance or free-text semantic correctness. There is no live retrieval, model call or autonomous dispatch. Extend evaluation with operations-labeled examples before introducing a model; measure supported-claim precision, abstention, inappropriate actions and review effort.

## Release

FIN-02 and MAP-03 are derived from the observed fixture conflicts and unmapped identities. EVT-01, DOC-04 and AI-05 cite executed regression tests. REC-06 is deliberately not run because no vendor data exists. All required checks must pass to become eligible for owner review. A final owner approval remains separate from this gate. These are sample gates, not the complete production control set.

A 30-minute location freshness threshold is an illustrative operations assumption. GPS does not establish remaining driver hours, regulatory compliance or delivery completion. A missing/stale observation holds the sample; a real rollout must define which actions require location and how outage exceptions are approved.
