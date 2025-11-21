#!/bin/bash
# Verification script for test token setup
# Checks all components are properly configured

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "Integration Test Token Setup Verification"
echo "═══════════════════════════════════════════════════════════════"
echo

# Check 1: Token generator script exists
echo "✓ Checking token generation script..."
if [ -f "scripts/generate_authkit_token.py" ]; then
    echo "  ✅ scripts/generate_authkit_token.py exists"
else
    echo "  ❌ scripts/generate_authkit_token.py not found"
    exit 1
fi

# Check 2: Token generator is executable
echo "✓ Testing token generation..."
TOKEN=$(python scripts/generate_authkit_token.py 2>/dev/null)
if [ -n "$TOKEN" ]; then
    echo "  ✅ Token generated successfully"
    echo "     Token length: ${#TOKEN} chars"
    echo "     Token preview: ${TOKEN:0:50}..."
else
    echo "  ❌ Failed to generate token"
    exit 1
fi

# Check 3: Token has correct structure
echo "✓ Validating token structure..."
PART_COUNT=$(echo "$TOKEN" | awk -F'.' '{print NF}')
if [ "$PART_COUNT" = "3" ]; then
    echo "  ✅ Token has 3 parts (header.payload.signature)"
else
    echo "  ❌ Token should have 3 parts, found $PART_COUNT"
    exit 1
fi

# Check 4: Token can be decoded
echo "✓ Decoding token claims..."
DECODED=$(python scripts/generate_authkit_token.py --decode 2>&1 | grep -c "email" || true)
if [ "$DECODED" -gt "0" ]; then
    echo "  ✅ Token claims successfully decoded"
else
    echo "  ❌ Failed to decode token claims"
    exit 1
fi

# Check 5: Conftest has updated fixture
echo "✓ Checking integration conftest..."
if grep -q "create_unsigned_jwt" tests/integration/conftest.py; then
    echo "  ✅ integration_auth_token fixture updated with token generation"
else
    echo "  ❌ integration_auth_token fixture not updated"
    exit 1
fi

# Check 6: Conftest sets ATOMS_TEST_MODE
echo "✓ Checking test mode configuration..."
if grep -q 'ATOMS_TEST_MODE.*true' tests/integration/conftest.py; then
    echo "  ✅ test_server fixture sets ATOMS_TEST_MODE=true"
else
    echo "  ❌ test_server fixture does not set ATOMS_TEST_MODE"
    exit 1
fi

# Check 7: Server has unsigned JWT support
echo "✓ Checking server auth implementation..."
if grep -q "_verify_unsigned_jwt\|ATOMS_TEST_MODE" services/auth/hybrid_auth_provider.py; then
    echo "  ✅ Server supports unsigned JWT verification"
else
    echo "  ❌ Server missing unsigned JWT support"
    exit 1
fi

# Check 8: Documentation exists
echo "✓ Checking documentation..."
DOCS_FOUND=0
if [ -f "INTEGRATION_TESTING_QUICKSTART.md" ]; then
    echo "  ✅ INTEGRATION_TESTING_QUICKSTART.md"
    DOCS_FOUND=$((DOCS_FOUND + 1))
fi
if [ -f "docs/INTEGRATION_TEST_GUIDE.md" ]; then
    echo "  ✅ docs/INTEGRATION_TEST_GUIDE.md"
    DOCS_FOUND=$((DOCS_FOUND + 1))
fi
if [ -f "docs/sessions/20251115-authkit-test-tokens/00_SESSION_OVERVIEW.md" ]; then
    echo "  ✅ Session documentation"
    DOCS_FOUND=$((DOCS_FOUND + 1))
fi

if [ "$DOCS_FOUND" -ge 2 ]; then
    echo "  ✅ Documentation comprehensive ($DOCS_FOUND of 3 found)"
else
    echo "  ⚠️  Some documentation missing (found $DOCS_FOUND of 3)"
    # Don't fail on docs, it's optional for verification
fi

# Check 9: Python syntax
echo "✓ Checking Python syntax..."
if python -m py_compile scripts/generate_authkit_token.py 2>/dev/null; then
    echo "  ✅ scripts/generate_authkit_token.py syntax OK"
else
    echo "  ❌ Python syntax error in token generator"
    exit 1
fi

if python -m py_compile tests/integration/conftest.py 2>/dev/null; then
    echo "  ✅ tests/integration/conftest.py syntax OK"
else
    echo "  ❌ Python syntax error in conftest"
    exit 1
fi

# Check 10: Token generation with environment variables
echo "✓ Testing token generation with custom settings..."
CUSTOM_EMAIL="test@example.com"
CUSTOM_TOKEN=$(AUTHKIT_EMAIL="$CUSTOM_EMAIL" python scripts/generate_authkit_token.py 2>/dev/null)
if [ -n "$CUSTOM_TOKEN" ]; then
    echo "  ✅ Custom token generation works"
else
    echo "  ❌ Failed to generate custom token"
    exit 1
fi

echo
echo "═══════════════════════════════════════════════════════════════"
echo "✅ All verification checks passed!"
echo "═══════════════════════════════════════════════════════════════"
echo
echo "Next steps:"
echo "  1. Run integration tests:"
echo "     python cli.py test run --scope integration"
echo
echo "  2. View token claims:"
echo "     python scripts/generate_authkit_token.py --decode"
echo
echo "  3. Generate token with custom email:"
echo "     AUTHKIT_EMAIL='custom@example.com' python scripts/generate_authkit_token.py"
echo
echo "  4. Read quick-start guide:"
echo "     cat INTEGRATION_TESTING_QUICKSTART.md"
echo
