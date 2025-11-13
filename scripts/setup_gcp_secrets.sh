#!/bin/bash

# Setup Google Cloud Secrets for Atoms MCP Server
# Usage: ./scripts/setup_gcp_secrets.sh [PROJECT_ID]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔐 Setting up Google Cloud Secrets${NC}"
echo "===================================="
echo ""

# Get project ID
PROJECT_ID=${1:-$(gcloud config get-value project)}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID not set"
    echo "Usage: ./scripts/setup_gcp_secrets.sh PROJECT_ID"
    exit 1
fi

echo "Project ID: $PROJECT_ID"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Enable Secret Manager API
echo -e "${YELLOW}Enabling Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com
echo ""

# Function to create or update secret
create_secret() {
    local SECRET_NAME=$1
    local SECRET_DESCRIPTION=$2
    
    echo -e "${YELLOW}Setting $SECRET_NAME${NC}"
    read -sp "Enter value for $SECRET_NAME: " SECRET_VALUE
    echo ""
    
    if [ -z "$SECRET_VALUE" ]; then
        echo "Skipping empty value"
        return
    fi
    
    # Check if secret exists
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &> /dev/null; then
        echo "Secret exists, adding new version..."
        echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME --data-file=-
    else
        echo "Creating new secret..."
        echo -n "$SECRET_VALUE" | gcloud secrets create $SECRET_NAME \
            --data-file=- \
            --replication-policy="automatic"
    fi
    
    echo -e "${GREEN}✓ $SECRET_NAME set${NC}"
    echo ""
}

# Create secrets
echo "You'll be prompted to enter values for each secret."
echo "Press Enter to skip a secret."
echo ""

create_secret "SUPABASE_URL" "Supabase project URL"
create_secret "SUPABASE_KEY" "Supabase anon/service key"
create_secret "WORKOS_API_KEY" "WorkOS API key"
create_secret "WORKOS_CLIENT_ID" "WorkOS client ID"
create_secret "WORKOS_REDIRECT_URI" "WorkOS redirect URI"

echo ""
echo -e "${GREEN}✅ Secrets setup complete!${NC}"
echo ""
echo "To view secrets:"
echo "  gcloud secrets list --project=$PROJECT_ID"
echo ""
echo "To update a secret:"
echo "  echo -n 'new-value' | gcloud secrets versions add SECRET_NAME --data-file=-"
echo ""
echo "To grant access to Cloud Run:"
echo "  gcloud secrets add-iam-policy-binding SECRET_NAME \\"
echo "    --member='serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com' \\"
echo "    --role='roles/secretmanager.secretAccessor'"

