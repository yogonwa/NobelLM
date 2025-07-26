# Umami Tracking Implementation

## Overview

NobelLM uses Umami for privacy-friendly analytics tracking. The implementation uses a combination of data attributes for simple events and JavaScript API calls for complex events.

## Tracking Methods

### 1. Data Attributes (Simple Events)

For basic user interactions, we use `data-umami-event` attributes:

```html
<!-- Query input focus -->
<input data-umami-event="Query input focused" />

<!-- Search button click -->
<button data-umami-event="Search button clicked">Search</button>

<!-- Suggestion click with metadata -->
<button 
  data-umami-event="Suggestion clicked"
  data-umami-event-index="0"
>
  Who won the Nobel Prize in Literature in 1965?
</button>

<!-- Navigation with page info -->
<NavLink 
  data-umami-event="Navigation"
  data-umami-event-page="about"
>
  About
</NavLink>
```

### 2. JavaScript API (Complex Events)

For events that need dynamic data or conditional logic:

```javascript
// Query success with timing and analysis
window.umami.track('Query success', {
  query_length: query.length,
  response_time: Date.now() - startTime,
  has_special_chars: /[!@#$%^&*]/.test(query),
  contains_quotes: /["']/.test(query)
});

// Query error with error details
window.umami.track('Query error', {
  query_length: query.length,
  error_type: 'api_error',
  error_message: error.message
});
```

## Events Tracked

### Query Events
- **Query submitted** - When user submits a query (data attribute)
- **Query success** - Successful query with timing and analysis (JavaScript)
- **Query error** - Failed query with error details (JavaScript)
- **Query input focused** - When user focuses on input field (data attribute)
- **Search button clicked** - When search button is clicked (data attribute)

### User Interaction Events
- **Suggestion clicked** - When user clicks a suggestion (data attribute)
- **Try again clicked** - When user clicks try again button (data attribute)
- **Navigation** - When user navigates between pages (data attribute)

### Event Data Limits
- Event names: max 50 characters
- Strings: max 500 characters
- Numbers: max 4 decimal precision
- Objects: max 50 properties

## Implementation Files

- `frontend/index.html` - Umami script tag
- `frontend/src/components/QueryInput.tsx` - Query input tracking
- `frontend/src/components/SuggestedPrompts.tsx` - Suggestion tracking
- `frontend/src/pages/Home.tsx` - Query success/error tracking
- `frontend/src/App.tsx` - Navigation tracking

## TypeScript Support

Global Umami declaration added to components:

```typescript
declare global {
  interface Window {
    umami?: {
      track: (eventName: string, data?: Record<string, any>) => void;
    };
  }
}
```

## Privacy

- No personally identifiable information tracked
- Query content not stored (only metadata)
- Anonymous tracking only
- GDPR compliant

## Dashboard Insights

Monitor these key metrics in your Umami dashboard:

1. **Query Performance**
   - Query submission rate
   - Success vs error rates
   - Average response times

2. **User Engagement**
   - Suggestion click rates
   - Navigation patterns
   - Input field engagement

3. **Error Analysis**
   - Error types and frequencies
   - User impact assessment

## Adding New Tracking

### Simple Events
Add data attributes to HTML elements:
```html
<button data-umami-event="My event" data-umami-event-property="value">
  Click me
</button>
```

### Complex Events
Use JavaScript API:
```javascript
if (window.umami) {
  window.umami.track('My event', { property: 'value' });
}
``` 