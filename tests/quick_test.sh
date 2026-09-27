#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "Login user1..."
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=password123" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Test vulnerable endpoint. user1 can access user2 order. This is expected for BOLA demo."
curl -s "$BASE_URL/orders/vulnerable/2" -H "Authorization: Bearer $TOKEN"
echo

echo "Test secure endpoint. user1 should be blocked from user2 order."
curl -s "$BASE_URL/orders/2" -H "Authorization: Bearer $TOKEN"
echo
