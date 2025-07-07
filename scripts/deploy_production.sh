#!/bin/bash

# Production Deployment Script for NobelLM
# This script automates the deployment of Modal embedder service, backend, and frontend

set -e  # Exit on any error

echo "🚀 NobelLM Production Deployment"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists modal; then
    print_error "Modal CLI not found. Please install Modal first:"
    echo "   pip install modal"
    echo "   modal setup"
    exit 1
fi

if ! command_exists fly; then
    print_error "Fly CLI not found. Please install Fly CLI first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

print_success "Prerequisites check passed"

# Step 1: Deploy Modal Embedder Service
print_status "Step 1: Deploying Modal Embedder Service..."
cd modal_embedder

if python deploy.py; then
    print_success "Modal embedder service deployed successfully"
else
    print_error "Modal embedder service deployment failed"
    exit 1
fi

cd ..

# Step 2: Verify Modal Service Health
print_status "Step 2: Verifying Modal Service Health..."
if NOBELLM_TEST_MODAL_LIVE=1 python -m pytest tests/e2e/test_modal_service_live.py::test_modal_service_health_only -v; then
    print_success "Modal service health check passed"
else
    print_warning "Modal service health check failed - continuing anyway"
fi

# Step 3: Deploy Backend API
print_status "Step 3: Deploying Backend API..."
if fly deploy --config fly.toml; then
    print_success "Backend API deployed successfully"
else
    print_error "Backend API deployment failed"
    exit 1
fi

# Step 4: Verify Backend Health
print_status "Step 4: Verifying Backend Health..."
sleep 10  # Wait for deployment to stabilize

if curl -f https://nobellm-api.fly.dev/health >/dev/null 2>&1; then
    print_success "Backend health check passed"
else
    print_warning "Backend health check failed - check logs with: fly logs --app nobellm-api"
fi

# Step 5: Deploy Frontend
print_status "Step 5: Deploying Frontend..."
cd frontend

if fly deploy --config fly.toml; then
    print_success "Frontend deployed successfully"
else
    print_error "Frontend deployment failed"
    exit 1
fi

cd ..

# Step 6: Verify Frontend
print_status "Step 6: Verifying Frontend..."
sleep 10  # Wait for deployment to stabilize

if curl -f https://nobellm-web.fly.dev >/dev/null 2>&1; then
    print_success "Frontend health check passed"
else
    print_warning "Frontend health check failed - check logs with: fly logs --app nobellm-web"
fi

# Step 7: Run E2E Tests
print_status "Step 7: Running E2E Tests..."
if NOBELLM_TEST_MODAL_LIVE=1 python -m pytest tests/e2e/test_e2e_frontend_contract.py::test_realistic_embedding_service_integration -v; then
    print_success "E2E tests passed"
else
    print_warning "E2E tests failed - check logs for details"
fi

# Final status
echo ""
echo "🎉 Deployment Summary"
echo "===================="
echo "✅ Modal Embedder Service: https://modal.com/apps/nobel-embedder"
echo "✅ Backend API: https://nobellm-api.fly.dev"
echo "✅ Frontend: https://nobellm-web.fly.dev"
echo ""
echo "📋 Next Steps:"
echo "1. Test the application manually at https://nobellm-web.fly.dev"
echo "2. Monitor logs: fly logs --app nobellm-api --follow"
echo "3. Check Modal service: modal logs nobel-embedder --follow"
echo "4. Run full E2E test suite: NOBELLM_TEST_MODAL_LIVE=1 python -m pytest tests/e2e/ -m e2e -v"
echo ""
echo "🔧 Troubleshooting:"
echo "- Backend logs: fly logs --app nobellm-api"
echo "- Frontend logs: fly logs --app nobellm-web"
echo "- Modal logs: modal logs nobel-embedder"
echo "- Restart services: fly restart --app nobellm-api"
echo ""
print_success "Production deployment completed!" 