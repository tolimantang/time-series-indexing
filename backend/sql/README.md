# Database Schema Management with Flyway

This project uses [Flyway](https://flywaydb.org/) for database schema versioning and migrations.

## Directory Structure

```
sql/
├── flyway/                     # Versioned migration files
│   ├── V001__initial_schema.sql
│   └── V004__clean_lunar_patterns_schema.sql
├── schema/                     # Ground truth schema definitions
│   ├── tables.sql             # Table definitions (source of truth)
│   ├── indexes.sql            # Index definitions
│   ├── views.sql              # View definitions
│   └── functions.sql          # Function and trigger definitions
├── scripts/                   # Schema management tools
│   ├── create_migration.sh    # Generate new migration files
│   └── compare_schema.sh      # Compare ground truth vs actual schema
├── flyway.conf               # Flyway configuration
└── README_FLYWAY.md          # This file
```

## Migration Naming Convention

Flyway uses a specific naming convention for migration files:

- **V{version}__{description}.sql** - Versioned migrations (V001__initial_schema.sql)
- **R__{description}.sql** - Repeatable migrations (for views, functions, etc.)

## Workflow for Schema Changes

### 1. Check Current Schema State

```bash
# Compare ground truth schema with actual database
export DB_HOST=localhost DB_PORT=5433 DB_NAME=financial_postgres DB_USER=postgres DB_PASSWORD=''
./sql/scripts/compare_schema.sh
```

### 2. Create a New Migration

```bash
# Generate a new migration file
./sql/scripts/create_migration.sh "add_user_preferences_table"

# This creates: sql/flyway/V005__add_user_preferences_table.sql
```

### 3. Update Ground Truth Schema

```bash
# Add your new table to sql/schema/tables.sql
# Add any indexes to sql/schema/indexes.sql
# Add any views to sql/schema/views.sql
# Add any functions to sql/schema/functions.sql
```

### 4. Edit the Migration File

```sql
-- V005__add_user_preferences_table.sql
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
```

### 3. Update ConfigMap (for Kubernetes deployment)

Add your new migration to `deploy/k8s/shared/flyway-simple-migration.yaml`:

```yaml
data:
  V005__add_user_preferences_table.sql: |
    CREATE TABLE IF NOT EXISTS user_preferences (
      -- your SQL here
    );
```

### 4. Run Migration

```bash
# Apply the migration
kubectl apply -f deploy/k8s/shared/flyway-simple-migration.yaml

# Check migration status
kubectl logs -n time-series-indexing job/flyway-simple-migration
```

## Ground Truth Schema Files

The `sql/schema/` directory contains the **ground truth** definitions of your database schema:

- **`tables.sql`** - All table definitions (the current desired state)
- **`indexes.sql`** - All index definitions
- **`views.sql`** - All view definitions
- **`functions.sql`** - All function and trigger definitions

### Two-Way Workflow

1. **Schema-First**: Update ground truth files → Generate migration
2. **Migration-First**: Create migration → Update ground truth files

Both approaches work, but **always keep the ground truth files in sync** with your actual database state after migrations are applied.

## Migration Best Practices

### ✅ Do

- **Use IF NOT EXISTS** for CREATE TABLE statements
- **Use IF EXISTS** for DROP TABLE statements
- **Make migrations idempotent** (safe to run multiple times)
- **Include rollback instructions** in comments
- **Test migrations locally** before deploying
- **Keep migrations small** and focused
- **Never modify existing migrations** (create new ones instead)

### ❌ Don't

- Don't modify existing migration files
- Don't use DROP TABLE without IF EXISTS
- Don't create migrations that can't be safely re-run
- Don't include environment-specific data
- Don't skip version numbers

## Current Schema State

| Table | Purpose | Status |
|-------|---------|---------|
| `market_data_intraday` | Intraday price data | ✅ Active |
| `daily_planetary_positions` | Astrological positions | ✅ Active |
| `daily_planetary_aspects` | Astrological aspects | ✅ Active |
| `lunar_patterns` | Lunar trading patterns | ✅ Active (V004 cleaned) |
| `astrological_insights` | Trading insights | ✅ Active |
| `daily_astrological_conditions` | Daily conditions | ✅ Active |
| `daily_trading_recommendations` | Trading recommendations | ✅ Active |
| `flyway_schema_history` | Migration tracking | ✅ Flyway managed |

## Local Development

### Running Migrations Locally

```bash
# Install Flyway CLI
# macOS: brew install flyway
# Linux: Download from https://flywaydb.org/download/

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5433  # or 5432
export DB_NAME=financial_postgres
export DB_USER=postgres
export DB_PASSWORD=your_password

# Run migrations
cd sql
flyway -configFiles=flyway.conf -url="jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME}" -user="${DB_USER}" -password="${DB_PASSWORD}" migrate

# Check status
flyway -configFiles=flyway.conf -url="jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME}" -user="${DB_USER}" -password="${DB_PASSWORD}" info
```

### Rollback Strategy

Flyway Community Edition doesn't support automatic rollbacks. For rollbacks:

1. **Create a new migration** with the reverse changes
2. **Test rollback SQL** in your migration comments:

```sql
-- V006__add_column.sql
ALTER TABLE users ADD COLUMN email VARCHAR(255);

-- ROLLBACK SQL (create V007__remove_email_column.sql):
-- ALTER TABLE users DROP COLUMN IF EXISTS email;
```

## Troubleshooting

### Common Issues

1. **Migration checksum mismatch**: Never modify existing migrations
2. **Table already exists**: Use `IF NOT EXISTS` in CREATE statements
3. **Constraint violations**: Check data compatibility before schema changes
4. **Permission errors**: Ensure database user has CREATE/ALTER privileges

### Useful Commands

```bash
# Check migration status
kubectl logs -n time-series-indexing job/flyway-simple-migration

# Force delete a stuck job
kubectl delete job flyway-simple-migration -n time-series-indexing

# Re-run migrations
kubectl delete -f deploy/k8s/shared/flyway-simple-migration.yaml
kubectl apply -f deploy/k8s/shared/flyway-simple-migration.yaml
```

## Migration History

| Version | Description | Date | Status |
|---------|-------------|------|--------|
| V001 | Initial schema baseline | 2025-10-25 | ✅ Applied |
| V004 | Clean lunar_patterns schema | 2025-10-25 | ✅ Applied |

---

For more information, see the [Flyway documentation](https://flywaydb.org/documentation/).