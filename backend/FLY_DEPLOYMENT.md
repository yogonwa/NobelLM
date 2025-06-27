# Fly.io Deployment Guide

## Environment Variables Setup

For Fly.io deployment, environment variables must be set using Fly's secrets management system. The application no longer relies on `.env` files in production.

### Required Secrets

Set these using `fly secrets set`:

```bash
# OpenAI API Key (required)
fly secrets set OPENAI_API_KEY=sk-your-actual-key-here

# CORS Origins (required for frontend communication)
fly secrets set CORS_ORIGINS=https://nobellm.com,https://www.nobellm.com

# Environment (optional, defaults to production behavior)
fly secrets set ENVIRONMENT=production
```

### Optional Configuration

You can also set these for custom configuration:

```bash
# RAG Configuration
fly secrets set DEFAULT_MODEL=bge-large
fly secrets set MAX_QUERY_LENGTH=1000
fly secrets set DEFAULT_TOP_K=5
fly secrets set DEFAULT_SCORE_THRESHOLD=0.2

# Logging
fly secrets set LOG_LEVEL=INFO
```

### Development vs Production

- **Development**: Use `.env` files locally
- **Production**: Use `fly secrets set` for all sensitive and configuration values

### Verification

After setting secrets, verify they're loaded correctly:

```bash
# Check current secrets
fly secrets list

# View application logs to see CORS configuration
fly logs
```

## CORS Configuration

The CORS origins are parsed from the `CORS_ORIGINS` environment variable as a comma-separated string:

```bash
# Production (frontend domains only)
fly secrets set CORS_ORIGINS=https://nobellm.com,https://www.nobellm.com

# With localhost for testing
fly secrets set CORS_ORIGINS=http://localhost:3000,https://nobellm.com,https://www.nobellm.com
```

## Troubleshooting

If CORS is not working:

1. **Check secrets are set**: `fly secrets list`
2. **Verify environment variables**: Check application logs for CORS configuration
3. **Restart deployment**: `fly deploy` after setting new secrets
4. **Check frontend domain**: Ensure it matches exactly what's in CORS_ORIGINS 