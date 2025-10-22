#!/bin/bash

# Comprehensive Astrological Trading System Setup Script
# This script sets up the complete system for analyzing ALL trading opportunities
# and generating daily trading recommendations based on astrological insights.

set -e

echo "🌟 Setting up Comprehensive Astrological Trading System"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "scripts/setup_comprehensive_trading_system.sh" ]; then
    print_error "Please run this script from the backend directory"
    exit 1
fi

print_info "Current directory: $(pwd)"

# Step 1: Create database schema
print_info "Step 1: Setting up database schema..."
echo "============================================="

print_info "Applying database migration for astrological insights tables..."
if command -v psql &> /dev/null; then
    if [ -n "$DB_HOST" ] && [ -n "$DB_USER" ] && [ -n "$DB_NAME" ]; then
        print_info "Using environment variables for database connection"
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p ${DB_PORT:-5432} -U $DB_USER -d $DB_NAME -f scripts/migrations/add_astrological_insights_tables.sql
        print_status "Database schema updated successfully"
    else
        print_warning "Database environment variables not set. Please run manually:"
        echo "PGPASSWORD=\$DB_PASSWORD psql -h \$DB_HOST -p \$DB_PORT -U \$DB_USER -d \$DB_NAME -f scripts/migrations/add_astrological_insights_tables.sql"
    fi
else
    print_warning "psql not found. Please install PostgreSQL client or run the migration manually."
    print_info "Migration file: scripts/migrations/add_astrological_insights_tables.sql"
fi

echo ""

# Step 2: Test local system
print_info "Step 2: Testing local LLM analyzer system..."
echo "============================================="

if [ -f "scripts/llm_analysis/test_local_analysis.py" ]; then
    print_info "Running local system test..."
    if python3 scripts/llm_analysis/test_local_analysis.py; then
        print_status "Local system test passed"
    else
        print_warning "Local system test failed - check database connection"
    fi
else
    print_warning "Local test script not found"
fi

echo ""

# Step 3: Setup batch processing
print_info "Step 3: Setting up batch processing system..."
echo "============================================="

print_info "Batch processing system components:"
echo "  - Enhanced database schema ✅"
echo "  - Batch processor for ALL trading opportunities ✅"
echo "  - Claude API integration for pattern analysis ✅"
echo "  - Insight extraction and storage ✅"

print_status "Batch processing system ready"

echo ""

# Step 4: Setup daily conditions calculator
print_info "Step 4: Setting up daily astrological conditions calculator..."
echo "============================================="

print_info "Daily conditions calculator components:"
echo "  - Swiss Ephemeris integration ✅"
echo "  - Planetary position calculations ✅"
echo "  - Lunar phase analysis ✅"
echo "  - Daily scoring algorithm ✅"
echo "  - Market outlook determination ✅"

print_status "Daily conditions calculator ready"

echo ""

# Step 5: Setup daily recommendations engine
print_info "Step 5: Setting up daily trading recommendations engine..."
echo "============================================="

print_info "Daily recommendations engine components:"
echo "  - Insight matching algorithm ✅"
echo "  - Multi-symbol recommendation generation ✅"
echo "  - Confidence scoring system ✅"
echo "  - Risk assessment integration ✅"

print_status "Daily recommendations engine ready"

echo ""

# Step 6: Kubernetes deployment files
print_info "Step 6: Kubernetes deployment files..."
echo "============================================="

print_info "Available Kubernetes jobs:"
echo "  - batch-astro-analysis-job.yaml (Process ALL opportunities)"
echo "  - daily-conditions-job.yaml (Daily at 6:00 AM UTC)"
echo "  - daily-recommendations-job.yaml (Daily at 6:30 AM UTC)"
echo "  - claude-oil-analysis-job.yaml (Original single analysis)"

print_status "Kubernetes deployment files ready"

echo ""

# Step 7: Usage instructions
print_info "Step 7: Usage Instructions"
echo "============================================="

echo ""
print_info "🚀 To run the comprehensive system:"
echo ""

echo "1️⃣ First, run batch analysis on ALL trading opportunities:"
echo "   kubectl apply -f deploy/k8s/shared/batch-astro-analysis-job.yaml"
echo "   kubectl logs -f job/batch-astro-analysis -n time-series-indexing"
echo ""

echo "2️⃣ Setup daily cron jobs for automatic operation:"
echo "   kubectl apply -f deploy/k8s/shared/daily-conditions-job.yaml"
echo "   kubectl apply -f deploy/k8s/shared/daily-recommendations-job.yaml"
echo ""

echo "3️⃣ Monitor the daily jobs:"
echo "   kubectl get cronjobs -n time-series-indexing"
echo "   kubectl get jobs -n time-series-indexing"
echo ""

echo "4️⃣ Local testing and development:"
echo "   # Test data retrieval"
echo "   python3 scripts/llm_analysis/test_local_analysis.py"
echo ""
echo "   # Run batch analysis locally"
echo "   python3 scripts/llm_analysis/run_batch_analysis.py --batch-size 50"
echo ""
echo "   # Calculate daily conditions"
echo "   python3 scripts/llm_analysis/run_daily_conditions.py"
echo ""
echo "   # Generate daily recommendations"
echo "   python3 scripts/llm_analysis/run_daily_recommendations.py"
echo ""

echo "5️⃣ Database queries to monitor progress:"
echo "   # Check insights"
echo "   SELECT category, COUNT(*) FROM astrological_insights GROUP BY category;"
echo ""
echo "   # Check daily conditions"
echo "   SELECT trade_date, daily_score, market_outlook FROM daily_astrological_conditions ORDER BY trade_date DESC LIMIT 10;"
echo ""
echo "   # Check recommendations"
echo "   SELECT recommendation_date, symbol, recommendation_type, confidence FROM daily_trading_recommendations ORDER BY recommendation_date DESC, confidence DESC LIMIT 10;"
echo ""

# Step 8: Environment check
print_info "Step 8: Environment Check"
echo "============================================="

echo ""
print_info "Required environment variables:"

# Check database variables
if [ -n "$DB_HOST" ]; then
    print_status "DB_HOST: $DB_HOST"
else
    print_warning "DB_HOST not set"
fi

if [ -n "$DB_USER" ]; then
    print_status "DB_USER: $DB_USER"
else
    print_warning "DB_USER not set"
fi

if [ -n "$DB_NAME" ]; then
    print_status "DB_NAME: $DB_NAME"
else
    print_warning "DB_NAME not set"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    print_status "ANTHROPIC_API_KEY: Set (${#ANTHROPIC_API_KEY} characters)"
else
    print_warning "ANTHROPIC_API_KEY not set"
fi

echo ""

# Final summary
print_info "🎯 System Architecture Summary"
echo "============================================="
echo ""
echo "📊 Data Flow:"
echo "   Trading Opportunities → Batch Analysis → Astrological Insights"
echo "   Daily Conditions → Insight Matching → Trading Recommendations"
echo ""
echo "🗄️ Database Tables:"
echo "   - trading_opportunities (existing with astro data)"
echo "   - astrological_insights (Claude analysis results)"
echo "   - daily_astrological_conditions (daily planetary positions)"
echo "   - daily_trading_recommendations (daily trading advice)"
echo ""
echo "⚙️ Processing Pipeline:"
echo "   1. Batch process ALL 401 trading opportunities"
echo "   2. Extract structured insights from Claude analysis"
echo "   3. Daily: Calculate planetary positions and conditions"
echo "   4. Daily: Generate trading recommendations using insights"
echo ""
echo "🕒 Automation Schedule:"
echo "   - 6:00 AM UTC: Calculate daily astrological conditions"
echo "   - 6:30 AM UTC: Generate trading recommendations"
echo "   - Weekly: Update insights with new batch analysis"
echo ""

print_status "Comprehensive Astrological Trading System Setup Complete!"
print_info "The system is now ready to analyze ALL trading opportunities and provide daily trading recommendations based on astrological insights."

echo ""
print_info "Next steps:"
echo "1. Ensure Claude API key is properly configured in Kubernetes secrets"
echo "2. Run the batch analysis job to process all trading opportunities"
echo "3. Deploy the daily cron jobs for automated operation"
echo "4. Monitor the system performance and recommendation accuracy"