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

  useEffect(() => {
    setQuery(initialValue);
  }, [initialValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query);
    }
  };

  const inputClasses = compact 
    ? "w-full py-2 px-4 pr-12 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all text-sm"
    : "w-full py-3 px-4 pr-12 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all";

  const containerClasses = compact 
    ? "w-full"
    : "w-full max-w-3xl mx-auto mb-8";

  return (
    <form onSubmit={handleSubmit} className={containerClasses}>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about Nobel laureate speeches..."
          className={inputClasses}
          disabled={isLoading}
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-md text-gray-500 hover:text-amber-600 transition-colors disabled:opacity-50"
          disabled={isLoading || !query.trim()}
        >
          <Search className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
};

export default QueryInput;