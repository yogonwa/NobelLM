# Nobel Laureate Speech Explorer – Frontend

This directory contains the Streamlit web UI for querying and exploring Nobel Prize laureate speeches and metadata.

## How to Launch

From the project root, run:

```bash
streamlit run frontend/app.py
```

- The app will open in your browser at http://localhost:8501
- No manual path adjustments are needed; all scripts are runnable from the project root.

## UI Features

- **Query Input:**
  - Enter your question in the input box and press Enter or click the search button.
  - Example: "What do laureates say about justice?"
- **Example Prompts:**
  - When no results are shown, you can click a prebuilt template button to auto-fill and run a sample query.
- **Results Display:**
  - The answer is shown at the top.
  - Below, each source card displays:
    - Year and laureate name
    - Source type (Lecture, Ceremony, Speech) as a chip
    - A snippet of the retrieved text
- **Try Again:**
  - Click "Try Again" to clear results and ask a new question.
- **Navigation:**
  - Top-right links for Home and About pages
  - Sidebar is collapsed by default for a minimalist look

## Notes
- The UI is minimalist and focused on search and exploration.
- All state is managed via Streamlit's session state for a smooth user experience.
- For more details on the backend and data pipeline, see the project root README and the `/rag` and `/scraper` directories.

---

_Last updated: June 2025_
