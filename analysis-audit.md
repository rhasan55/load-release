# Checks and development notes

- Replayed the full stream three times; load projections and issue records remain identical.
- Shuffled delivery order with a fixed seed; current state remains identical.
- Recomputed accounting in SQLite separately from Python; cents match for all three loads.
- Tested shared event IDs across fleets, unmapped source IDs, conflicting event IDs, equal-revision conflicts, future occurrences and float money.
- Verified the POD hold at 18:00 and its availability at 18:12. Later evidence cannot rewrite the earlier result.
- Verified five structured note fixtures; only the supported internal note passes to human review. Extra schema fields and another tenant are rejected.
- Required failed and not-run gates block release even though all automated tests pass.
- During review, tightened conflicting event-ID handling so the affected load is held, not merely omitted from the ledger.
- Matched the prior Intuit and claims-report typography, width, tabs, methods links and concise README structure.

See test-results.txt for the executed output. No throughput, vendor sandbox or live-model evaluation has been run.
