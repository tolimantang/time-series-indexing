#!/bin/bash
# Script to compare ground truth schema with actual database schema

set -e

echo "🔍 Schema Comparison Tool"
echo "========================="

# Check if required environment variables are set
if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
    echo "❌ Missing required environment variables:"
    echo "   DB_HOST, DB_NAME, DB_USER, DB_PASSWORD"
    echo ""
    echo "Example usage:"
    echo "   export DB_HOST=localhost"
    echo "   export DB_PORT=5433"
    echo "   export DB_NAME=financial_postgres"
    echo "   export DB_USER=postgres"
    echo "   export DB_PASSWORD=your_password"
    echo "   ./sql/scripts/compare_schema.sh"
    exit 1
fi

DB_PORT=${DB_PORT:-5432}
PGPASSWORD="$DB_PASSWORD"
export PGPASSWORD

echo "📊 Connecting to database: $DB_HOST:$DB_PORT/$DB_NAME"

# Function to run SQL query
run_query() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$1" 2>/dev/null || echo "ERROR"
}

echo ""
echo "📋 Tables Comparison"
echo "===================="

# Get actual tables from database
echo "🔍 Actual tables in database:"
run_query "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;"

echo ""
echo "📄 Expected tables from schema files:"
grep -h "^CREATE TABLE" sql/schema/tables.sql | sed 's/CREATE TABLE //' | sed 's/ (.*//' | sort

echo ""
echo "📋 Indexes Comparison"
echo "===================="

echo "🔍 Actual indexes in database:"
run_query "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname NOT LIKE '%_pkey' ORDER BY indexname;"

echo ""
echo "📄 Expected indexes from schema files:"
grep -h "^CREATE INDEX" sql/schema/indexes.sql | sed 's/CREATE INDEX //' | sed 's/ ON.*//' | sort

echo ""
echo "📋 Views Comparison"
echo "=================="

echo "🔍 Actual views in database:"
run_query "SELECT table_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name;"

echo ""
echo "📄 Expected views from schema files:"
grep -h "^CREATE OR REPLACE VIEW" sql/schema/views.sql | sed 's/CREATE OR REPLACE VIEW //' | sed 's/ AS.*//' | sort

echo ""
echo "📋 Functions Comparison"
echo "======================"

echo "🔍 Actual functions in database:"
run_query "SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public' AND routine_type = 'FUNCTION' ORDER BY routine_name;"

echo ""
echo "📄 Expected functions from schema files:"
grep -h "^CREATE OR REPLACE FUNCTION" sql/schema/functions.sql | sed 's/CREATE OR REPLACE FUNCTION //' | sed 's/(.*//' | sort

echo ""
echo "✅ Schema comparison completed!"
echo ""
echo "💡 To generate a migration for missing items:"
echo "   ./sql/scripts/create_migration.sh 'add_missing_schema_items'"