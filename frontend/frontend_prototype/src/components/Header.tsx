import React from 'react';
import { BookOpen } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="text-center py-6 border-b border-gray-200">
      <div className="flex items-center justify-center gap-3 mb-2">
        <BookOpen className="h-8 w-8 text-amber-500" />
        <h1 className="text-3xl font-bold text-gray-800">Explore Nobel Prize Speeches</h1>
      </div>
      <p className="text-gray-600 max-w-2xl mx-auto">
        Ask questions and discover insights from over a century of Nobel Prize acceptance speeches
      </p>
    </header>
  );
};

export default Header;