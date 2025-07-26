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