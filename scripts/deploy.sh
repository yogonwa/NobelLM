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

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
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
    
    # Skip volume creation for now - can be added later
    print_status "Skipping volume creation for initial deployment..."
    
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
    
    # Check if OPENAI_API_KEY is set
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY environment variable not set."
        print_warning "Please set it before running this script:"
        print_warning "export OPENAI_API_KEY=your_api_key_here"
        exit 1
    fi
    
    # Set secrets for backend
    print_status "Setting secrets for backend..."
    fly secrets set OPENAI_API_KEY="$OPENAI_API_KEY" --app nobellm-api
    
    print_status "Secrets configured successfully!"
}

# Function to check deployment status
check_status() {
    print_status "Checking deployment status..."
    
    echo ""
    echo "Backend Status:"
    fly status --app nobellm-api
    
    echo ""
    echo "Frontend Status:"
    fly status --app nobellm-web
    
    echo ""
    print_status "Deployment URLs:"
    echo "Backend API: https://nobellm-api.fly.dev"
    echo "Frontend: https://nobellm-web.fly.dev"
    echo "API Docs: https://nobellm-api.fly.dev/docs"
}

# Main deployment flow
main() {
    print_status "Starting deployment process..."
    
    # Set secrets first
    set_secrets
    
    # Deploy backend
    deploy_backend
    
    # Deploy frontend
    deploy_frontend
    
    # Check status
    check_status
    
    print_status "🎉 Deployment completed successfully!"
    echo ""
    print_status "Your NobelLM application is now live at:"
    echo "  Frontend: https://nobellm-web.fly.dev"
    echo "  Backend API: https://nobellm-api.fly.dev"
    echo "  API Documentation: https://nobellm-api.fly.dev/docs"
}

# Run main function
main "$@" 