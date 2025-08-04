# Archive Directory

This directory contains archived code and assets that are no longer actively used in the NobelLM project.

## Archived Items

### `deployment_docs/`
**Archived on:** January 2025  
**Reason:** Redundant deployment documentation consolidated into single guide

**Contents:**
- `DEPLOYMENT_CHECKLIST.md` - Superseded by `PRODUCTION_DEPLOYMENT_GUIDE.md`
- `PRODUCTION_DEPLOYMENT_CHECKLIST.md` - Superseded by `PRODUCTION_DEPLOYMENT_GUIDE.md`

**Why archived:**
- `PRODUCTION_DEPLOYMENT_GUIDE.md` in root provides comprehensive deployment documentation
- These files contained redundant information and created maintenance overhead
- Single source of truth for deployment documentation is preferred

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

### `development_notes/`
**Archived on:** January 2025  
**Reason:** Development artifacts moved to archive for production readiness

**Contents:**
- `TASKS.md` - Development task list and execution plan
- `NOTES.md` - Design decisions and implementation notes
- `SPEC.md` - Original project specification
- `IMPLEMENTATION_PLAN.md` - Development implementation phases
- `META_ANALYSIS.md` - Development analysis and insights
- `Improve_Prompts.md` - Prompt engineering development work
- `gen_Audience_blog.md` - Blog content and audience analysis
- `ux_upgrade.md` - UX development notes and improvements
- `DOCUMENTATION_UPDATE_SUMMARY.md` - Documentation work tracking

**Why archived:**
- These files contain development history and planning artifacts
- Not needed for production deployment or user documentation
- Preserved for historical reference and development context

### `completed_phases/`
**Archived on:** January 2025  
**Reason:** Completed development phases and implementation notes

**Contents:**
- `PHASE3_TODO.md` - Completed thematic reformulation expansion
- `PHASE4_COMPLETED.md` - Completed retrieval logic enhancements
- `PHASE5_COMPLETED.md` - Completed thematic synthesis improvements
- `PHASE5_TODO.md` - Completed phase 5 implementation
- `RAG_Audit.md` - RAG pipeline audit and analysis
- `Dual_process_implementation.md` - FAISS dual-process implementation notes
- `GENERATIVE_EMOTIONAL_RETRIEVAL_PROJECT.md` - Research and development notes
- `MODAL_INTEGRATION_PLAN.md` - Completed Modal integration
- `MODAL_EMBEDDING_TEST_PLAN.md` - Completed Modal testing strategy
- `test_coverage_plan.md` - Completed test coverage implementation
- `refactor.md` - Modal embedder refactoring notes

**Why archived:**
- These represent completed development work and implementation phases
- Functionality is now integrated into the main codebase
- Preserved for development history and reference

### `legacy_docs/`
**Archived on:** January 2025  
**Reason:** Superseded documentation and legacy guides

**Contents:**
- `nobellm_fly_migration.md` - Completed migration documentation
- `PRODUCTION_DEPLOYMENT.md` - Superseded by main deployment guide
- `THEME_EMBEDDINGS.md` - Technical implementation documentation
- `FLY_DEPLOYMENT.md` - Superseded backend deployment guide
- `UMAMI_TRACKING.md` - Analytics setup documentation
- `README.md` - Legacy frontend documentation

**Why archived:**
- These documents have been superseded by updated, consolidated documentation
- Information is now covered in the main README and deployment guides
- Preserved for reference and migration history

## Archive Organization

The archive is organized into logical categories:

- **`development_notes/`** - Planning, specification, and development artifacts
- **`completed_phases/`** - Completed implementation phases and technical notes
- **`legacy_docs/`** - Superseded documentation and guides
- **`frontend_prototype_20250623/`** - Initial frontend prototype
- **`streamlit_legacy/`** - Original Streamlit implementation

## Accessing Archived Content

All archived content is preserved for historical reference and development context. The main project documentation is now consolidated in:

- **Main README.md** - Comprehensive project overview and setup
- **PRODUCTION_DEPLOYMENT_GUIDE.md** - Complete deployment instructions
- **Module-specific README files** - Detailed documentation for each component

**Note:** The main frontend in `/frontend/` and backend in `/backend/` are now the canonical implementations and should be used for all development. 