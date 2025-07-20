#!/bin/bash

echo "🚀 Deploying Sapyyn to Heroku..."

# Commit current changes
git add .
git commit -m "Deploy: $(date)"

# Create Procfile if missing
if [ ! -f "Procfile" ]; then
    echo "web: node server.js" > Procfile
    git add Procfile
    git commit -m "Add Procfile"
fi

# Set Heroku remote
heroku git:remote -a sapyyn-platform

# Set environment variables
echo "⚙️ Setting environment variables..."
heroku config:set NODE_ENV=production -a sapyyn-platform
heroku config:set PORT=443 -a sapyyn-platform
heroku config:set FRONTEND_URL=https://sapyyn-platform-f18042e4f220.herokuapp.com -a sapyyn-platform

# Generate secrets
JWT_SECRET=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -hex 16)
ENCRYPTION_IV=$(openssl rand -hex 8)

heroku config:set JWT_SECRET="$JWT_SECRET" -a sapyyn-platform
heroku config:set ENCRYPTION_KEY="$ENCRYPTION_KEY" -a sapyyn-platform
heroku config:set ENCRYPTION_IV="$ENCRYPTION_IV" -a sapyyn-platform

# Deploy
echo "🚀 Deploying..."
git push heroku master

# Scale
heroku ps:scale web=1 -a sapyyn-platform

echo "✅ Deployment complete!"
echo "🌐 App URL: https://sapyyn-platform-f18042e4f220.herokuapp.com/"

# Show logs
heroku logs --tail -a sapyyn-platform
