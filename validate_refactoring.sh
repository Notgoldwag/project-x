#!/bin/bash
# Refactoring Validation Script
# Validates that the home.html refactoring was successful

echo "==================================================================="
echo "Home.html Feature Refactoring - Validation Script"
echo "==================================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Function to check if a file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} File missing: $1"
        ((FAILED++))
        return 1
    fi
}

# Function to check if a string is in a file
check_string_in_file() {
    if grep -q "$2" "$1"; then
        echo -e "${GREEN}✓${NC} Found in $1: $2"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} Not found in $1: $2"
        ((FAILED++))
        return 1
    fi
}

# Function to check if a string is NOT in a file
check_string_not_in_file() {
    if ! grep -q "$2" "$1"; then
        echo -e "${GREEN}✓${NC} Correctly removed from $1: $2"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Still exists in $1: $2"
        ((FAILED++))
        return 1
    fi
}

# Function to validate JavaScript syntax
check_js_syntax() {
    if node -c "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Valid JavaScript: $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} Invalid JavaScript: $1"
        ((FAILED++))
        return 1
    fi
}

echo "1. Checking Feature Files..."
echo "-------------------------------------------------------------------"
check_file "features/authentication/script.js"
check_file "features/authentication/template.html"
check_file "features/background_animation/script.js"
check_file "features/background_animation/template.html"
check_file "features/cursor_glow/script.js"
check_file "features/cursor_glow/template.html"
check_file "features/navigation/script.js"
check_file "features/navigation/template.html"
check_file "features/profile_widget/script.js"
check_file "features/profile_widget/template.html"
echo ""

echo "2. Checking Reorganized Files..."
echo "-------------------------------------------------------------------"
check_file "features/prompt_playground/playground.js"
check_file "features/prompt_injection/promptinjections.js"
check_file "features/ai_assistant/chat.js"
echo ""

echo "3. Checking Documentation..."
echo "-------------------------------------------------------------------"
check_file "REFACTORING_GUIDE.md"
check_file "features/README.md"
check_file "REFACTORING_SUMMARY.md"
echo ""

echo "4. Validating JavaScript Syntax..."
echo "-------------------------------------------------------------------"
check_js_syntax "features/authentication/script.js"
check_js_syntax "features/cursor_glow/script.js"
check_js_syntax "features/navigation/script.js"
check_js_syntax "features/profile_widget/script.js"
echo ""

echo "5. Checking home.html Integration..."
echo "-------------------------------------------------------------------"
check_string_in_file "home.html" "features/cursor_glow/script.js"
check_string_in_file "home.html" "features/navigation/script.js"
check_string_in_file "home.html" "REFACTORED:"
echo ""

echo "6. Verifying Inline Code Removal..."
echo "-------------------------------------------------------------------"
# Check that cursor glow inline code was removed
check_string_not_in_file "home.html" "const glow = document.getElementById('cursor-glow');"
# Check that navigation inline code was removed  
check_string_not_in_file "home.html" "const settingsBtn = document.getElementById('settingsBtn');"
echo ""

echo "7. Checking File Moves..."
echo "-------------------------------------------------------------------"
# Verify files were moved from static/js/
if [ ! -f "static/js/playground.js" ]; then
    echo -e "${GREEN}✓${NC} playground.js successfully moved from static/js/"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} playground.js still in static/js/"
    ((FAILED++))
fi

if [ ! -f "static/js/promptinjections.js" ]; then
    echo -e "${GREEN}✓${NC} promptinjections.js successfully moved from static/js/"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} promptinjections.js still in static/js/"
    ((FAILED++))
fi

if [ ! -f "static/js/chat.js" ]; then
    echo -e "${GREEN}✓${NC} chat.js successfully moved from static/js/"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} chat.js still in static/js/"
    ((FAILED++))
fi
echo ""

echo "8. Checking Backup Files..."
echo "-------------------------------------------------------------------"
check_file "home_original_backup.html"
echo ""

echo "==================================================================="
echo "Validation Results"
echo "==================================================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validation checks passed!${NC}"
    echo "The refactoring was successful."
    exit 0
else
    echo -e "${YELLOW}⚠ Some validation checks failed.${NC}"
    echo "Please review the failures above."
    exit 1
fi
