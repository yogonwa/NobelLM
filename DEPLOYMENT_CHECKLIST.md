# 🚀 NobelLM Fly.io Deployment Checklist

## Pre-Deployment Verification

### ✅ Environment Setup
- [ ] Fly CLI installed: `fly --version`
- [ ] Logged into Fly.io: `fly auth whoami`
- [ ] OpenAI API key available: `echo $OPENAI_API_KEY`
- [ ] Git LFS tracking confirmed: `git lfs track`
- [ ] All changes committed to migration branch

### ✅ Backend Verification
- [ ] FastAPI app starts locally: `uvicorn backend.app.main:app --reload`
- [ ] Health check endpoint works: `curl http://localhost:8000/api/health`
- [ ] Query endpoint works: `curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" -d '{"query":"test"}'`
- [ ] RAG pipeline loads FAISS index successfully
- [ ] Theme embeddings are accessible
- [ ] All environment variables configured in `backend/app/config.py`

### ✅ Frontend Verification
- [ ] React app builds successfully: `cd frontend && npm run build`
- [ ] Development server works: `npm run dev`
- [ ] API integration works in development
- [ ] All components render correctly
- [ ] Nobel logo and assets load properly
- [ ] Responsive design works on mobile

### ✅ Docker Verification
- [ ] Backend Dockerfile exists and is valid
- [ ] Frontend Dockerfile exists and is valid
- [ ] Nginx configuration is correct
- [ ] Docker Compose works locally (optional)

### ✅ Data Verification
- [ ] FAISS index files present in `data/faiss_index_bge-large/`
- [ ] Theme embeddings present in `data/theme_embeddings/`
- [ ] All data files tracked by Git LFS
- [ ] Data directory structure matches Dockerfile expectations

## Deployment Steps

### 1. Set Environment Variables
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 2. Run Deployment Script
```bash
./scripts/deploy.sh
```

### 3. Verify Deployment
- [ ] Backend API responds: `curl https://nobellm-api.fly.dev/api/health`
- [ ] Frontend loads: `curl https://nobellm-web.fly.dev`
- [ ] API documentation accessible: `https://nobellm-api.fly.dev/docs`
- [ ] Query functionality works end-to-end

## Post-Deployment Verification

### ✅ Backend Health Checks
- [ ] Health endpoint: `https://nobellm-api.fly.dev/api/health`
- [ ] Root endpoint: `https://nobellm-api.fly.dev/`
- [ ] Query endpoint: `https://nobellm-api.fly.dev/api/query`
- [ ] Models endpoint: `https://nobellm-api.fly.dev/api/models`

### ✅ Frontend Health Checks
- [ ] Home page loads: `https://nobellm-web.fly.dev`
- [ ] About page loads: `https://nobellm-web.fly.dev/about`
- [ ] Query interface functional
- [ ] Source citations display correctly
- [ ] Responsive design works

### ✅ Integration Tests
- [ ] Submit a test query through the frontend
- [ ] Verify response includes answer and sources
- [ ] Check that source citations are clickable
- [ ] Test error handling with invalid queries
- [ ] Verify loading states work correctly

### ✅ Performance Checks
- [ ] Initial page load time < 3 seconds
- [ ] Query response time < 10 seconds
- [ ] No console errors in browser
- [ ] Images and assets load quickly

## Troubleshooting

### Common Issues

**Backend Deployment Fails**
- Check Fly.io logs: `fly logs --app nobellm-api`
- Verify environment variables: `fly secrets list --app nobellm-api`
- Check volume mounting: `fly volumes list --app nobellm-api`

**Frontend Deployment Fails**
- Check build logs: `fly logs --app nobellm-web`
- Verify Dockerfile syntax
- Check nginx configuration

**API Connection Issues**
- Verify CORS configuration in backend
- Check API URL in frontend configuration
- Test API endpoints directly

**Data Loading Issues**
- Check FAISS index files are present
- Verify volume mounting configuration
- Check file permissions in container

### Rollback Plan
If deployment fails:
1. Check logs: `fly logs --app nobellm-api` and `fly logs --app nobellm-web`
2. Rollback to previous version: `fly deploy --image-label <previous-version>`
3. Fix issues and redeploy

## Success Criteria

✅ **Deployment Complete When:**
- Both backend and frontend are accessible via HTTPS
- Query functionality works end-to-end
- All health checks pass
- Performance is acceptable
- No critical errors in logs
- UI renders correctly on desktop and mobile

## Next Steps After Deployment

1. **Update Documentation**
   - Update README.md with production URLs
   - Document deployment process
   - Update migration status

2. **Monitor Performance**
   - Set up logging and monitoring
   - Track query response times
   - Monitor error rates

3. **Plan Future Enhancements**
   - Custom domain setup
   - CDN integration
   - Database for query logging
   - User analytics

---

**Last Updated:** June 2025  
**Status:** Ready for deployment 