# Archive Directory

This directory contains archived code and assets that are no longer actively used in the NobelLM project.

## Archived Items

### `frontend_prototype_20250623/`
**Archived on:** June 23, 2025  
**Reason:** Superseded by the main frontend implementation

**What it was:**
- Initial React TypeScript prototype for the NobelLM frontend
- Basic implementation with mock data and simple UX
- Used React 18.3.1 with minimal tooling

**Why it was archived:**
- The main `frontend/` directory has evolved into a production-ready application
- Main frontend includes:
  - React 19.1.0 with modern tooling
  - Real API integration with comprehensive error handling
  - Advanced UX with dual-state design and smooth animations
  - Comprehensive testing setup with Vitest
  - Enhanced styling with custom CSS animations
  - Error boundaries and proper TypeScript implementation

**Key differences:**
- **Architecture:** Prototype used mock data, main frontend has real API integration
- **UX:** Prototype had basic single-state design, main frontend has sophisticated dual-state layout
- **Code Quality:** Main frontend includes proper error handling, testing, and modern React patterns
- **Styling:** Prototype used basic Tailwind, main frontend has custom animations and comprehensive styling

### `streamlit_legacy/`
**Archived on:** January 2025  
**Reason:** Migrated to React TypeScript frontend with FastAPI backend

**What it was:**
- Original Streamlit-based frontend for NobelLM
- Deployed on Hugging Face Spaces
- Monolithic app with embedded RAG pipeline
- Basic UI with query input and response display

**Why it was archived:**
- Project migrated to modern React TypeScript frontend
- Backend separated into dedicated FastAPI service
- Deployed on Fly.io for better performance and control
- Improved architecture with separation of concerns

**Key differences:**
- **Architecture:** Streamlit was monolithic, new system has separate frontend/backend
- **Deployment:** Hugging Face Spaces → Fly.io
- **Technology:** Streamlit → React + TypeScript + FastAPI
- **Performance:** Better scalability and user experience
- **Development:** More maintainable and extensible codebase

**Note:** The main frontend in `/frontend/` and backend in `/backend/` are now the canonical implementations and should be used for all development. 