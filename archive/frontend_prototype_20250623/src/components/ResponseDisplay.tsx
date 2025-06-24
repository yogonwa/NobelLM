import React from 'react';
import { Loader2 } from 'lucide-react';
import { QueryResponse } from '../types';

interface ResponseDisplayProps {
  response: QueryResponse | null;
  isLoading: boolean;
}

const ResponseDisplay: React.FC<ResponseDisplayProps> = ({ response, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-8 w-8 text-amber-500 animate-spin mb-4" />
        <p className="text-gray-600">Searching through Nobel laureate speeches...</p>
      </div>
    );
  }

  if (!response || (!response.answer && !response.error)) {
    return (
      <div className="bg-amber-50 rounded-lg p-6 text-center text-gray-600 mb-8">
        <p>Ask a question to explore insights from Nobel laureate speeches.</p>
      </div>
    );
  }

  if (response.error) {
    return (
      <div className="bg-red-50 rounded-lg p-6 text-center text-red-700 mb-8">
        <p>{response.error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8 transition-all duration-300 ease-in-out">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Answer</h2>
      <div className="prose max-w-none">
        <p className="text-gray-700 leading-relaxed">{response.answer}</p>
      </div>
    </div>
  );
};

export default ResponseDisplay;