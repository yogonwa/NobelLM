# UX Upgrade: Cold Start Experience Improvements for NobelLM

## Overview

This spec outlines user experience enhancements to handle cold-start delays caused by backend and Modal microservice startup times. The goal is to turn latency into personality, reduce query failure rates, and provide users with clear, enjoyable feedback.

---

## ⚠️ Problem

First user query often fails or times out due to:
- Fly.io machines scaling from zero
- Modal microservice loading the embedding model
- Backend initialization lag

This results in frustrating first impressions or empty/error responses.

---

## ✅ Solution Summary

| Feature                  | Description                                                  | Benefit                            |
|--------------------------|--------------------------------------------------------------|-------------------------------------|
| 🍞 Preheat the Ovens     | Fun user-triggered warm-up button                            | Proactively warms backend + Modal   |
| ⏳ Smart Retry Logic     | Automatic retry after failure or extended backend timeout     | Increases query success rate        |
| 📚 Loading Trivia        | Fun laureate facts, quotes, or literary one-liners           | Distracts and adds personality      |
| 🚫 Retry Feedback Modal  | Friendly retry screen if first query fails                   | Prevents blank/error state confusion|

---

## 🍞 Feature 1: “Preheat the Ovens” Button

### Idea
A whimsical button that calls Fly + Modal `/ping` endpoints to warm the services before the first real query.

### UX Copy
> “Preheat the NobelLM ovens 🍞 — we’re warming up the literary engines!”

### Action
- Add a button that triggers:
  1. `GET /api/ping` (Fly backend)
  2. `GET /modal/warmup` (lightweight Modal call like `embed("hello")`)
- Shows playful spinner or “warming…” animation
- Then unlocks the full query UI

### How to Test
- Simulate a cold start by scaling app to 0
- Use dev tools to watch for ping requests
- Query immediately after preheat → should succeed

### Benefit
- Reduces frustration from cold-start failures
- Gives users a sense of agency and delight

---

## ⏳ Feature 2: Smart Retry Logic

### Idea
Gracefully handle backend timeouts or cold responses by retrying with context.

### Action
- On 502, 504, or timeout from `/api/query`:
  - Wait 2s, show message:
    > _“Warming up the Nobel brain 🧠... trying again...”_
  - Retry once automatically
  - If retry also fails, show retry modal (see below)

### How to Test
- Cold start app
- Submit query
- Confirm retry triggers before user sees failure

### Benefit
- Improves perceived stability
- Prevents unnecessary user friction

---

## 📚 Feature 3: Loading Trivia

### Idea
Instead of a blank spinner, show rotating trivia or quotes while waiting.

### Action
- Create `loading_quotes.json` with 10–20 entries:
  ```json
  [
    "Toni Morrison won the Nobel in 1993 — the first Black woman to do so.",
    "“All art is a kind of confession.” – Camus",
    "Sartre refused his Nobel Prize in 1964.",
    "Embedding poetic truth… Please stand by 🧠"
  ]
On query start, show one quote randomly

Keep visible until results are returned

How to Test
Submit query in dev

Verify a quote loads every time, never repeats immediately

Benefit
Makes loading feel intentional

Adds personality and Nobel context

🚫 Feature 4: Retry Feedback Modal
Idea
If first query fails even after retry, show a friendly, human message with retry action.

UX Copy
“We’re still waking up… try that again in just a moment!”

Add button:

🔁 “Try again”
☕️ “Or come back later — we’ll still be smart then.”

Action
Catch 2x failed queries

Show modal with retry/exit options

How to Test
Force a failure with timeout or disable API temporarily

Confirm fallback modal appears with retry

Benefit
Prevents blank page or unhelpful error text

Reinforces trust and user comfort

Deferred / Not Implemented
❌ Keep Modal Warm with pings (excluded due to cost)


----
implementationm details
🧊 Cold Start UX — Cursor Handoff
✅ Goal
Improve first-load experience by displaying a “Cold Start” warning when services have not yet been warmed up, and offer a “Preheat the Ovens” button to trigger manual warm-up.

🧩 Components Involved
Home.tsx (main page layout)

utils/api.ts (contains warmUpServices)

🆕 Add new component: components/ColdStartBanner.tsx

1. ➕ Create ColdStartBanner.tsx
Location: components/ColdStartBanner.tsx

tsx
Copy
Edit
import { Flame, Info } from 'lucide-react';

type Props = {
  onPreheat: () => void;
  servicesWarmed: boolean;
};

const ColdStartBanner: React.FC<Props> = ({ onPreheat, servicesWarmed }) => {
  if (servicesWarmed) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 text-sm text-gray-700 rounded-xl px-4 py-3 flex items-center justify-between gap-4 mt-4 shadow-sm animate-fade-in">
      <div className="flex items-start gap-2">
        <Info className="w-4 h-4 text-blue-500 mt-1" />
        <div>
          <div className="font-semibold text-blue-700">Cold Start</div>
          <p className="text-sm text-gray-600">Systems are cold, first query may take longer</p>
        </div>
      </div>
      <button
        onClick={onPreheat}
        className="flex items-center gap-1 bg-orange-100 hover:bg-orange-200 text-orange-800 px-3 py-1.5 text-sm rounded-lg font-medium transition"
      >
        <Flame className="w-4 h-4" />
        Preheat the Ovens
      </button>
    </div>
  );
};

export default ColdStartBanner;
2. 🏠 Integrate into Home.tsx
Import the component at the top:

tsx
Copy
Edit
import ColdStartBanner from '../components/ColdStartBanner';
Then, insert this into the initial layout (just after <QueryInput />):

tsx
Copy
Edit
<ColdStartBanner 
  servicesWarmed={servicesWarmed}
  onPreheat={async () => {
    const result = await warmUpServices();
    setServicesWarmed(result.backend || result.modal);
  }}
/>
3. 🧠 Optional Enhancements (If Time)
Track button click in Umami:

tsx
Copy
Edit
if (window.umami) {
  window.umami.track('Preheat ovens clicked');
}
Add animation delay if needed (match hero layout timing)

Could auto-dismiss banner after 5–8 seconds if desired

✅ Acceptance Criteria
Banner only shows if servicesWarmed === false

Clicking "Preheat the Ovens" triggers warm-up + hides banner

No disruption to query flow or suggested prompts

Let me know if you want to wire this up to a toast message, progress indicator, or log any warm-up failures visually.