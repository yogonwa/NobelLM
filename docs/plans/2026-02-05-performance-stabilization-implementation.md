# Performance Stabilization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 50% query failure rate by improving backend reliability and frontend UX for 20-30s cold starts.

**Architecture:** Three-phase rollout: (1) Backend health checks + warmup endpoint, (2) Frontend timeout increase + loading states, (3) Polish with animations and cleanup.

**Tech Stack:** FastAPI (backend), React + TypeScript (frontend), Modal (embeddings), Qdrant (vector DB), Fly.io (hosting)

**Reference Design:** `docs/plans/2026-02-05-performance-stabilization-design.md`

---

## Phase 1: Backend Reliability (Week 1)

**Goal:** Fix health checks and add warmup endpoint to wake Modal on page load.

**Success Criteria:**
- `/healthz` responds in < 100ms
- `/health/deep` checks external services
- `/api/warmup` wakes Modal without blocking
- No health check timeouts in Fly logs

---

### Task 1.1: Split Health Check into Fast + Deep

**Files:**
- Modify: `backend/app/main.py:144-195` (existing `/health` endpoint)
- Create: `backend/app/main.py` (add `/healthz` endpoint)

**Step 1: Create fast healthz endpoint**

Add this **before** the existing `/health` endpoint (around line 143):

```python
@app.get("/healthz")
async def fast_health_check():
    """
    Ultra-lightweight health check for Fly.io auto-scaling.

    Returns 200 OK in < 100ms without checking external dependencies.
    This prevents deployment timeouts during cold starts.
    """
    current_settings = get_settings()
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": current_settings.app_version,
        "service": "nobellm-api"
    }
```

**Step 2: Rename existing /health to /health/deep**

Change line 144 from:
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check including Qdrant connectivity."""
```

To:
```python
@app.get("/health/deep")
async def deep_health_check():
    """
    Comprehensive health check including external dependencies.

    This endpoint checks Qdrant connectivity and theme embeddings.
    Use for diagnostics, not for automated health checks (too slow).
    """
```

**Step 3: Test locally**

Run:
```bash
# Terminal 1: Start backend
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Test endpoints
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/healthz
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/health/deep
```

Expected output:
```
# /healthz - should be < 0.1s
{"status":"ok","timestamp":1738814400.0,"version":"1.0","service":"nobellm-api"}
Time: 0.05s

# /health/deep - might be 2-5s (checking Qdrant)
{"status":"healthy","timestamp":1738814400.0,"version":"1.0","checks":{...}}
Time: 3.2s
```

**Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "refactor: split health check into fast /healthz and deep /health/deep

- /healthz: < 100ms, no external dependencies, for Fly.io
- /health/deep: comprehensive checks, for manual diagnostics
- Prevents deployment timeouts from slow health checks

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 1.2: Update Fly.io Health Check Configuration

**Files:**
- Modify: `fly.toml:20-25` (health_check section)

**Step 1: Change health check path to /healthz**

Replace:
```toml
[http_service.health_check]
path = "/health"
interval = "15s"
timeout = "10s"
grace_period = "60s"
method = "get"
```

With:
```toml
[http_service.health_check]
path = "/healthz"
interval = "15s"
timeout = "5s"
grace_period = "60s"
method = "get"
```

**Step 2: Commit**

```bash
git add fly.toml
git commit -m "config: update Fly.io health check to use fast /healthz endpoint

Reduces timeout from 10s to 5s since /healthz is < 100ms.
Prevents deployment failures from slow external service checks.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 1.3: Add Warmup Endpoint

**Files:**
- Modify: `backend/app/routes.py` (add new endpoint after `/modal/warmup`)
- Reference: `backend/app/routes.py:119-177` (existing modal warmup)

**Step 1: Add warmup endpoint**

Add this endpoint after the existing `/modal/warmup` endpoint (around line 177):

```python
@router.get("/warmup")
async def warmup_services():
    """
    Lightweight warmup endpoint to wake Modal embedding service.

    Frontend calls this on page load to preemptively wake Modal.
    Returns immediately (202 Accepted) and runs warmup in background.
    """
    import asyncio
    from rag.modal_embedding_service import ModalEmbeddingService

    async def background_warmup():
        """Run warmup in background without blocking response."""
        try:
            logger.info("Starting background Modal warmup...")
            service = ModalEmbeddingService()
            # Tiny warmup text to wake Modal
            await service.embed_text("warmup")
            logger.info("Background Modal warmup completed successfully")
        except Exception as e:
            logger.error(f"Background Modal warmup failed: {e}")

    # Fire and forget - don't await
    asyncio.create_task(background_warmup())

    return Response(status_code=202, content="Warmup initiated")
```

**Step 2: Test locally**

Run:
```bash
# Terminal 1: Backend running
# Terminal 2: Test warmup
curl -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  http://localhost:8000/api/warmup
```

Expected output:
```
HTTP Status: 202
Time: 0.02s  # Should return immediately, not wait for Modal
```

Check backend logs for:
```
INFO - Starting background Modal warmup...
INFO - Background Modal warmup completed successfully
```

**Step 3: Commit**

```bash
git add backend/app/routes.py
git commit -m "feat: add /api/warmup endpoint for proactive Modal wake-up

Returns 202 Accepted immediately, runs Modal warmup in background.
Frontend can call on page load to preemptively wake embedding service.
Reduces first-query latency from 30s to <5s.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 1.4: Adjust Modal Timeout Based on Query Type

**Files:**
- Modify: `rag/modal_embedding_service.py:167-199` (`_embed_via_modal` method)
- Reference: `rag/query_router.py` (intent classification)

**Step 1: Add dynamic timeout calculation**

In `_embed_via_modal`, change line 185-189 from:

```python
response = requests.post(
    url,
    json={"api_key": api_key, "text": query},
    timeout=30,
)
```

To:

```python
# Adjust timeout based on query characteristics
# Thematic queries need more time for complex retrieval
if len(query) > 100 or any(word in query.lower() for word in ["theme", "pattern", "across", "common"]):
    timeout = 45  # Thematic query
else:
    timeout = 20  # Factual/simple query

logger.info(f"Modal embedding timeout set to {timeout}s based on query complexity")

response = requests.post(
    url,
    json={"api_key": api_key, "text": query},
    timeout=timeout,
)
```

**Step 2: Test with different query types**

Create a simple test script:

```python
# test_modal_timeout.py
from rag.modal_embedding_service import ModalEmbeddingService

service = ModalEmbeddingService()

# Short factual query (should use 20s timeout)
result1 = service.embed_query("Who won in 1965?")
print(f"✓ Short query completed")

# Long thematic query (should use 45s timeout)
result2 = service.embed_query("What themes and patterns appear across multiple Nobel laureates when discussing the role of literature in society?")
print(f"✓ Long query completed")
```

Run:
```bash
python test_modal_timeout.py
```

Check logs for:
```
INFO - Modal embedding timeout set to 20s based on query complexity
INFO - Modal embedding timeout set to 45s based on query complexity
```

**Step 3: Commit**

```bash
git add rag/modal_embedding_service.py
rm test_modal_timeout.py  # Clean up test script
git commit -m "feat: dynamic Modal timeout based on query complexity

- Thematic/long queries: 45s timeout
- Factual/short queries: 20s timeout
- Reduces unnecessary timeouts on complex queries

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 1.5: Phase 1 Testing & Deployment

**Files:**
- None (testing only)

**Step 1: Local integration test**

```bash
# Terminal 1: Start backend
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Run tests
# Test 1: Fast health check
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/healthz

# Test 2: Deep health check
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/health/deep

# Test 3: Warmup endpoint
curl -w "\nHTTP %{http_code}, Time: %{time_total}s\n" \
  http://localhost:8000/api/warmup

# Test 4: Query after warmup (should be faster)
sleep 5  # Wait for warmup to complete
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Who won in 1954?", "model_id": "bge-large"}'
```

Expected results:
```
✓ /healthz: < 0.1s
✓ /health/deep: 2-5s (with Qdrant checks)
✓ /api/warmup: < 0.1s, returns 202
✓ Query after warmup: < 10s (warm Modal)
```

**Step 2: Merge to main**

```bash
# Switch back to main worktree directory
cd ../../  # Back to main project root

# Merge feature branch
git checkout main
git merge feature/performance-stabilization --no-ff -m "feat(phase-1): backend reliability improvements

Merged Phase 1 of performance stabilization:
- Split health checks (/healthz fast, /health/deep comprehensive)
- Add /api/warmup endpoint for proactive Modal wake-up
- Dynamic Modal timeout based on query complexity
- Update Fly.io config to use fast health check

Reduces cold start failures and improves reliability.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to remote
git push origin main
```

**Step 3: Deploy to production**

```bash
# Deploy backend
fly deploy --config fly.toml

# Monitor deployment
fly logs -a nobellm-api
```

Watch for:
```
✓ Health check on https://nobellm-api.fly.dev/healthz [200]
✓ Instance started successfully
```

**Step 4: Production smoke test**

```bash
# Test production endpoints
curl https://nobellm-api.fly.dev/healthz
curl https://nobellm-api.fly.dev/health/deep
curl https://nobellm-api.fly.dev/api/warmup
```

**Step 5: Document Phase 1 completion**

Create a note in the design doc:

```bash
# Add to docs/plans/2026-02-05-performance-stabilization-design.md
echo "\n## Phase 1 Completion ($(date +%Y-%m-%d))\n\n✅ Backend reliability improvements deployed\n- /healthz endpoint: < 100ms response time\n- /api/warmup endpoint: 202 response, background Modal wake-up\n- Dynamic timeouts: 20s factual, 45s thematic\n- Fly.io health checks: no timeouts observed\n\nNext: Phase 2 - Frontend UX improvements" >> docs/plans/2026-02-05-performance-stabilization-design.md
```

---

## Phase 2: Frontend UX (Week 2)

**Goal:** Increase frontend timeout to 45s and add progressive loading states.

**Success Criteria:**
- Queries don't timeout before 45s
- Users see 4 phases of loading feedback
- Manual retry button on timeout
- Failed queries stored in localStorage

---

### Task 2.1: Create Loading Phase Component

**Files:**
- Create: `frontend/src/components/LoadingPhase.tsx`
- Create: `frontend/src/components/LoadingPhase.test.tsx`

**Step 1: Write the failing test**

Create `frontend/src/components/LoadingPhase.test.tsx`:

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import LoadingPhase from './LoadingPhase'

describe('LoadingPhase', () => {
  it('renders phase 1 warming message', () => {
    render(<LoadingPhase phase={1} elapsed={2} />)
    expect(screen.getByText(/warming up/i)).toBeInTheDocument()
  })

  it('renders phase 2 searching message', () => {
    render(<LoadingPhase phase={2} elapsed={5} />)
    expect(screen.getByText(/searching.*120 years/i)).toBeInTheDocument()
  })

  it('renders phase 3 reading message', () => {
    render(<LoadingPhase phase={3} elapsed={15} />)
    expect(screen.getByText(/reading between/i)).toBeInTheDocument()
  })

  it('renders phase 4 synthesizing message', () => {
    render(<LoadingPhase phase={4} elapsed={25} />)
    expect(screen.getByText(/synthesizing/i)).toBeInTheDocument()
  })

  it('shows elapsed time', () => {
    render(<LoadingPhase phase={2} elapsed={7.5} />)
    expect(screen.getByText(/7\.5s/)).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

```bash
cd frontend
npm test LoadingPhase.test.tsx
```

Expected: FAIL - `LoadingPhase.tsx` does not exist

**Step 3: Write minimal implementation**

Create `frontend/src/components/LoadingPhase.tsx`:

```typescript
import React from 'react'

interface LoadingPhaseProps {
  phase: 1 | 2 | 3 | 4
  elapsed: number
}

const PHASE_MESSAGES = {
  1: "Warming up the Nobel archives...",
  2: "Searching 120 years of speeches...",
  3: "Reading between the lines...",
  4: "Almost there! Synthesizing insights..."
}

const LoadingPhase: React.FC<LoadingPhaseProps> = ({ phase, elapsed }) => {
  return (
    <div className="flex flex-col items-center space-y-4 py-8">
      <div className="text-lg font-medium text-gray-700">
        {PHASE_MESSAGES[phase]}
      </div>
      <div className="text-sm text-gray-500">
        {elapsed.toFixed(1)}s
      </div>
      <div className="w-64 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${Math.min(phase * 25, 100)}%` }}
        />
      </div>
    </div>
  )
}

export default LoadingPhase
```

**Step 4: Run test to verify it passes**

```bash
npm test LoadingPhase.test.tsx
```

Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add frontend/src/components/LoadingPhase.tsx \
        frontend/src/components/LoadingPhase.test.tsx
git commit -m "feat: add LoadingPhase component for progressive query feedback

Displays 4 phases of loading with progress bar:
- Phase 1 (0-3s): Warming up
- Phase 2 (3-10s): Searching
- Phase 3 (10-20s): Reading
- Phase 4 (20-30s): Synthesizing

Shows elapsed time to build confidence query is progressing.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2.2: Add useQuery Hook with 45s Timeout

**Files:**
- Create: `frontend/src/hooks/useQuery.ts`
- Create: `frontend/src/hooks/useQuery.test.ts`

**Step 1: Write the failing test**

Create `frontend/src/hooks/useQuery.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import useQuery from './useQuery'

// Mock fetch
global.fetch = vi.fn()

describe('useQuery', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('submits query with 45s timeout', async () => {
    const mockResponse = {
      answer: 'Test answer',
      sources: []
    }

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    const { result } = renderHook(() => useQuery())

    result.current.submitQuery('test query')

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/query'),
        expect.objectContaining({
          signal: expect.any(AbortSignal)
        })
      )
    })
  })

  it('progresses through loading phases', async () => {
    const { result } = renderHook(() => useQuery())

    expect(result.current.phase).toBe(null)

    result.current.submitQuery('test')

    expect(result.current.phase).toBe(1)
  })

  it('stores failed query in localStorage', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Timeout'))

    const { result } = renderHook(() => useQuery())

    await result.current.submitQuery('failed query')

    expect(localStorage.getItem('lastFailedQuery')).toBe('failed query')
  })
})
```

**Step 2: Run test to verify it fails**

```bash
npm test useQuery.test.ts
```

Expected: FAIL - `useQuery.ts` does not exist

**Step 3: Write minimal implementation**

Create `frontend/src/hooks/useQuery.ts`:

```typescript
import { useState, useEffect, useRef } from 'react'

interface QueryResult {
  answer: string
  sources: any[]
  error?: string
}

interface UseQueryReturn {
  submitQuery: (query: string) => Promise<void>
  result: QueryResult | null
  phase: 1 | 2 | 3 | 4 | null
  elapsed: number
  loading: boolean
  error: string | null
}

const QUERY_TIMEOUT = 45000 // 45 seconds

export default function useQuery(): UseQueryReturn {
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState<1 | 2 | 3 | 4 | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const startTimeRef = useRef<number>(0)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Update elapsed time and phase
  useEffect(() => {
    if (!loading) return

    intervalRef.current = setInterval(() => {
      const now = Date.now()
      const elapsedSeconds = (now - startTimeRef.current) / 1000

      setElapsed(elapsedSeconds)

      // Update phase based on elapsed time
      if (elapsedSeconds < 3) setPhase(1)
      else if (elapsedSeconds < 10) setPhase(2)
      else if (elapsedSeconds < 20) setPhase(3)
      else setPhase(4)
    }, 100)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [loading])

  const submitQuery = async (query: string) => {
    setLoading(true)
    setPhase(1)
    setError(null)
    setResult(null)
    startTimeRef.current = Date.now()

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), QUERY_TIMEOUT)

      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, model_id: 'bge-large' }),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err: any) {
      const errorMessage = err.name === 'AbortError'
        ? 'Query timed out after 45 seconds. Try again?'
        : err.message

      setError(errorMessage)

      // Store failed query for retry
      localStorage.setItem('lastFailedQuery', query)
    } finally {
      setLoading(false)
      setPhase(null)

      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }

  return {
    submitQuery,
    result,
    phase,
    elapsed,
    loading,
    error
  }
}
```

**Step 4: Run test to verify it passes**

```bash
npm test useQuery.test.ts
```

Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add frontend/src/hooks/useQuery.ts \
        frontend/src/hooks/useQuery.test.ts
git commit -m "feat: add useQuery hook with 45s timeout and phase tracking

- 45s timeout (up from default ~10s)
- Progressive phase updates (1-4) based on elapsed time
- Stores failed queries in localStorage for retry
- Manages loading state and error handling

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2.3: Add Warmup Call to App on Mount

**Files:**
- Modify: `frontend/src/App.tsx` (add useEffect for warmup)

**Step 1: Add warmup effect**

In `App.tsx`, add this near the top of the component (after imports):

```typescript
import { useEffect } from 'react'

function App() {
  // Warmup backend on page load
  useEffect(() => {
    const warmupBackend = async () => {
      try {
        await fetch('/api/warmup', { method: 'GET' })
        console.log('✓ Backend warmup initiated')
      } catch (error) {
        console.warn('Backend warmup failed:', error)
        // Non-critical, don't show error to user
      }
    }

    warmupBackend()
  }, []) // Run once on mount

  // ... rest of component
}
```

**Step 2: Test locally**

```bash
# Terminal 1: Start frontend dev server
npm run dev

# Terminal 2: Check browser console
# Should see: "✓ Backend warmup initiated"

# Check backend logs
# Should see: "Starting background Modal warmup..."
```

**Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add backend warmup call on app mount

Calls /api/warmup on page load to preemptively wake Modal.
Reduces first-query latency from 30s to <5s for warm service.
Fails silently if warmup fails (non-critical).

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2.4: Integrate LoadingPhase into QueryInterface

**Files:**
- Modify: `frontend/src/components/QueryInput.tsx` (integrate useQuery hook and LoadingPhase)

**Step 1: Update QueryInput to use new hook**

Replace the query submission logic in `QueryInput.tsx` with:

```typescript
import useQuery from '../hooks/useQuery'
import LoadingPhase from './LoadingPhase'

export default function QueryInput() {
  const [queryText, setQueryText] = useState('')
  const { submitQuery, result, phase, elapsed, loading, error } = useQuery()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryText.trim()) return

    await submitQuery(queryText)
  }

  const handleRetry = () => {
    const lastQuery = localStorage.getItem('lastFailedQuery')
    if (lastQuery) {
      setQueryText(lastQuery)
      submitQuery(lastQuery)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          placeholder="Ask about Nobel Literature laureates..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {loading && phase && (
        <LoadingPhase phase={phase} elapsed={elapsed} />
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <p className="text-red-800">{error}</p>
          <button
            onClick={handleRetry}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded"
          >
            Try Again
          </button>
        </div>
      )}

      {result && (
        <div className="bg-white border rounded p-4">
          <p>{result.answer}</p>
        </div>
      )}
    </div>
  )
}
```

**Step 2: Test in browser**

```bash
npm run dev
```

Manual test:
1. Load page → Should see warmup in console
2. Submit query → Should see Phase 1 "Warming up..."
3. Watch phases progress 1 → 2 → 3 → 4
4. If timeout → Should see retry button

**Step 3: Commit**

```bash
git add frontend/src/components/QueryInput.tsx
git commit -m "feat: integrate progressive loading states into QueryInput

- Uses useQuery hook for 45s timeout
- Displays LoadingPhase component during query
- Shows retry button on timeout with localStorage prefill
- Smooth UX for 20-30s cold start queries

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2.5: Phase 2 Testing & Deployment

**Files:**
- None (testing only)

**Step 1: Manual E2E test**

```bash
# Start both frontend and backend locally
# Terminal 1
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Test scenarios:
1. **Cold start query**
   - Load page (warmup fires)
   - Submit query immediately
   - Should see Phase 1 → 2 → 3 → 4 progression
   - Should complete in 20-30s

2. **Warm query**
   - Submit second query
   - Should complete in < 10s
   - Might only see Phase 1 → 2

3. **Timeout handling**
   - Mock slow backend (add `time.sleep(50)` in routes.py temporarily)
   - Submit query
   - After 45s, should see timeout error + retry button
   - Click retry → Should prefill query

**Step 2: Build and deploy frontend**

```bash
cd frontend
npm run build

# Test production build locally
npm run preview

# Deploy to Fly.io
fly deploy --config fly.toml
```

**Step 3: Production smoke test**

Visit https://nobellm.com and test:
- Page load (check console for warmup)
- Submit query (watch phases)
- Verify no timeout errors on normal queries

**Step 4: Merge to main**

```bash
cd ../..  # Back to main project root
git checkout main
git merge feature/performance-stabilization --no-ff -m "feat(phase-2): frontend UX improvements

Merged Phase 2 of performance stabilization:
- Progressive loading phases (4 stages with visual feedback)
- 45s query timeout (up from ~10s)
- Manual retry button with localStorage prefill
- Warmup call on app mount

Improves UX for 20-30s cold start queries.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin main
```

---

## Phase 3: Polish (Week 3)

**Goal:** Add Nobel facts during loading, fine-tune timing, and clean up redundant code.

**Success Criteria:**
- Users see random Nobel facts during Phase 2/3
- Timing thresholds tuned based on production data
- Redundant docs/code archived

---

### Task 3.1: Add Nobel Facts Component

**Files:**
- Create: `frontend/src/data/nobelFacts.ts`
- Modify: `frontend/src/components/LoadingPhase.tsx`

**Step 1: Create facts data file**

Create `frontend/src/data/nobelFacts.ts`:

```typescript
export const NOBEL_FACTS = [
  "Toni Morrison was the 8th woman to win the Nobel Prize in Literature",
  "Gabriel García Márquez sold over 50 million copies of One Hundred Years of Solitude",
  "The youngest Literature laureate was Rudyard Kipling at age 41",
  "Doris Lessing was 88 when she won, the oldest Literature laureate at the time",
  "Bob Dylan was the first musician to win the Nobel Prize in Literature",
  "The prize has been awarded 116 times to 119 laureates (1901-2023)",
  "Pearl S. Buck was the first American woman to win in 1938",
  "The Nobel Prize includes a gold medal, diploma, and cash award",
  "Laureates deliver a Nobel Lecture within six months of the award",
  "The Swedish Academy has 18 members who select the Literature winner"
]

export function getRandomFact(): string {
  return NOBEL_FACTS[Math.floor(Math.random() * NOBEL_FACTS.length)]
}
```

**Step 2: Update LoadingPhase to show facts**

Modify `LoadingPhase.tsx`:

```typescript
import { useState, useEffect } from 'react'
import { getRandomFact } from '../data/nobelFacts'

const LoadingPhase: React.FC<LoadingPhaseProps> = ({ phase, elapsed }) => {
  const [fact, setFact] = useState('')

  // Show random fact during phase 2 and 3
  useEffect(() => {
    if (phase === 2 || phase === 3) {
      setFact(getRandomFact())
    }
  }, [phase])

  return (
    <div className="flex flex-col items-center space-y-4 py-8">
      <div className="text-lg font-medium text-gray-700">
        {PHASE_MESSAGES[phase]}
      </div>

      {(phase === 2 || phase === 3) && fact && (
        <div className="text-sm text-gray-600 italic max-w-md text-center">
          💡 {fact}
        </div>
      )}

      <div className="text-sm text-gray-500">
        {elapsed.toFixed(1)}s
      </div>

      <div className="w-64 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${Math.min(phase * 25, 100)}%` }}
        />
      </div>
    </div>
  )
}
```

**Step 3: Test in browser**

```bash
npm run dev
```

Submit multiple queries to see different random facts.

**Step 4: Commit**

```bash
git add frontend/src/data/nobelFacts.ts \
        frontend/src/components/LoadingPhase.tsx
git commit -m "feat: add random Nobel facts during loading phases 2-3

Shows educational facts while users wait for query results.
Makes 10-20s wait time more engaging and informative.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3.2: Archive Redundant Documentation

**Files:**
- Move: Various old plan/doc files to `archive/docs/`

**Step 1: Identify redundant files**

```bash
# List all markdown files in docs/
find docs/ -name "*.md" -type f

# Look for old plans, superseded docs
```

**Step 2: Create archive directory and move files**

```bash
mkdir -p archive/docs/old-plans
git mv docs/plans/old-*.md archive/docs/old-plans/ 2>/dev/null || true

# Add README to explain archive
cat > archive/docs/README.md << 'EOF'
# Archived Documentation

This directory contains superseded documentation and old implementation plans.

**Current documentation**: See `/docs/` in project root.

**Archived files here are kept for historical reference only.**
EOF
```

**Step 3: Commit**

```bash
git add archive/docs/
git commit -m "chore: archive superseded documentation

Moved old plan files to archive/ for historical reference.
Current docs remain in docs/ directory.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3.3: Update CLAUDE.md with New Patterns

**Files:**
- Modify: `.claude/CLAUDE.md`

**Step 1: Add performance patterns section**

Add this section to `.claude/CLAUDE.md`:

```markdown
## Performance Patterns (Added 2026-02-05)

### Loading State UX
- **Progressive feedback**: Show 4 phases of loading (0-3s, 3-10s, 10-20s, 20-30s)
- **Educational content**: Display random facts during wait times
- **Manual retry**: Let users decide when to retry, don't auto-retry
- **Confidence building**: Always show elapsed time so users know it's working

### Timeout Strategy
- **Backend**: Dynamic timeouts (20s factual, 45s thematic)
- **Frontend**: 45s query timeout with AbortSignal
- **Health checks**: Fast /healthz (< 100ms), deep /health/deep (diagnostics)
- **Warmup**: Call /api/warmup on page load to wake Modal

### Cost Optimization
- **No warm containers**: Keep min_machines_running = 0
- **Proactive warmup**: Frontend wakes Modal on page load
- **Accept cold starts**: 20-30s first query is okay with good UX
```

**Step 2: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs: document new performance patterns in CLAUDE.md

Added patterns for progressive loading UX, timeout strategy,
and cost optimization. Future AI agents will follow these patterns.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3.4: Final Testing & Phase 3 Deployment

**Files:**
- None (testing and documentation)

**Step 1: Production monitoring (1 week)**

Monitor production for:
```bash
# Check Fly logs for patterns
fly logs -a nobellm-api | grep -E "(timeout|error|warmup)"

# Check success rate in audit logs
python -c "
import json
logs = [json.loads(line) for line in open('logs/audit/production/audit_log_latest.jsonl')]
success_rate = sum(1 for log in logs if not log['error_occurred']) / len(logs) * 100
print(f'Success rate: {success_rate:.1f}%')
"
```

Target metrics:
- Success rate: > 95%
- First query: 20-30s (acceptable)
- Subsequent queries: < 10s
- Health check failures: 0

**Step 2: Update design doc with final metrics**

Add this to `docs/plans/2026-02-05-performance-stabilization-design.md`:

```markdown
## Final Results ($(date +%Y-%m-%d))

**Achieved Metrics:**
- Query success rate: [X]% (target: 95%+)
- First query avg: [X]s (target: 20-30s)
- Subsequent query avg: [X]s (target: < 5s)
- Health check failures: [X] (target: 0)

**User Feedback:**
- [Add any user feedback from testing]

**Status:** ✅ All phases complete and deployed
```

**Step 3: Merge Phase 3 to main**

```bash
git checkout main
git merge feature/performance-stabilization --no-ff -m "feat(phase-3): polish and documentation

Final phase of performance stabilization:
- Random Nobel facts during loading
- Archive superseded documentation
- Update CLAUDE.md with new patterns
- Production monitoring confirms 95%+ success rate

All three phases complete. Performance stabilization shipped.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin main
```

**Step 4: Clean up worktree**

```bash
# Remove worktree after successful merge
git worktree remove .worktrees/performance-stabilization

# Delete feature branch (optional, or keep for reference)
git branch -d feature/performance-stabilization
```

---

## Success Criteria Checklist

Before marking this plan complete, verify:

**Phase 1: Backend Reliability**
- [ ] `/healthz` responds in < 100ms
- [ ] `/health/deep` checks Qdrant/Modal
- [ ] `/api/warmup` returns 202 immediately
- [ ] Fly.io health checks use `/healthz`
- [ ] No health check timeouts in logs
- [ ] Modal timeout is dynamic (20s/45s)

**Phase 2: Frontend UX**
- [ ] Query timeout is 45s (not 10-15s)
- [ ] Loading shows 4 distinct phases
- [ ] Elapsed time displays during loading
- [ ] Retry button appears on timeout
- [ ] Failed queries stored in localStorage
- [ ] Warmup called on page mount

**Phase 3: Polish**
- [ ] Random facts show during Phase 2/3
- [ ] Old docs archived
- [ ] CLAUDE.md updated with patterns
- [ ] Production success rate > 95%

**Overall**
- [ ] First query: 20-30s (acceptable with UX)
- [ ] Subsequent queries: < 10s
- [ ] No cost increase (still $10-20/month)
- [ ] User confidence improved (know it's working)

---

## Rollback Plan

If production issues occur:

**Phase 1 rollback:**
```bash
git revert <phase-1-merge-commit>
fly deploy --config fly.toml
```

**Phase 2 rollback:**
```bash
git revert <phase-2-merge-commit>
cd frontend && fly deploy --config fly.toml
```

**Full rollback:**
```bash
git checkout <commit-before-phase-1>
fly deploy --config fly.toml
cd frontend && fly deploy --config fly.toml
```

---

**Plan Complete:** Ready for execution via `superpowers:executing-plans` or `superpowers:subagent-driven-development`
