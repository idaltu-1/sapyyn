#!/bin/bash

# Script to push only new files to repository without deleting existing files
# Usage: ./push_new_files.sh [commit message]

# Default commit message if not provided
COMMIT_MSG=${1:-"Add NoCodeBackend integration"}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting selective push process...${NC}"

# Add only specific new files
echo -e "${YELLOW}Adding only new files...${NC}"

# Add new files
git add app_example.py
git add controllers/nocodebackend_controller.py
git add routes/nocode_routes.py
git add services/nocodebackend_client.py
git add services/nocodebackend_service.py
git add static/css/logo.css
git add static/images/sapyyn-icon.svg
git add static/images/sapyyn-logo.svg
git add tests/test_nocodebackend.py
git add utils/nocodebackend_utils.py
git add push_to_repos.sh
git add push_new_files.sh

# Add modified files
git add -u .env.example
git add -u README.md
git add -u controllers/promotion_controller.py
git add -u cron_expire_promotions.py
git add -u cron_jobs/expire_promotions.py
git add -u requirements.txt
git add -u static/login.html

# Commit changes
echo -e "${YELLOW}Committing changes with message: ${COMMIT_MSG}${NC}"
git commit -m "$COMMIT_MSG"

# Pull with rebase to avoid conflicts
echo -e "${YELLOW}Pulling latest changes from remote...${NC}"
git pull --rebase origin main

# Push to origin
echo -e "${YELLOW}Pushing to GitHub...${NC}"
if git push origin main; then
  echo -e "${GREEN}Successfully pushed to GitHub.${NC}"
else
  echo -e "${RED}Failed to push to GitHub. You may need to resolve conflicts.${NC}"
  exit 1
fi

echo -e "${GREEN}Push process completed successfully.${NC}"