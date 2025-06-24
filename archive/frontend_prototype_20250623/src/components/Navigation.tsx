import React from 'react';
import { NavLink } from 'react-router-dom';

const Navigation: React.FC = () => {
  return (
    <nav className="py-2">
      <div className="container mx-auto px-4 flex justify-end space-x-6">
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
    </nav>
  );
};

export default Navigation;