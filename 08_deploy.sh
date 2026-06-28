#!/bin/bash
# 08_deploy.sh
# ==============================================================================
# Automated Deployment Script for tAIatlas.github.io
#
# This script ensures the JSON databases are freshly built, the metadata
# (including the missing codon draft assembly warnings) are properly stamped,
# and stages the changes for deployment. 
#
# IMPORTANT: It will purposefully pause before pushing to allow for data review.
# ==============================================================================

set -e

echo "============================================================"
echo "tAIatlas Deployment Pipeline"
echo "============================================================"

# Ensure we are in the taiatlas.github.io directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${DIR}"

echo "[1/4] Running build_website_json.py..."
python build_website_json.py
echo "[*] Website JSONs built successfully."

echo "[2/4] Running update_db_files.py to stamp missing codon metadata..."
python update_db_files.py
echo "[*] Database metadata stamped successfully."

echo "[3/4] Staging changes in git..."
git add .
git commit -m "chore: auto-deploy updated databases" || echo "[*] No changes to commit."

echo "============================================================"
echo "DEPLOYMENT PAUSED"
echo "============================================================"
echo "The updated database files have been successfully built, stamped,"
echo "and staged locally in git."
echo ""
echo "CRITICAL SAFEGUARD TRIGGERED:"
echo "As requested, the script has stopped here. Please run the statistical"
echo "report script to review the new UCSC and Legacy Anwar data."
echo ""
echo "When you are satisfied with the report and ready to deploy to the live"
echo "GitHub Pages server, manually run:"
echo "    git push origin main"
echo "============================================================"

exit 0
