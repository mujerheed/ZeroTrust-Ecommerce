#!/bin/bash
# Cleanup Script - Remove redundant, temporary, and unnecessary files

set -e

cd "/home/secure/Desktop/Shobhit University/3rd Semester/Minor Project/ZeroTrust-Ecommerce"

echo "🧹 TrustGuard Cleanup Script"
echo "============================"
echo ""

# Track what we're doing
CLEANED=0

echo "📦 Step 1: Remove Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Python cache cleaned"
CLEANED=$((CLEANED + 1))

echo ""
echo "📦 Step 2: Remove log files..."
find . -type f -name "*.log" -delete 2>/dev/null || true
find . -type f -name "*.log.*" -delete 2>/dev/null || true
rm -f /tmp/trustguard_server.log 2>/dev/null || true
echo "✅ Log files removed"
CLEANED=$((CLEANED + 1))

echo ""
echo "📦 Step 3: Remove build artifacts..."
rm -rf backend/deployment-backend 2>/dev/null || true
rm -rf backend/package 2>/dev/null || true
rm -f backend/*.zip 2>/dev/null || true
rm -f backend/lambda-deployment.zip 2>/dev/null || true
rm -f trustguard-backend-*.tar.gz 2>/dev/null || true
rm -f trustguard-deployment-*.tar.gz 2>/dev/null || true
rm -f build.log 2>/dev/null || true
echo "✅ Build artifacts removed"
CLEANED=$((CLEANED + 1))

echo ""
echo "📦 Step 4: Remove duplicate/redundant test files..."

# Keep only essential test files, remove duplicates
cd backend

# Remove old/redundant test files (keep the latest versions)
rm -f test_buyer_auth_e2e.py 2>/dev/null || true  # Covered by test_complete_buyer_flow.py
rm -f test_ceo_e2e.py 2>/dev/null || true  # Covered by test_ceo_registration.py
rm -f test_ceo_escalation_manual.py 2>/dev/null || true  # Covered by test_vendor_approval.py
rm -f test_order_e2e.py 2>/dev/null || true  # Covered by test_complete_buyer_flow.py
rm -f test_otp_debug.py 2>/dev/null || true  # Debug file, not needed
rm -f test_e2e_complete.py 2>/dev/null || true  # Redundant with other tests

echo "✅ Redundant test files removed"
CLEANED=$((CLEANED + 1))

cd ..

echo ""
echo "📦 Step 5: Remove duplicate documentation..."

# Keep only the final, comprehensive docs
cd .gemini/antigravity/brain/*/

# Remove redundant/superseded docs
rm -f trustguard_comprehensive_audit.md 2>/dev/null || true  # Superseded by walkthrough.md
rm -f otp_troubleshooting.md 2>/dev/null || true  # Info in production_readiness_qa.md
rm -f system_status.md 2>/dev/null || true  # Info in walkthrough.md
rm -f instagram_2m_order_test.md 2>/dev/null || true  # Specific test, covered in testing_checklist.md

echo "✅ Redundant documentation removed"
CLEANED=$((CLEANED + 1))

cd ../../../../

echo ""
echo "📦 Step 6: Remove temporary/scratch files..."
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.bak" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
echo "✅ Temporary files removed"
CLEANED=$((CLEANED + 1))

echo ""
echo "📦 Step 7: Remove node_modules if present (can reinstall)..."
# Commented out - uncomment if you want to remove node_modules
# rm -rf frontend/node_modules 2>/dev/null || true
# echo "✅ node_modules removed (run npm install to restore)"
echo "⏭️  Skipped node_modules (keeping installed packages)"

echo ""
echo "📦 Step 8: Clean up frontend build artifacts..."
rm -rf frontend/.next/cache 2>/dev/null || true
rm -rf frontend/.next/lock 2>/dev/null || true
rm -rf frontend/out 2>/dev/null || true
echo "✅ Frontend build cache cleaned"
CLEANED=$((CLEANED + 1))

echo ""
echo "============================"
echo "✅ Cleanup Complete!"
echo "============================"
echo ""
echo "📊 Summary:"
echo "  - Python cache: Removed"
echo "  - Log files: Removed"
echo "  - Build artifacts: Removed"
echo "  - Redundant tests: 6 files removed"
echo "  - Redundant docs: 4 files removed"
echo "  - Temp files: Removed"
echo "  - Frontend cache: Cleaned"
echo ""
echo "📁 Kept Essential Files:"
echo "  Backend:"
echo "    - Core services (auth, order, ceo, vendor, integrations)"
echo "    - 9 essential test scripts"
echo "    - Production deployment scripts"
echo "  Frontend:"
echo "    - Next.js app (with node_modules)"
echo "    - Build output (.next)"
echo "  Documentation:"
echo "    - 13 comprehensive guides"
echo "    - Sample receipts (3 images)"
echo ""
echo "💾 Disk space saved: $(du -sh . | cut -f1) total project size"
echo ""
echo "🎯 Next: Review remaining files with 'git status'"
