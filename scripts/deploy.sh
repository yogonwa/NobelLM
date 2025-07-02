#!/bin/bash

# NobelLM Fly.io Deployment Script
# This script deploys both backend and frontend to Fly.io

set -e  # Exit on any error

echo "🚀 Starting NobelLM deployment to Fly.io..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Deployment flags
DEPLOY_BACKEND=true
DEPLOY_FRONTEND=true

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --backend-only) DEPLOY_FRONTEND=false ;;
    --frontend-only) DEPLOY_BACKEND=false ;;
    --help)
      echo "Usage: $0 [--backend-only|--frontend-only]"
      echo "  --backend-only: Deploy only the backend API"
      echo "  --frontend-only: Deploy only the frontend"
      echo "  --help: Show this help message"
      exit 0
      ;;
  esac
done

# Function to print colored output with timestamp
print_status() {
    echo -e "${GREEN}[INFO] [$(date '+%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] [$(date '+%H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR] [$(date '+%H:%M:%S')]${NC} $1"
}

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    print_error "Fly CLI is not installed. Please install it first:"
    echo "curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if user is logged in to Fly.io
if ! fly auth whoami &> /dev/null; then
    print_error "Not logged in to Fly.io. Please run: fly auth login"
    exit 1
fi

# Function to deploy backend
deploy_backend() {
    print_status "Deploying backend API..."
    
    # Check if backend app exists, create if not
    if ! fly apps list | grep -q "nobellm-api"; then
        print_status "Creating backend app 'nobellm-api'..."
        fly apps create nobellm-api --org personal
    fi
    
    # Deploy backend
    print_status "Deploying backend with remote build..."
    fly deploy --remote-only --app nobellm-api
    
    print_status "Backend deployed successfully!"
}

# Function to deploy frontend
deploy_frontend() {
    print_status "Deploying frontend..."
    
    # Check if frontend app exists, create if not
    if ! fly apps list | grep -q "nobellm-web"; then
        print_status "Creating frontend app 'nobellm-web'..."
        fly apps create nobellm-web --org personal
    fi
    
    # Deploy frontend
    print_status "Deploying frontend with remote build..."
    cd frontend
    fly deploy --remote-only --app nobellm-web
    cd ..
    
    print_status "Frontend deployed successfully!"
}

# Function to set secrets
set_secrets() {
    print_status "Setting up secrets..."
    
    # Check if secrets already exist
    existing_secrets=$(fly secrets list --app nobellm-api --json 2>/dev/null | jq -r '.[].Name' | sort)
    
    # Set OPENAI_API_KEY if not already set
    if echo "$existing_secrets" | grep -q "OPENAI_API_KEY"; then
        print_status "OPENAI_API_KEY already exists in Fly secrets"
    else
        if [ -z "$OPENAI_API_KEY" ]; then
            print_warning "OPENAI_API_KEY not found in Fly secrets and not set locally."
            print_warning "Please set it before running this script:"
            print_warning "export OPENAI_API_KEY=your_api_key_here"
            exit 1
        fi
        print_status "Setting OPENAI_API_KEY..."
        fly secrets set OPENAI_API_KEY="$OPENAI_API_KEY" --app nobellm-api
    fi
    
    # Set Weaviate secrets if needed
    if echo "$existing_secrets" | grep -q "WEAVIATE_API_KEY"; then
        print_status "Weaviate secrets already exist"
    else
        if [ -n "$WEAVIATE_API_KEY" ]; then
            print_status "Setting Weaviate secrets..."
            fly secrets set WEAVIATE_API_KEY="$WEAVIATE_API_KEY" --app nobellm-api
            fly secrets set USE_WEAVIATE="true" --app nobellm-api
            fly secrets set WEAVIATE_URL="https://a0dq8xtrtkw6lovkllxw.c0.us-east1.gcp.weaviate.cloud" --app nobellm-api
        else
            print_warning "WEAVIATE_API_KEY not set. Weaviate will be disabled."
            fly secrets set USE_WEAVIATE="false" --app nobellm-api
        fi
    fi
    
    # Set CORS origins if not already set
    if echo "$existing_secrets" | grep -q "CORS_ORIGINS"; then
        print_status "CORS_ORIGINS already exists"
    else
        print_status "Setting CORS origins..."
        fly secrets set CORS_ORIGINS="https://nobellm.com,https://www.nobellm.com,https://nobellm-web.fly.dev" --app nobellm-api
    fi
    
    # Set debug logging if not already set
    if echo "$existing_secrets" | grep -q "LOG_LEVEL"; then
        print_status "LOG_LEVEL already exists"
    else
        print_status "Setting debug logging..."
        fly secrets set LOG_LEVEL="DEBUG" --app nobellm-api
    fi
    
    print_status "Secrets configured successfully!"
}

# Function to check deployment status
check_status() {
    print_status "Checking deployment status..."
    
    if [ "$DEPLOY_BACKEND" = true ]; then
        echo ""
        echo "Backend Status:"
        fly status --app nobellm-api
    fi
    
    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo ""
        echo "Frontend Status:"
        fly status --app nobellm-web
    fi
    
    echo ""
    print_status "Deployment URLs:"
    if [ "$DEPLOY_BACKEND" = true ]; then
        echo "Backend API: https://nobellm-api.fly.dev"
        echo "API Docs: https://nobellm-api.fly.dev/docs"
        echo "Health Check: https://nobellm-api.fly.dev/health"
    fi
    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo "Frontend: https://nobellm-web.fly.dev"
    fi
}

# Function to start backend
start_backend() {
    print_status "Starting backend..."
    
    # Get machine ID
    machine_id=$(fly machines list --app nobellm-api --json | jq -r '.[0].id')
    
    if [ -z "$machine_id" ] || [ "$machine_id" = "null" ]; then
        print_error "No machines found for nobellm-api"
        return 1
    fi
    
    print_status "Starting machine: $machine_id"
    fly machine start "$machine_id" --app nobellm-api
    print_status "Backend started successfully!"
}

# Main deployment flow
main() {
    print_status "Starting deployment process..."
    
    # Show deployment plan
    echo ""
    print_status "Deployment Plan:"
    if [ "$DEPLOY_BACKEND" = true ]; then
        echo "  ✅ Backend API (nobellm-api)"
    else
        echo "  ❌ Backend API (skipped)"
    fi
    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo "  ✅ Frontend (nobellm-web)"
    else
        echo "  ❌ Frontend (skipped)"
    fi
    echo ""
    
    # Confirmation prompt
    read -p "⚠️  Ready to deploy to Fly.io? (y/n): " confirm
    if [[ "$confirm" != "y" ]]; then
        print_warning "Aborted by user."
        exit 0
    fi
    
    # Set secrets first
    set_secrets
    
    # Deploy backend
    if [ "$DEPLOY_BACKEND" = true ]; then
        deploy_backend
        # Start backend (it might be stopped)
        start_backend
    fi
    
    # Deploy frontend
    if [ "$DEPLOY_FRONTEND" = true ]; then
        deploy_frontend
    fi
    
    # Check status
    check_status
    
    print_status "🎉 Deployment completed successfully!"
    echo ""
    print_status "Your NobelLM application is now live at:"
    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo "  Frontend: https://nobellm-web.fly.dev"
    fi
    if [ "$DEPLOY_BACKEND" = true ]; then
        echo "  Backend API: https://nobellm-api.fly.dev"
        echo "  API Documentation: https://nobellm-api.fly.dev/docs"
        echo "  Health Check: https://nobellm-api.fly.dev/health"
    fi
}

# Run main function
main "$@" 