#!/bin/bash

# SST Setup Script for Atoms MCP Server
# This script helps you set up SST for the first time

set -e

echo "🚀 Setting up SST for Atoms MCP Server"
echo "========================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi
echo "✅ Node.js $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi
echo "✅ npm $(npm --version)"

# Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "✅ uv $(uv --version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.12."
    exit 1
fi
echo "✅ Python $(python3 --version)"

# Check AWS CLI (optional but recommended)
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI $(aws --version)"
else
    echo "⚠️  AWS CLI not found (optional but recommended)"
fi

echo ""
echo "📦 Installing dependencies..."
echo ""

# Install Node.js dependencies (SST CLI)
echo "Installing Node.js dependencies..."
npm install

echo ""
echo "Installing Python dependencies with uv..."
uv sync

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Check if AWS credentials are configured
echo "🔐 Checking AWS credentials..."
if [ -f ~/.aws/credentials ] || [ -n "$AWS_ACCESS_KEY_ID" ]; then
    echo "✅ AWS credentials found"
else
    echo "⚠️  AWS credentials not found. You'll need to configure them:"
    echo "   Run: aws configure"
    echo "   Or set environment variables:"
    echo "     export AWS_ACCESS_KEY_ID=your_key"
    echo "     export AWS_SECRET_ACCESS_KEY=your_secret"
fi

echo ""
echo "📝 Next steps:"
echo ""
echo "1. Configure AWS credentials (if not done):"
echo "   aws configure"
echo ""
echo "2. Set up SST secrets:"
echo "   npx sst secret set SupabaseUrl \"https://your-project.supabase.co\""
echo "   npx sst secret set SupabaseKey \"your-supabase-anon-key\""
echo "   npx sst secret set WorkosApiKey \"your-workos-api-key\""
echo "   npx sst secret set WorkosClientId \"your-workos-client-id\""
echo "   npx sst secret set WorkosRedirectUri \"https://your-domain.com/auth/complete\""
echo ""
echo "3. Start local development:"
echo "   npm run dev"
echo ""
echo "4. Or deploy to AWS:"
echo "   npm run deploy"
echo ""
echo "📚 For more information, see SST_SETUP.md"
echo ""
echo "✨ Setup complete!"

