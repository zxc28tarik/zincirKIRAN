# Free-Only Development Path

Zincir Kıran development must not depend on paid infrastructure at this stage.

## Current rule

Until explicitly changed by the owner:

- Do not create paid Supabase projects.
- Do not purchase Borsa İstanbul DataStore products.
- Do not add paid data APIs.
- Do not require paid cloud warehouses.
- InvestingPro+ may be used only because the owner already has access; it must not become a mandatory runtime dependency.
- Prefer official free KAP / Borsa İstanbul public surfaces.
- Keep database schema portable and reproducible in Git.

## Database strategy

The canonical schema remains PostgreSQL-compatible under supabase/schemas/.

Development and tests must be able to proceed without a hosted Supabase project.

The live hosted database is an optional deployment target, not a development blocker.

## Data-source strategy

Priority for the free phase:

1. KAP public disclosure pages and downloadable official files
2. Borsa İstanbul free public market/reference pages
3. Company-published reports linked from KAP
4. Existing owner access to InvestingPro+ for manual/cross-check research only
5. Free public web sources with preserved provenance

## Upgrade trigger

Paid infrastructure or data may be reconsidered only if a specific blocker is demonstrated, documented, and cannot be solved reliably with free official/public sources.
