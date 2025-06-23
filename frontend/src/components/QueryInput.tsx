import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  initialValue?: string;
  compact?: boolean;
}

const QueryInput: React.FC<QueryInputProps> = ({ 
  onSubmit, 
  isLoading, 
  initialValue = '', 
  compact = false 
}) => {
  const [query, setQuery] = useState(initialValue);
  const [showEmptyError, setShowEmptyError] = useState(false);

  useEffect(() => {
    setQuery(initialValue);
  }, [initialValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setShowEmptyError(true);
      setTimeout(() => setShowEmptyError(false), 3000);
      return;
    }
    setShowEmptyError(false);
    onSubmit(query);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (showEmptyError && e.target.value.trim()) {
      setShowEmptyError(false);
    }
  };

  const inputClasses = compact 
    ? `w-full py-2 px-4 pr-12 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all text-sm hover:border-gray-400 ${showEmptyError ? 'border-red-300 focus:ring-red-500' : 'border-gray-300'}`
    : `w-full py-3 px-4 pr-12 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all hover:border-gray-400 ${showEmptyError ? 'border-red-300 focus:ring-red-500' : 'border-gray-300'}`;

  const containerClasses = compact 
    ? "w-full"
    : "w-full max-w-3xl mx-auto mb-8";

  return (
    <form onSubmit={handleSubmit} className={containerClasses}>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          placeholder="Ask a question about Nobel laureate speeches..."
          className={inputClasses}
          disabled={isLoading}
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-md text-gray-500 hover:text-amber-600 transition-all disabled:opacity-50 hover:bg-amber-50"
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <div className="h-4 w-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <Search className="h-4 w-4" />
          )}
        </button>
      </div>
      {showEmptyError && (
        <p className="text-red-500 text-sm mt-2 animate-fade-in">
          Please enter a question to search.
        </p>
      )}
    </form>
  );
};

export default QueryInput; 