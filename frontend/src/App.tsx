import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Home from './pages/Home';
import About from './About';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <div className="container mx-auto px-4 py-4">
            <div className="flex justify-end space-x-6">
              <NavLink 
                to="/" 
                className={({ isActive }) => 
                  `text-gray-600 hover:text-amber-600 transition-colors ${isActive ? 'text-amber-600' : ''}`
                }
              >
                Home
              </NavLink>
              <NavLink 
                to="/about" 
                className={({ isActive }) => 
                  `text-gray-600 hover:text-amber-600 transition-colors ${isActive ? 'text-amber-600' : ''}`
                }
              >
                About
              </NavLink>
            </div>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/about" element={<About />} />
            </Routes>
            
            <footer className="text-center text-gray-500 text-sm py-8">
              <p>NobelLM &copy; 2025</p>
            </footer>
          </div>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
