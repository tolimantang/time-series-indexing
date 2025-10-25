#!/bin/bash
# Script to create new Flyway migrations

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <migration_description>"
    echo "Example: $0 'add_user_preferences_table'"
    exit 1
fi

DESCRIPTION=$1
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Find the next version number
LAST_VERSION=$(ls sql/flyway/V*.sql 2>/dev/null | tail -1 | sed 's/.*V\([0-9]*\).*/\1/' || echo "0")
NEXT_VERSION=$(printf "%03d" $((LAST_VERSION + 1)))

# Create the migration file
MIGRATION_FILE="sql/flyway/V${NEXT_VERSION}__${DESCRIPTION}.sql"

cat > "$MIGRATION_FILE" << EOF
-- Migration: ${DESCRIPTION}
-- Created: $(date)
-- Version: V${NEXT_VERSION}

-- Add your SQL migration here
-- Remember:
-- - Use IF NOT EXISTS for CREATE TABLE
-- - Use IF EXISTS for DROP TABLE
-- - Consider data migration needs
-- - Test rollback procedures manually

-- Example:
-- CREATE TABLE IF NOT EXISTS new_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

EOF

echo "✅ Created migration file: $MIGRATION_FILE"
echo ""
echo "Next steps:"
echo "1. Edit the migration file with your SQL changes"
echo "2. Test the migration locally"
echo "3. Update flyway-simple-migration.yaml ConfigMap with the new migration"
echo "4. Run the migration: kubectl apply -f deploy/k8s/shared/flyway-simple-migration.yaml"