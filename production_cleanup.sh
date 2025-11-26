#!/bin/bash
# Production Cleanup Script - Remove Debug Logs and Console Output

set -e

PROJECT_DIR="/home/secure/Desktop/Shobhit University/3rd Semester/Minor Project/ZeroTrust-Ecommerce"
cd "$PROJECT_DIR"

echo "🧹 Production Cleanup - Remove Debug Logs"
echo "=========================================="
echo ""

CLEANED_FILES=0

# Function to remove print statements from Python files
remove_debug_prints() {
    local file=$1
    local backup="${file}.backup"
    
    # Create backup
    cp "$file" "$backup"
    
    # Remove common debug patterns
    sed -i '/print(f\?".*\[DEBUG\]/d' "$file"
    sed -i '/print(f\?".*DEBUG/d' "$file"
    sed -i '/print(f\?"✅/d' "$file"
    sed -i '/print(f\?"❌/d' "$file"
    sed -i '/print(f\?"🔥/d' "$file"
    sed -i '/logger\.debug(/d' "$file"
    
    # Check if file changed
    if ! cmp -s "$file" "$backup"; then
        echo "  ✓ Cleaned: $file"
        CLEANED_FILES=$((CLEANED_FILES + 1))
        rm "$backup"
    else
        # No changes, restore backup
        mv "$backup" "$file"
    fi
}

echo "📦 Step 1: Remove debug print statements from backend..."
echo ""

# Clean auth service
echo "Cleaning auth_service..."
for file in backend/auth_service/*.py; do
    if [ -f "$file" ]; then
        remove_debug_prints "$file"
    fi
done

# Clean integrations
echo "Cleaning integrations..."
for file in backend/integrations/*.py; do
    if [ -f "$file" ]; then
        remove_debug_prints "$file"
    fi
done

# Clean other services
for service in order_service ceo_service vendor_service receipt_service; do
    echo "Cleaning $service..."
    for file in backend/$service/*.py; do
        if [ -f "$file" ] 2>/dev/null; then
            remove_debug_prints "$file"
        fi
    done
done

echo ""
echo "📦 Step 2: Remove console.log from frontend..."
echo ""

# Clean frontend JavaScript/TypeScript files
find frontend/app -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" 2>/dev/null | while read file; do
    if [ -f "$file" ]; then
        backup="${file}.backup"
        cp "$file" "$backup"
        
        # Remove console.log, console.debug, console.warn (keep console.error)
        sed -i '/console\.log(/d' "$file"
        sed -i '/console\.debug(/d' "$file"
        
        if ! cmp -s "$file" "$backup"; then
            echo "  ✓ Cleaned: $file"
            CLEANED_FILES=$((CLEANED_FILES + 1))
            rm "$backup"
        else
            mv "$backup" "$file"
        fi
    fi
done

echo ""
echo "📦 Step 3: Update logger configuration for production..."
echo ""

# Update common/logger.py to use WARNING level in production
if [ -f "backend/common/logger.py" ]; then
    cat > backend/common/logger.py << 'EOF'
"""
Structured logging configuration for TrustGuard.
Production mode: WARNING level (no DEBUG/INFO logs)
Development mode: DEBUG level (all logs)
"""

import logging
import sys
import os
from datetime import datetime

# Determine environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# Set log level based on environment
if ENVIRONMENT == 'production':
    LOG_LEVEL = logging.WARNING  # Only warnings and errors in production
else:
    LOG_LEVEL = logging.DEBUG  # All logs in development

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('trustguard')
logger.setLevel(LOG_LEVEL)

# Disable debug logs in production
if ENVIRONMENT == 'production':
    logger.debug = lambda *args, **kwargs: None
    logger.info = lambda *args, **kwargs: None

def log_security_event(user_id: str, event_type: str, metadata: dict = None):
    """Log security events (always logged, even in production)."""
    logger.warning(f"SECURITY_EVENT: {event_type} | User: {user_id} | {metadata or {}}")

def log_error(message: str, exc_info=None):
    """Log errors (always logged)."""
    logger.error(message, exc_info=exc_info)
EOF
    echo "  ✓ Updated logger.py for production"
    CLEANED_FILES=$((CLEANED_FILES + 1))
fi

echo ""
echo "📦 Step 4: Remove test print statements..."
echo ""

# Clean test files (but keep test output)
for file in backend/test_*.py; do
    if [ -f "$file" ]; then
        backup="${file}.backup"
        cp "$file" "$backup"
        
        # Only remove [DEBUG] prints, keep test output
        sed -i '/print(.*\[DEBUG\]/d' "$file"
        
        if ! cmp -s "$file" "$backup"; then
            echo "  ✓ Cleaned: $file"
            CLEANED_FILES=$((CLEANED_FILES + 1))
            rm "$backup"
        else
            mv "$backup" "$file"
        fi
    fi
done

echo ""
echo "📦 Step 5: Create production environment flag..."
echo ""

# Update .env.production to set ENVIRONMENT=production
if [ -f "backend/.env.production" ]; then
    if ! grep -q "^ENVIRONMENT=production" backend/.env.production; then
        sed -i '1i ENVIRONMENT=production' backend/.env.production
        echo "  ✓ Added ENVIRONMENT=production to .env.production"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Production Cleanup Complete!"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "  Files cleaned: $CLEANED_FILES"
echo ""
echo "🎯 What was removed:"
echo "  ✓ Debug print statements (print with [DEBUG], emojis)"
echo "  ✓ logger.debug() calls"
echo "  ✓ console.log() and console.debug() from frontend"
echo "  ✓ Unnecessary development logs"
echo ""
echo "🎯 What was kept:"
echo "  ✓ logger.error() - Error logging"
echo "  ✓ logger.warning() - Security events"
echo "  ✓ console.error() - Frontend errors"
echo "  ✓ Test output (for test scripts)"
echo ""
echo "📝 Production logging:"
echo "  - Set ENVIRONMENT=production in .env"
echo "  - Only WARNING and ERROR logs will show"
echo "  - All DEBUG and INFO logs suppressed"
echo ""
echo "🚀 Ready for production deployment!"
