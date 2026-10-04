# Analyst Estimates / Revisions Ingestion

This layer is for analyst-consensus information exported from InvestingPro+ or another timestamped source.

## Why it is separate

The historical Total Rasyo data packages do not contain a real analyst EPS/revenue revision history. This makes estimates/revisions one of the few data families where InvestingPro+ can add genuinely new information.

## Historical PIT requirements

A historical estimate snapshot must contain:
- ticker
- fiscal period end
- estimate snapshot timestamp
- EPS consensus, when available
- revenue consensus, when available
- analyst count, when available
- high/low range or dispersion, when available
- source identity

A revision feature requires **two historically timestamped snapshots for the same ticker and fiscal period**.

Allowed:
`revision = later historical consensus - earlier historical consensus`

Forbidden:
- taking today's consensus and pretending it existed six months ago;
- using today's analyst count historically;
- using Pro Fair Value, ProTips, AI-picked scores, analyst rating scores or other derived vendor ratings as the model target;
- filling missing estimates with zero/neutral.

## InvestingPro export authority

If an InvestingPro export contains only the current consensus and no historical snapshot timestamp, it is **CURRENT_ONLY**.

It may be useful for:
- live feature calculation
- current Live Shadow
- coverage diagnostics

It cannot be used in a historical backtest as though it were an old estimate.

Historical revisions become trainable only when the export/source exposes historical estimate snapshots with dates.

## Minimum useful export fields

- Ticker
- Fiscal Period
- Estimate Date / Snapshot Date
- EPS Estimate
- Revenue Estimate
- Analyst Count
- EPS High / Low
- Revenue High / Low
- Estimate Dispersion, if available
- Actual EPS / Revenue publication date, if included

Current-only exports should still be kept; their authority is simply lower.
