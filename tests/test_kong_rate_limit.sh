#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://localhost:8080}"

echo "Sending 8 failed login requests to $BASE_URL/auth/login"
echo "Kong config allows only 5 login requests per minute per IP."

for i in 1 2 3 4 5 6 7 8; do
  code=$(curl -s -o /tmp/kong_rate_limit_response.txt -w "%{http_code}" \
    -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=user1&password=wrong_password")
  printf "Attempt %s -> HTTP %s\n" "$i" "$code"
  cat /tmp/kong_rate_limit_response.txt
  printf "\n---\n"
done
