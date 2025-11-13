#!/bin/bash

# Deploy Atoms MCP Server to Google Cloud Run
# Usage: ./scripts/deploy_gcp.sh [PROJECT_ID] [REGION]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Atoms MCP Server to Google Cloud Run${NC}"
echo "=================================================="
echo ""

# Get project ID and region
PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-us-central1}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: PROJECT_ID not set${NC}"
    echo "Usage: ./scripts/deploy_gcp.sh PROJECT_ID [REGION]"
    exit 1
fi

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${YELLOW}📋 Setting project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com

echo ""
echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Check if secrets exist
echo -e "${YELLOW}🔐 Checking secrets...${NC}"

SECRETS=(
    "SUPABASE_URL"
    "SUPABASE_KEY"
    "WORKOS_API_KEY"
    "WORKOS_CLIENT_ID"
    "WORKOS_REDIRECT_URI"
)

MISSING_SECRETS=()

for SECRET in "${SECRETS[@]}"; do
    if ! gcloud secrets describe $SECRET --project=$PROJECT_ID &> /dev/null; then
        MISSING_SECRETS+=($SECRET)
    else
        echo -e "${GREEN}✓${NC} $SECRET exists"
    fi
done

if [ ${#MISSING_SECRETS[@]} -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Missing secrets:${NC}"
    for SECRET in "${MISSING_SECRETS[@]}"; do
        echo "  - $SECRET"
    done
    echo ""
    echo "Create them with:"
    echo "  echo -n 'your-value' | gcloud secrets create SECRET_NAME --data-file=-"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Deploy to Cloud Run
echo -e "${YELLOW}🚢 Deploying to Cloud Run...${NC}"
echo ""

gcloud run deploy atoms-mcp-server \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars ATOMS_FASTMCP_TRANSPORT=http,ATOMS_FASTMCP_HTTP_PATH=/api/mcp \
  --update-secrets SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest,WORKOS_API_KEY=WORKOS_API_KEY:latest,WORKOS_CLIENT_ID=WORKOS_CLIENT_ID:latest,WORKOS_REDIRECT_URI=WORKOS_REDIRECT_URI:latest \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --project $PROJECT_ID

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe atoms-mcp-server \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"
echo ""
echo "Test endpoints:"
echo "  Health: $SERVICE_URL/health"
echo "  MCP: $SERVICE_URL/api/mcp"
echo ""
echo -e "${GREEN}🎉 Done!${NC}"

