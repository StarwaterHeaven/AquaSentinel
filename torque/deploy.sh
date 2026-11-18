#!/bin/bash
# Deploy the AquaSentinel report store (Cloudflare Worker) from this folder.
# Run from a Mac terminal:  bash deploy.sh            (add --qatom the first time, or when the
#                                                     sponsor seller account's Client ID/secret change)
# Writes the secrets (write path, item 212's Authorization value) to SECRET-aquasentinel-reports.txt
# (chmod 600) and a result log without secrets to aqs-deploy-result-<time>.txt.
# Live sponsorships: real $1 payments on Qatom item 212; Qatom donates the total to WaterAid Canada.
set -uo pipefail
cd "$(dirname "$0")"
[ -f wrangler.toml ] || cd worker
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

echo "== 4. Write secrets"
if [ -s "$SECRET_FILE" ]; then
  WP=$(sed -n 's/^WRITE_PATH=//p' "$SECRET_FILE")
  FT=$(sed -n 's/^FUND_ITEM_AUTHORIZATION=Bearer //p' "$SECRET_FILE")
fi
if [ -z "${WP:-}" ]; then WP=$(openssl rand -hex 16); fi
if [ -z "${FT:-}" ]; then FT=$(openssl rand -hex 24); fi
printf "%s" "$WP" | $WR secret put WRITE_PATH || { echo "STOP: secret put failed"; exit 1; }
printf "%s" "$FT" | $WR secret put QATOM_FULFILMENT_TOKEN || { echo "STOP: secret put failed"; exit 1; }
if [ "${1:-}" = "--qatom" ]; then
  echo "Qatom credentials of the seller account that owns item 212 (dashboard.qatom.ai > API credentials)."
  read -r -p "Qatom Client ID: " CID </dev/tty
  read -r -s -p "Qatom Client secret (not shown): " CSEC </dev/tty; echo
  printf "%s" "$CID" | $WR secret put QATOM_CLIENT_ID >/dev/null && printf "%s" "$CSEC" | $WR secret put QATOM_CLIENT_SECRET >/dev/null && echo "Qatom credentials stored as Worker secrets."
fi
umask 077
cat > "$SECRET_FILE" <<EOF
WRITE_PATH=$WP
TORQUE_WEBHOOK=$BASE/in/$WP
QATOM_ENDPOINT=$BASE/q/$WP
RESET=$BASE/reset/$WP
FUND_ITEM_ENDPOINT=$BASE/qatom/fund
FUND_ITEM_AUTHORIZATION=Bearer $FT
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
echo "funds (public):    $(code $BASE/funds)  (want 200)"
echo "fund item, no auth: $(code -X POST $BASE/qatom/fund)  (want 404)"
echo "fund/start:        $(curl -s -X POST -H 'content-type: application/json' -d '{"wp_id":"9999"}' $BASE/fund/start | tr -d '\n' | cut -c1-100)  (want invalid)"
echo "== Done. Public read URL: $BASE/reports"
