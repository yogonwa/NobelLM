import React from 'react';
import { Loader2, Search, AlertTriangle } from 'lucide-react';
import type { QueryResponse } from '../types';
import nobelLogo from '../assets/nobel_logo.png';
import FactualAnswerCard from './FactualAnswerCard';

interface ResponseDisplayProps {
  response: QueryResponse | null;
  isLoading: boolean;
  onRetry?: () => void;
}

const ResponseDisplay: React.FC<ResponseDisplayProps> = ({ 
  response, 
  isLoading, 
  onRetry 
}) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 animate-fade-in">
        <div className="relative">
          <Loader2 className="h-12 w-12 text-amber-500 animate-spin mb-4" />
        </div>
        <p className="text-gray-600 font-medium mb-2">Searching through Nobel laureate speeches...</p>
        <p className="text-gray-500 text-sm">This may take a few moments</p>
      </div>
    );
  }

  if (!response || (!response.answer && !response.error)) {
    return (
      <div className="bg-amber-50 rounded-lg p-8 text-center text-gray-600 mb-8 animate-fade-in">
        <div className="flex justify-center mb-4">
          <Search className="h-12 w-12 text-amber-500" />
        </div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Ready to explore</h3>
        <p className="text-gray-600">Ask a question to discover insights from Nobel laureate speeches.</p>
      </div>
    );
  }

  if (response.error) {
    return (
      <div className="bg-red-50 rounded-lg p-8 text-center text-red-700 mb-8 animate-fade-in">
        <div className="flex justify-center mb-4">
          <AlertTriangle className="h-12 w-12 text-red-500" />
        </div>
        <h3 className="text-lg font-semibold text-red-800 mb-2">Something went wrong</h3>
        <p className="text-red-600 mb-4">{response.error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-800 rounded-lg transition-all font-medium hover-lift"
          >
            Try Again
          </button>
        )}
      </div>
    );
  }

  // Render FactualAnswerCard for factual/metadata answers
  if (response.answer_type === 'metadata' && response.metadata_answer) {
    return <FactualAnswerCard metadata={response.metadata_answer} />;
  }

  // Default: RAG/other answer types
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8 transition-all duration-300 ease-in-out hover-lift animate-fade-in">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 bg-gray-50 rounded-full flex items-center justify-center group transition-shadow duration-200">
          <img
            src={nobelLogo}
            alt="Nobel Logo"
            className="w-4 h-4 rounded-full object-cover transition-transform duration-200"
            style={{ transition: 'filter 0.2s', filter: 'none' }}
            onMouseOver={e => e.currentTarget.style.filter = 'drop-shadow(0 4px 12px rgba(0,0,0,0.35))'}
            onMouseOut={e => e.currentTarget.style.filter = 'none'}
          />
        </div>
        <h2 className="text-xl font-semibold text-gray-800">Answer</h2>
      </div>
      <div className="prose max-w-none">
        <p className="text-gray-700 leading-relaxed">{response.answer}</p>
      </div>
    </div>
  );
};

export default ResponseDisplay; 