# NobelLM Performance Stabilization Design

**Date**: 2026-02-05
**Status**: Approved
**Priority**: High - fixes 50% query failure rate
**Budget Constraint**: Keep costs minimal (side project)

---

## Problem Summary

NobelLM currently has a **50% query failure rate** due to frontend timeouts while backend processes slowly. Users experience:
- Query timeouts (frontend gives up before backend completes)
- 30-40 second response times on cold starts
- No feedback during long waits
- Unpredictable success/failure (feels broken)

### Root Causes

**Forensic Evidence from Production Logs:**
```
Query 1 (García Márquez themes):
- Total: 39.0 seconds
- Retrieval: 32.5 seconds (83%)
- LLM: 4.5 seconds (12%)
- Status: Success (but likely timed out on frontend)

Query 2 (Who won 1965):
- Total: 13.8 seconds
- Retrieval: 12.8 seconds (93%)
- LLM: 1.0 seconds (7%)
- Status: Success
```

**Identified Issues:**

1. **Modal Cold Starts** - Embedding service sleeps between requests. First query waits 20-30s for container spinup.

2. **Frontend Timeout Mismatch** - Backend takes 30-40s, frontend likely times out at 10-15s. Creates 50/50 failure rate.

3. **Wasteful Health Checks** - `/health` endpoint queries Qdrant every 15s, causing timeout cascades and wasting API calls.

4. **Inconsistent Retrieval** - Logs show mixing of FAISS and Qdrant, suggesting fallback logic fires unpredictably.

5. **No User Feedback** - Users don't know if query is working or stuck.

---

## Solution Strategy

**Core Philosophy**: Instead of fighting Modal's cold starts (expensive), embrace them with UX and reliability improvements.

**User Acceptance Criteria**:
> "I don't mind a 20-30s fetch IF I know it's working, if I know it won't error but will eventually return response" - User

**Targets**:
- **First query of day**: 20-30s (acceptable with good UX)
- **Subsequent queries**: < 5s (warm Modal)
- **Success rate**: 95%+ (up from 50%)
- **Cost**: No increase (keep min_machines_running = 0)

---

## Architecture Changes

### 1. Frontend UX - Make Waiting Delightful

**Progressive Loading States:**

```
Phase 1 (0-3s): "Warming up the Nobel archives..."
  └─ Animation: Books flying off shelf

Phase 2 (3-10s): "Searching 120 years of speeches..."
  ├─ Progress bar (aesthetic, not real progress)
  └─ Random Nobel facts: "Did you know Toni Morrison was the 8th woman to win?"

Phase 3 (10-20s): "Reading between the lines..."
  └─ Mini word game: "Guess which laureate said: [quote]"
     (User can interact while waiting)

Phase 4 (20-30s): "Almost there! Synthesizing insights..."
  └─ Show anticipation-building message

Error State (30s+): "This is taking longer than usual..."
  ├─ Don't auto-fail - let user decide
  └─ Manual retry button
```

**Technical Implementation:**
- Frontend fires warmup ping on page load: `GET /api/warmup`
- Query timeout: **45 seconds** (up from ~10-15s)
- Retry logic: Manual retry button (no auto-retry)
- Store failed query in `localStorage` for easy retry

### 2. Backend Reliability - Fix the Foundations

**Health Check Refactor:**

Split into two endpoints:

```python
# Fast health check for Fly.io (< 100ms)
GET /healthz
  → Just return 200 OK
  → No external dependencies
  → Used by Fly.io auto-scaling every 15s

# Deep health check for monitoring (manual/rare)
GET /health/deep
  → Check Qdrant connectivity
  → Check Modal availability
  → Return detailed status
  → Only for diagnostics
```

**Warmup Endpoint (Critical Fix):**

```python
GET /api/warmup
  → Fire tiny embedding request to Modal ("hello")
  → Wake up Modal containers (20-30s first time)
  → Return 202 Accepted immediately (don't block)
  → Run in background
  → Subsequent queries hit warm Modal (< 2s)
```

**Consistent Retrieval Path:**

- **Production**: Always use Qdrant (remove FAISS fallback)
- **Development**: Always use FAISS (local, no API calls)
- **Remove**: Dual-mode logic causing inconsistency

### 3. Timeout & Retry Logic

**Frontend Timeout Strategy:**

```typescript
const submitQuery = async (query: string) => {
  setPhase("warming")

  try {
    const response = await fetch("/api/query", {
      timeout: 45000,  // Up from ~10-15s
      signal: AbortSignal.timeout(45000)
    })
    return response

  } catch (error) {
    if (error.name === "TimeoutError") {
      setPhase("timeout")
      return {
        canRetry: true,
        message: "Taking longer than expected. Try again?"
      }
    }
    throw error
  }
}
```

**Backend Timeout Tuning:**

Adjust Modal timeout based on query type:

- **Simple queries** (factual): 15s timeout
- **Thematic queries**: 45s timeout (need more retrieval)
- **Cold start**: 60s timeout on first query after warmup

**Smart Retry:**
- Frontend stores failed query in `localStorage`
- "Try again" button pre-fills last query
- Second attempt hits warm Modal (< 5s expected)
- Expected success rate: 95%+ on retry

### 4. Error Handling & Monitoring

**Graceful Failure Modes:**

```python
class QueryError:
  MODAL_TIMEOUT = {
    "error": "embedding_timeout",
    "user_message": "Our AI is waking up. This happens on the first query of the day. Try again in 10 seconds!",
    "can_retry": True,
    "estimated_wait": 10
  }

  QDRANT_TIMEOUT = {
    "error": "retrieval_timeout",
    "user_message": "The Nobel archive is taking a coffee break. Retry now?",
    "can_retry": True,
    "estimated_wait": 0
  }

  OPENAI_RATE_LIMIT = {
    "error": "llm_rate_limit",
    "user_message": "Too many questions at once! Wait 30 seconds.",
    "can_retry": True,
    "estimated_wait": 30
  }
```

**Lightweight Monitoring:**

- Audit logs (existing) track timing per query type
- Simple metrics endpoint: `GET /api/metrics`
  - Last 10 queries: success/fail/timing
  - Modal/Qdrant health status
  - Uptime since last deploy
- No external APM (costs money)

**Alerting Strategy:**

- If 3+ queries fail in a row → log ERROR with "investigate" tag
- Weekly log review to spot patterns
- No pager duty, no Slack alerts (side project!)

---

## Implementation Plan

### Files to Modify

**Frontend (3 files):**
```
src/components/QueryInterface.tsx
  └─ Add progressive loading states (Phases 1-4)

src/hooks/useQuery.ts
  └─ Increase timeout to 45s, add retry logic

src/App.tsx
  └─ Add warmup ping on mount: fetch("/api/warmup")
```

**Backend (4 files):**
```
backend/app/main.py
  └─ Split /health into /healthz (fast) and /health/deep

backend/app/routes.py
  ├─ Add GET /api/warmup endpoint
  └─ Update query timeout handling

rag/modal_embedding_service.py
  └─ Adjust timeout: 45s for thematic, 15s for factual

fly.toml
  └─ Change health_check path to /healthz
```

**Configuration (1 file):**
```
frontend/.env
  └─ Add VITE_QUERY_TIMEOUT=45000
```

### Testing Checklist

**Local Testing (before deploy):**
1. Test cold start: restart backend, submit query, verify warmup works
2. Test warm query: second query should be < 5s
3. Test timeout: mock 60s delay, verify UI shows retry button
4. Test health checks: `curl /healthz` should be < 100ms

**Production Testing (after deploy):**
1. First query of day: expect 20-30s, should succeed
2. Follow-up query: expect < 5s
3. Check Fly logs: no health check timeouts
4. Monitor `/api/metrics` for failure rate

### Rollout Strategy

**Phase 1 (Week 1): Backend Reliability**
- Fix health checks (`/healthz` vs `/health/deep`)
- Add warmup endpoint (`/api/warmup`)
- Deploy and monitor for crashes

**Phase 2 (Week 2): Frontend UX**
- Add loading animations (Phases 1-4)
- Increase timeouts to 45s
- Add retry buttons

**Phase 3 (Week 3): Polish**
- Add Nobel facts/games during loading
- Fine-tune timing thresholds
- Archive redundant docs/code

---

## Success Metrics

**Before:**
- Query success rate: ~50%
- Response time: 13-39 seconds (unpredictable)
- User experience: Frustrating, feels broken
- Cost: ~$10-20/month

**After (Target):**
- Query success rate: 95%+
- First query: 20-30s with delightful UX
- Subsequent queries: < 5s
- User experience: Predictable, fun loading states
- Cost: ~$10-20/month (no increase)

---

## Non-Goals (Explicitly Out of Scope)

- ❌ Reduce cold start time to < 5s (would require keeping Modal warm = $$)
- ❌ Add caching layer (adds complexity, low ROI for side project)
- ❌ Switch to self-hosted embeddings (Phase 1 focus is stability, not architecture)
- ❌ Real-time progress updates via WebSocket (nice-to-have for Phase 4)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Modal still times out at 45s | Medium | High | Add manual retry button, show clear messaging |
| Warmup endpoint increases costs | Low | Medium | Monitor Fly metrics, warmup is single lightweight call |
| Users hate the loading games | Low | Low | A/B test, make it subtle/skippable |
| Health check changes break deployment | Medium | High | Test in staging, keep old /health for 1 week |

---

## Open Questions

1. **Loading animation style**: Playful vs professional? → User says playful is fine
2. **Retry strategy**: Auto-retry once or manual only? → Manual only (simpler)
3. **Remove FAISS from prod**: Safe to do? → Yes, if we validate Qdrant is stable

---

## Appendix: Alternative Approaches Considered

### A. Keep Modal Warm (Rejected - Too Expensive)
- Ping Modal every 5 minutes to prevent sleep
- Cost: ~$30-50/month extra
- Benefit: Sub-second cold starts
- **Why rejected**: Budget constraint (side project)

### B. Switch to Local FAISS (Deferred to Phase 4)
- Embed models in Fly.io machine
- Simpler architecture, lower cost
- Trade-off: Slower cold starts (model loading)
- **Why deferred**: Bigger refactor, want quick win first

### C. Add Redis Caching (Rejected - Over-Engineering)
- Cache query embeddings and results
- Benefit: Instant results for repeated queries
- **Why rejected**: Low ROI (most queries are unique), adds complexity

---

**Approved by**: Joe (User)
**Next Steps**: Set up git worktree, write detailed implementation plan
