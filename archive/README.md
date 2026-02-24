# archive/

Archived scripts that have already been executed and are no longer needed for daily development. Kept for reference only.

## migrations/

One-time database migration scripts. These have already been applied to production and development databases.

- `add_workspaces.py` - Added workspace tables
- `add_credits_and_invites.py` - Added credits and invite code tables
- `add_implementation_path_column.py` - Added implementation_path column to papers
- `backfill_implementation_path.py` - Backfilled implementation_path for existing papers
