import React, { useState } from 'react';
import { Award, RotateCcw } from 'lucide-react';
import QueryInput from '../components/QueryInput';
import ResponseDisplay from '../components/ResponseDisplay';
import SourceCitation from '../components/SourceCitation';
import SuggestedPrompts from '../components/SuggestedPrompts';
import type { QueryResponse, SuggestedPrompt } from '../types';
import { fetchQueryResponse } from '../utils/api';

const Home: React.FC = () => {
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  const suggestedPrompts: SuggestedPrompt[] = [
    { id: 'prompt1', text: 'What lectures mention war?' },
    { id: 'prompt2', text: 'Who spoke about solitude?' },
    { id: 'prompt3', text: 'How have laureates described their creative process?' },
    { id: 'prompt4', text: 'Which themes appear most often in acceptance speeches?' }
  ];

  const handleSubmit = async (query: string) => {
    if (!query.trim()) return;
    
    setCurrentQuery(query);
    setHasSearched(true);
    setIsLoading(true);
    
    try {
      const result = await fetchQueryResponse(query);
      setResponse(result);
    } catch {
      setResponse({
        answer: '',
        sources: [],
        error: 'An error occurred while processing your request. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (currentQuery.trim()) {
      handleSubmit(currentQuery);
    }
  };

  const handleClearSearch = () => {
    setResponse(null);
    setCurrentQuery('');
    setHasSearched(false);
    setIsLoading(false);
  };

  // Results page layout
  if (hasSearched) {
    return (
      <main className="max-w-6xl mx-auto px-4 animate-in">
        {/* Top header with logo and search - full width layout */}
        <div className="py-6 border-b border-gray-200 mb-8 animate-fade-in">
          <div className="flex items-center gap-6">
            {/* Logo and title - fixed width */}
            <div className="flex items-center gap-3 flex-shrink-0 animate-scale-in">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center shadow-md hover-lift">
                <Award className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-800 whitespace-nowrap">NobelLM</h1>
            </div>
            
            {/* Search input - takes remaining space */}
            <div className="flex-1 animate-fade-in" style={{ animationDelay: '0.1s' }}>
              <QueryInput 
                onSubmit={handleSubmit} 
                isLoading={isLoading}
                initialValue={currentQuery}
                compact={true}
              />
            </div>
            
            {/* Try again button - fixed width */}
            <button
              onClick={handleClearSearch}
              className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-all flex-shrink-0 hover-lift"
              title="Clear search and try again"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="hidden sm:inline font-medium">Try Again</span>
            </button>
          </div>
        </div>

        {/* Results content */}
        <div className="space-y-8 pb-12">
          <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <ResponseDisplay response={response} isLoading={isLoading} onRetry={handleRetry} />
          </div>
          
          {response && response.sources.length > 0 && !isLoading && (
            <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <SourceCitation sources={response.sources} />
            </div>
          )}
          
          {/* Bottom Try Again button - only show after results are loaded */}
          {(response || (!isLoading && hasSearched)) && (
            <div className="flex justify-center pt-8 border-t border-gray-100 animate-fade-in" style={{ animationDelay: '0.4s' }}>
              <button
                onClick={handleClearSearch}
                className="flex items-center gap-3 px-6 py-3 bg-amber-50 hover:bg-amber-100 text-amber-800 rounded-lg transition-all font-medium shadow-sm hover-lift"
                title="Clear search and start over"
              >
                <RotateCcw className="w-5 h-5" />
                Try Another Search
              </button>
            </div>
          )}
        </div>
      </main>
    );
  }

  // Initial home page layout
  return (
    <main className="max-w-4xl mx-auto px-4">
      {/* Hero section positioned at ~40% viewport height */}
      <div className="flex flex-col items-center justify-center min-h-[40vh] mb-8">
        {/* Logo */}
        <div className="w-32 h-32 mb-6 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center shadow-lg animate-scale-in hover-lift">
          <Award className="w-16 h-16 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-gray-800 mb-4 animate-fade-in" style={{ animationDelay: '0.1s' }}>NobelLM</h1>
        <p className="text-gray-600 text-center max-w-2xl mb-8 animate-fade-in" style={{ animationDelay: '0.2s' }}>
          Ask questions and discover insights from over a century of Nobel Prize lectures and acceptance speeches.
        </p>
        
        <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <QueryInput onSubmit={handleSubmit} isLoading={isLoading} />
        </div>
      </div>
      
      <div className="pb-8 animate-fade-in" style={{ animationDelay: '0.4s' }}>
        <SuggestedPrompts 
          prompts={suggestedPrompts} 
          onPromptClick={handleSubmit}
          isLoading={isLoading}
        />
      </div>
    </main>
  );
};

export default Home; 