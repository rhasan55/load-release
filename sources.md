# Public context

Reviewed November 20, 2026. Public documentation informs the failure scenarios; the sample is not a vendor-certified integration.

- [Moldex role and Ion Repida as poster](https://www.linkedin.com/jobs/view/4491260729/). The posting names CENTRIX, an existing development team and integrations with Alvys, Samsara, QuickBooks and DAT. It asks for progress tracking, technical tasks, QA and accountability, approximately 20 hours/week.
- [CENTRIX](https://centrix.group/). Public platform context; not evidence of internal architecture or company performance.
- [Alvys authentication](https://alvys.readme.io/reference/authentication). Client-credentials authentication, scoped applications and API-access prerequisites. This demo has no Alvys token or adapter.
- [Samsara webhooks](https://developers.samsara.com/docs/webhooks). Event identity, asynchronous handling and signature headers. This demo uses a normalized event envelope, not a copied vendor payload.
- [Samsara delivery and retry guidance](https://kb.samsara.com/hc/en-us/articles/360020400952-Webhooks). Quick acknowledgement and retries motivate a replay-safe consumer. Vendor guidance can change; verify before implementation.
- [Samsara rate limits](https://developers.samsara.com/docs/rate-limits). Endpoint limits and Retry-After. No requests to these APIs are made here.
- [QuickBooks webhook best practices](https://static.developer.intuit.com/output_html/qbo/docs/develop/webhooks/best-practices.html). Out-of-sequence notifications, asynchronous processing and CDC reconciliation for missed changes.

No proprietary data, real driver locations, customer records, company logos or credentials are included. The claims about balances, tests and release holds refer only to the included fixtures. No inference about corporate ownership is needed for this project.
