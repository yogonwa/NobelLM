# NobelLM Frontend

A modern React TypeScript application for exploring Nobel Prize laureate speeches and lectures through AI-powered search and discovery.

## Features

- **AI-Powered Search**: Query the extensive database of Nobel Prize speeches and lectures
- **Dual-State UX**: Elegant hero page transitions to comprehensive results view
- **Real-time API Integration**: Connected to NobelLM backend with comprehensive error handling
- **Responsive Design**: Mobile-first approach with smooth animations and transitions
- **Accessibility**: Built with accessibility best practices and keyboard navigation
- **Type Safety**: Full TypeScript implementation with proper interfaces

## Technology Stack

- **React 18.3.1** - Modern React with hooks
- **TypeScript 5.8.3** - Type-safe development
- **Vite 6.3.5** - Fast build tool and dev server
- **Tailwind CSS 3.4.1** - Utility-first CSS framework
- **Lucide React** - Beautiful, customizable icons
- **React Router DOM 7.6.2** - Client-side routing
- **Vitest** - Unit testing framework

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Lint code
npm run lint

# Format code
npm run format
```

### Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ErrorBoundary.tsx
│   ├── QueryInput.tsx
│   ├── ResponseDisplay.tsx
│   ├── SourceCitation.tsx
│   └── SuggestedPrompts.tsx
├── pages/              # Page components
│   └── Home.tsx
├── types/              # TypeScript type definitions
│   └── index.ts
├── utils/              # Utility functions
│   └── api.ts
├── test/               # Test setup and examples
├── App.tsx             # Main application component
├── main.tsx            # Application entry point
└── index.css           # Global styles and animations
```

## Architecture

### Component Design
- **Functional Components**: Modern React with hooks
- **TypeScript Interfaces**: Proper type definitions for all props
- **Error Boundaries**: Graceful error handling at component level
- **Loading States**: Comprehensive loading and error state management

### Styling Approach
- **Tailwind CSS**: Utility-first styling with custom components
- **Custom Animations**: CSS keyframes for smooth transitions
- **Responsive Design**: Mobile-first with proper breakpoints
- **Design System**: Consistent color scheme and typography

### State Management
- **Local State**: React hooks for component-level state
- **API Integration**: Real-time communication with NobelLM backend
- **Error Handling**: Comprehensive error states and retry mechanisms

## Testing

The application includes a comprehensive testing setup:

- **Vitest**: Fast unit testing framework
- **React Testing Library**: Component testing utilities
- **JS DOM**: Browser environment simulation
- **Coverage Reporting**: Test coverage analysis

## Deployment

The application is configured for production deployment with:

- **Vite Build**: Optimized production builds
- **Static Assets**: Proper asset handling and optimization
- **Environment Configuration**: Support for different deployment environments

### Production Deployment

The frontend is deployed on Fly.io:

```bash
# Deploy to production
fly deploy --config fly.toml
```

**Production URL**: [nobellm.com](https://nobellm.com)

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new features
3. Ensure TypeScript types are properly defined
4. Update documentation as needed

## License

Part of the NobelLM project - see main project LICENSE for details.
