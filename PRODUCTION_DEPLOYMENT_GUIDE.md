# 🚀 NobelLM Production Deployment Guide

## **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Weaviate DB   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Vector DB)   │
│   nobellm-web   │    │   nobellm-api   │    │   Cloud Instance│
│   .fly.dev      │    │   .fly.dev      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## **Pre-Deployment Checklist**

### **1. Environment Variables**
```bash
# Required
export OPENAI_API_KEY="sk-your-openai-key"

# Optional (for Weaviate)
export WEAVIATE_API_KEY="your-weaviate-key"
```

### **2. Local Testing**
```bash
# Test Weaviate health
python tests/e2e/test_weaviate_health.py

# Test full E2E pipeline
python tests/e2e/test_weaviate_e2e.py

# Test backend locally
uvicorn backend.app.main:app --reload
```

### **3. Fly.io Setup**
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login to Fly.io
fly auth login

# Verify login
fly auth whoami
```

## **Deployment Process**

### **Step 1: Deploy Backend**
```bash
# Deploy backend with Weaviate support
./scripts/deploy.sh
```

**What this does:**
- Sets all required secrets (OpenAI, Weaviate, CORS)
- Builds and deploys backend Docker image
- Starts the backend machine

### **Step 2: Verify Backend**
```bash
# Check backend status
fly status --app nobellm-api

# Check logs
fly logs --app nobellm-api

# Test health endpoint
curl https://nobellm-api.fly.dev/api/health

# Test CORS configuration
curl https://nobellm-api.fly.dev/debug/cors
```

### **Step 3: Deploy Frontend**
```bash
# Frontend is deployed automatically by deploy.sh
# Verify frontend status
fly status --app nobellm-web

# Test frontend
curl https://nobellm-web.fly.dev
```

## **Configuration Details**

### **Backend Configuration (`backend/app/config.py`)**
```python
# Weaviate Configuration
use_weaviate: bool = False  # Set via USE_WEAVIATE env var
weaviate_url: str = "https://a0dq8xtrtkw6lovkllxw.c0.us-east1.gcp.weaviate.cloud"
weaviate_api_key: str = ""  # Set via WEAVIATE_API_KEY env var

# CORS Configuration
cors_origins: str = ""  # Set via CORS_ORIGINS env var
```

### **Fly.io Secrets**
```bash
# View current secrets
fly secrets list --app nobellm-api

# Set secrets manually (if needed)
fly secrets set OPENAI_API_KEY="sk-..." --app nobellm-api
fly secrets set WEAVIATE_API_KEY="your-key" --app nobellm-api
fly secrets set USE_WEAVIATE="true" --app nobellm-api
fly secrets set WEAVIATE_URL="https://..." --app nobellm-api
fly secrets set CORS_ORIGINS="https://nobellm.com,https://www.nobellm.com" --app nobellm-api
```

### **Retriever Selection Logic**
The system automatically chooses the retriever based on environment:

1. **Weaviate** (if `USE_WEAVIATE=true`)
2. **FAISS Subprocess** (if `NOBELLM_USE_FAISS_SUBPROCESS=1`)
3. **FAISS In-Process** (default fallback)

## **Monitoring & Troubleshooting**

### **Health Checks**
```bash
# Backend health
curl https://nobellm-api.fly.dev/api/health

# Frontend health
curl https://nobellm-web.fly.dev

# API documentation
curl https://nobellm-api.fly.dev/docs
```

### **Logs**
```bash
# Backend logs
fly logs --app nobellm-api

# Frontend logs
fly logs --app nobellm-web

# Follow logs in real-time
fly logs --app nobellm-api --follow
```

### **Common Issues**

#### **Backend Won't Start**
```bash
# Check machine status
fly status --app nobellm-api

# Start machine manually
fly machine start app --app nobellm-api

# Check logs for errors
fly logs --app nobellm-api
```

#### **Weaviate Connection Issues**
```bash
# Verify secrets are set
fly secrets list --app nobellm-api

# Check Weaviate configuration
fly secrets get USE_WEAVIATE --app nobellm-api
fly secrets get WEAVIATE_URL --app nobellm-api
fly secrets get WEAVIATE_API_KEY --app nobellm-api
```

#### **CORS Issues**
```bash
# Check CORS configuration
curl https://nobellm-api.fly.dev/debug/cors

# Verify frontend domain is in CORS origins
fly secrets get CORS_ORIGINS --app nobellm-api
```

### **Performance Monitoring**
```bash
# Check machine resources
fly status --app nobellm-api

# Monitor logs for performance issues
fly logs --app nobellm-api | grep -i "error\|warning\|timeout"
```

## **Rollback Procedure**

### **Quick Rollback**
```bash
# List recent deployments
fly releases --app nobellm-api

# Rollback to previous version
fly deploy --image-label <previous-version> --app nobellm-api
```

### **Full Rollback**
```bash
# Stop current deployment
fly machine stop app --app nobellm-api

# Deploy previous version
fly deploy --image-label <previous-version> --app nobellm-api

# Start machine
fly machine start app --app nobellm-api
```

## **Scaling & Performance**

### **Current Configuration**
- **Backend**: 1 CPU, 2GB RAM, Performance tier
- **Frontend**: 1 CPU, 512MB RAM, Shared tier
- **Auto-scaling**: Enabled (stops when idle, starts on demand)

### **Scaling Options**
```bash
# Scale backend to multiple machines
fly scale count 2 --app nobellm-api

# Scale to larger machine
fly scale vm performance-2x --app nobellm-api

# Check current scaling
fly status --app nobellm-api
```

## **Security Considerations**

### **Environment Variables**
- All sensitive data stored as Fly.io secrets
- No hardcoded API keys in code
- CORS origins restricted to production domains

### **Network Security**
- HTTPS enforced on all endpoints
- Trusted hosts middleware enabled
- CORS properly configured

### **Application Security**
- Non-root user in Docker containers
- Input validation on all endpoints
- Error messages don't expose sensitive data

## **Maintenance**

### **Regular Tasks**
```bash
# Check for updates
fly releases --app nobellm-api

# Monitor logs for issues
fly logs --app nobellm-api --follow

# Verify health endpoints
curl https://nobellm-api.fly.dev/api/health
```

### **Updates**
```bash
# Deploy updates
./scripts/deploy.sh

# Or deploy manually
fly deploy --app nobellm-api
fly deploy --app nobellm-web
```

## **Success Metrics**

### **Performance Targets**
- **Page Load**: < 3 seconds
- **Query Response**: < 10 seconds
- **Uptime**: > 99.9%
- **Error Rate**: < 1%

### **Monitoring Checklist**
- [ ] Backend responds to health checks
- [ ] Frontend loads without errors
- [ ] Query functionality works end-to-end
- [ ] Weaviate integration functional
- [ ] No critical errors in logs
- [ ] Performance within acceptable limits

---

**Last Updated:** July 2025  
**Version:** 2.0 (Weaviate-enabled) 