#!/bin/bash
# Deploy the AquaSentinel report store (Cloudflare Worker) from this folder.
# Run from a Mac terminal:  bash deploy.sh
# Writes the secret write URL to SECRET-aquasentinel-reports.txt (chmod 600) and
# a result log without the secret to aqs-deploy-result-<time>.txt.
set -uo pipefail
cd "$(dirname "$0")"
TS=$(date +%Y%m%d-%H%M%S)
LOG="aqs-deploy-result-$TS.txt"
SECRET_FILE="SECRET-aquasentinel-reports.txt"
BASE="https://aquasentinel-reports.hassan-khan-cd6.workers.dev"
exec > >(tee "$LOG") 2>&1
echo "== AquaSentinel report store deploy $TS"

echo "== 1. npm install"
npm install --no-audit --no-fund || { echo "STOP: npm install failed"; exit 1; }
WR=./node_modules/.bin/wrangler

echo "== 2. Cloudflare login"
if ! $WR whoami 2>&1 | grep -qi "logged in"; then
  echo "Not logged in: a browser window will open for Cloudflare login."
  $WR login || { echo "STOP: login failed"; exit 1; }
fi
$WR whoami 2>&1 | grep -i -E "logged in|account" | head -5

echo "== 3. Deploy"
$WR deploy || { echo "STOP: deploy failed"; exit 1; }

echo "== 4. Write secret"
if [ -s "$SECRET_FILE" ]; then
  WP=$(sed -n 's/^WRITE_PATH=//p' "$SECRET_FILE")
fi
if [ -z "${WP:-}" ]; then WP=$(openssl rand -hex 16); fi
printf "%s" "$WP" | $WR secret put WRITE_PATH || { echo "STOP: secret put failed"; exit 1; }
umask 077
cat > "$SECRET_FILE" <<EOF
WRITE_PATH=$WP
TORQUE_WEBHOOK=$BASE/in/$WP
QATOM_ENDPOINT=$BASE/q/$WP
RESET=$BASE/reset/$WP
EOF
chmod 600 "$SECRET_FILE"
echo "Secret saved to $SECRET_FILE (not shown here)."

echo "== 5. Verify (waiting 15s)"
sleep 15
code() { curl -s -o /dev/null -w "%{http_code}" "$@"; }
echo "health:            $(code $BASE/health)  (want 200)"
echo "reports (public):  $(code $BASE/reports)  (want 200)"
echo "check (public):    $(curl -s "$BASE/check?wp_id=0631&status=broken" | tr -d '\n' | cut -c1-160)"
echo "write, wrong path: $(code -X POST $BASE/in/wrong-path-0000000000)  (want 404)"
echo "write, GET:        $(code $BASE/in/$WP)  (want 405)"
R=$(curl -s -X POST -H 'content-type: application/json' -d '{"wp_id":"0631","status":"OK","message":"deploy test","reporter":"deploy script"}' "$BASE/in/$WP")
echo "write, test:       $(echo "$R" | tr -d '\n' | cut -c1-120)"
echo "reset after test:  $(curl -s -X POST "$BASE/reset/$WP" | tr -d '\n')"
echo "== Done. Public read URL: $BASE/reports"
