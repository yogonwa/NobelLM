# Production Deployment Checklist - Modal Embedder Integration

## 🎯 **Overview**
This checklist covers the complete production deployment of NobelLM with Modal embedding service integration, removing BGE-large dependencies from the backend, and ensuring live E2E functionality.

## 📋 **Pre-Deployment Checklist**

### ✅ **Modal Embedder Service**
- [ ] Modal CLI installed and authenticated (`modal setup`)
- [ ] Modal embedder service deployed (`cd modal_embedder && python deploy.py`)
- [ ] Modal service health verified (`NOBELLM_TEST_MODAL_LIVE=1 python -m pytest tests/e2e/test_modal_service_live.py`)
- [ ] Modal app name confirmed: `nobel-embedder`

### ✅ **Environment Variables**
- [ ] OpenAI API key configured
- [ ] Weaviate API key configured
- [ ] Production environment variables set
- [ ] CORS origins configured for production domains

### ✅ **Code Changes**
- [ ] Backend config updated with Modal service settings
- [ ] Fly.io configuration updated with production environment
- [ ] Dockerfile updated to remove BGE-large dependencies
- [ ] Environment template created

## 🚀 **Deployment Steps**

### **Step 1: Deploy Modal Embedder Service**
```bash
# Navigate to modal embedder directory
cd modal_embedder

# Deploy the service
python deploy.py

# Verify deployment
NOBELLM_TEST_MODAL_LIVE=1 python -m pytest tests/e2e/test_modal_service_live.py -v
```

**Expected Output:**
```
🎯 Nobel Embedder Service Deployment
========================================
✅ App is already deployed and running!
```

### **Step 2: Deploy Backend API**
```bash
# Navigate to project root
cd /Users/joegonwa/Projects/NobelLM

# Deploy backend to Fly.io
fly deploy --config fly.toml

# Verify deployment
fly status --app nobellm-api
```

**Expected Output:**
```
Deploying nobellm-api
...
✅ Deployment successful
```

### **Step 3: Deploy Frontend**
```bash
# Navigate to frontend directory
cd frontend

# Deploy frontend to Fly.io
fly deploy --config fly.toml

# Verify deployment
fly status --app nobellm-web
```

**Expected Output:**
```
Deploying nobellm-web
...
✅ Deployment successful
```

## 🔍 **Post-Deployment Verification**

### **Step 1: Backend Health Check**
```bash
# Test backend API health
curl https://nobellm-api.fly.dev/health

# Expected: {"status": "healthy", "environment": "production"}
```

### **Step 2: Modal Service Integration Test**
```bash
# Test Modal embedding service integration
curl -X POST https://nobellm-api.fly.dev/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What did Toni Morrison say about justice?"}'

# Expected: Valid response with answer and sources
```

### **Step 3: Frontend Integration Test**
```bash
# Test frontend connectivity
curl https://nobellm-web.fly.dev

# Expected: Frontend loads successfully
```

### **Step 4: Live E2E Test**
```bash
# Run comprehensive E2E tests against production
NOBELLM_TEST_MODAL_LIVE=1 python -m pytest tests/e2e/ -m e2e -v
```

## 🎯 **Success Criteria**

### ✅ **Modal Service**
- [ ] Modal embedder service deployed and healthy
- [ ] Embedding generation working correctly
- [ ] Performance acceptable (< 2 seconds per embedding)
- [ ] Error handling and fallbacks working

### ✅ **Backend API**
- [ ] Backend deployed and responding
- [ ] Environment detection working (production mode)
- [ ] Modal service integration working
- [ ] No BGE-large model loading in production
- [ ] Weaviate integration working
- [ ] CORS configured correctly

### ✅ **Frontend**
- [ ] Frontend deployed and accessible
- [ ] API communication working
- [ ] Query submission and response display working
- [ ] Error handling working

### ✅ **End-to-End**
- [ ] Complete user query → answer flow working
- [ ] Source citations displaying correctly
- [ ] Performance acceptable (< 10 seconds total)
- [ ] Error scenarios handled gracefully

## 🔧 **Troubleshooting**

### **Modal Service Issues**
```bash
# Check Modal service logs
modal logs nobel-embedder

# Redeploy if needed
cd modal_embedder && python deploy.py
```

### **Backend Issues**
```bash
# Check backend logs
fly logs --app nobellm-api

# Restart if needed
fly restart --app nobellm-api
```

### **Frontend Issues**
```bash
# Check frontend logs
fly logs --app nobellm-web

# Restart if needed
fly restart --app nobellm-web
```

### **Environment Issues**
```bash
# Check environment variables
fly ssh console --app nobellm-api
env | grep NOBELLM

# Update environment if needed
fly secrets set NOBELLM_ENVIRONMENT=production --app nobellm-api
```

## 📊 **Performance Monitoring**

### **Key Metrics to Monitor**
- Modal embedding response time (< 2s)
- Backend API response time (< 5s)
- Frontend load time (< 3s)
- Error rates (< 1%)
- Memory usage (stable)

### **Monitoring Commands**
```bash
# Check Modal service performance
modal logs nobel-embedder --follow

# Check backend performance
fly logs --app nobellm-api --follow

# Check frontend performance
fly logs --app nobellm-web --follow
```

## 🎉 **Completion Checklist**

- [ ] Modal embedder service deployed and tested
- [ ] Backend deployed with Modal integration
- [ ] Frontend deployed and connected
- [ ] Live E2E tests passing
- [ ] Performance metrics acceptable
- [ ] Error handling verified
- [ ] Documentation updated

## 📞 **Support**

If issues arise during deployment:
1. Check logs for specific error messages
2. Verify environment variables are set correctly
3. Test individual components in isolation
4. Review Modal service health and quotas
5. Check Fly.io service status and quotas

---

**Last Updated:** January 2025  
**Status:** Ready for Production Deployment 