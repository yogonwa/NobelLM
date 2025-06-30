// Handle www redirect before app loads
if (window.location.hostname === 'www.nobellm.com') {
  window.location.href = window.location.href.replace('www.', '');
}

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
