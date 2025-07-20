#!/bin/bash

# Script to push code to multiple repositories
# Usage: ./push_to_repos.sh [commit message]

# Default commit message if not provided
COMMIT_MSG=${1:-"Update code"}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting repository push process...${NC}"

# Check if there are changes to commit
if [[ -z $(git status -s) ]]; then
  echo -e "${YELLOW}No changes to commit.${NC}"
else
  # Add all changes
  echo -e "${YELLOW}Adding all changes...${NC}"
  git add .
  
  # Commit changes
  echo -e "${YELLOW}Committing changes with message: ${COMMIT_MSG}${NC}"
  git commit -m "$COMMIT_MSG"
  
  # Push to origin (GitHub)
  echo -e "${YELLOW}Pushing to GitHub...${NC}"
  if git push origin main; then
    echo -e "${GREEN}Successfully pushed to GitHub.${NC}"
  else
    echo -e "${RED}Failed to push to GitHub.${NC}"
    exit 1
  fi
  
  # Add more repositories here if needed
  # Example:
  # echo -e "${YELLOW}Pushing to secondary repository...${NC}"
  # if git push secondary main; then
  #   echo -e "${GREEN}Successfully pushed to secondary repository.${NC}"
  # else
  #   echo -e "${RED}Failed to push to secondary repository.${NC}"
  # fi
fi

echo -e "${GREEN}Repository push process completed.${NC}"