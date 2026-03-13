#!/bin/bash

# Barcode Management System - Setup Verification Script
# This script verifies that the complete barcode management system is properly set up

echo "======================================"
echo "Barcode Management System Setup Check"
echo "======================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BENCH_PATH="/home/mi-cloud/vecmocon-bench"
APP_PATH="$BENCH_PATH/apps/vecmocon_customization"
SITE="dev-erp.vecmocon.com"

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2 (missing: $1)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2 (missing: $1)"
        return 1
    fi
}

echo "1. Checking File Structure..."
echo "----------------------------"

check_file "$APP_PATH/vecmocon_customization/override/barcode_api.py" "barcode_api.py"
check_file "$APP_PATH/vecmocon_customization/override/barcode_utils.py" "barcode_utils.py"
check_file "$APP_PATH/vecmocon_customization/public/js/barcode_generator.js" "barcode_generator.js"
check_file "$APP_PATH/vecmocon_customization/public/js/barcode_scanner.js" "barcode_scanner.js"
check_file "$APP_PATH/vecmocon_customization/public/css/barcode_generator.css" "barcode_generator.css"
check_file "$APP_PATH/vecmocon_customization/vecomocon/doctype/barcode_log/barcode_log.json" "barcode_log.json"
check_file "$APP_PATH/vecmocon_customization/templates/barcode_label.html" "barcode_label.html"
check_file "$APP_PATH/vecmocon_customization/config/desktop.py" "desktop.py"
check_file "$APP_PATH/vecmocon_customization/install.py" "install.py"
check_file "$APP_PATH/vecmocon_customization/hooks.py" "hooks.py"

echo ""
echo "2. Checking Configuration..."
echo "----------------------------"

# Check hooks.py for page_js
if grep -q "barcode-generator" "$APP_PATH/vecmocon_customization/hooks.py"; then
    echo -e "${GREEN}✓${NC} page_js configured for barcode-generator"
else
    echo -e "${RED}✗${NC} page_js not configured in hooks.py"
fi

# Check hooks.py for app_include
if grep -q "app_include_css" "$APP_PATH/vecmocon_customization/hooks.py"; then
    echo -e "${GREEN}✓${NC} app_include_css configured"
else
    echo -e "${RED}✗${NC} app_include_css not configured"
fi

if grep -q "app_include_js" "$APP_PATH/vecmocon_customization/hooks.py"; then
    echo -e "${GREEN}✓${NC} app_include_js configured"
else
    echo -e "${RED}✗${NC} app_include_js not configured"
fi

# Check after_install hook
if grep -q "after_install" "$APP_PATH/vecmocon_customization/hooks.py"; then
    echo -e "${GREEN}✓${NC} after_install hook configured"
else
    echo -e "${RED}✗${NC} after_install hook not configured"
fi

echo ""
echo "3. Checking Dependencies..."
echo "----------------------------"

# Check if qrcode is installed
cd "$BENCH_PATH"
if ./env/bin/pip list | grep -q "qrcode"; then
    echo -e "${GREEN}✓${NC} qrcode package installed"
else
    echo -e "${YELLOW}!${NC} qrcode package not installed (will install: run 'bench --site $SITE migrate')"
fi

if ./env/bin/pip list | grep -q "Pillow"; then
    echo -e "${GREEN}✓${NC} Pillow package installed"
else
    echo -e "${YELLOW}!${NC} Pillow package not installed (required for qrcode[pil])"
fi

echo ""
echo "4. System Summary..."
echo "----------------------------"
echo -e "Bench Path: ${YELLOW}$BENCH_PATH${NC}"
echo -e "App Path: ${YELLOW}$APP_PATH${NC}"
echo -e "Site: ${YELLOW}$SITE${NC}"
echo -e "DocType: ${YELLOW}Barcode Log (vecmocon/module)${NC}"

echo ""
echo "======================================"
echo "Setup Verification Complete!"
echo "======================================"
echo ""
echo "Next Steps:"
echo "1. Run migrations: bench --site $SITE migrate"
echo "2. Clear cache: bench --site $SITE clear-cache"
echo "3. Restart: bench restart"
echo "4. Access at: http://localhost:8000/app/barcode-generator"
echo ""
