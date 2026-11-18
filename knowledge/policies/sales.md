# Sales policy

## Discount authority
| Who | Max discount on list price |
|---|---|
| Sales executive | [[ % ]] |
| Owner | Above that |

## Margin floor
- Minimum gross margin per order: [[ % ]]. Below it, the owner must approve.

## Follow-up standard
- First response to a new lead: [[ same day / within 2 hours ]].
- Follow up a quoted lead every [[ 3 ]] days until closed or lost.
- A lead is **stale** after [[ 3 ]] days with no touch (used by `tools/leads_report.py --stale-days`).

## Monthly targets and incentive slabs
Fill in `data/templates/incentive_slabs.csv` (copy it to `data/live/` with real
numbers). Example structure: achievement % of target → incentive % of sales.

| Achievement of target | Incentive |
|---|---|
| [[ < 80% ]] | [[ 0% ]] |
| [[ 80–99% ]] | [[ x% of sales ]] |
| [[ ≥ 100% ]] | [[ y% of sales ]] |
