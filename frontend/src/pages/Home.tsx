import React, { useState } from 'react';
import { RotateCcw } from 'lucide-react';
import QueryInput from '../components/QueryInput';
import ResponseDisplay from '../components/ResponseDisplay';
import SourceCitation from '../components/SourceCitation';
import SuggestedPrompts from '../components/SuggestedPrompts';
import type { QueryResponse, SuggestedPrompt } from '../types';
import { fetchQueryResponse } from '../utils/api';
import nobelLogo from '../assets/nobel_logo.png';
import { Link } from 'react-router-dom';

const Home: React.FC = () => {
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  const suggestedPrompts: SuggestedPrompt[] = [
    { id: 'prompt1', text: 'Who won the Nobel Prize in Literature in 1965?' },
    { id: 'prompt2', text: 'Which country has the most Nobel literature laureates?' },
    { id: 'prompt3', text: 'What do laureates say about justice and freedom?' },
    { id: 'prompt4', text: 'How is hope portrayed in Nobel Prize lectures?' },
    { id: 'prompt5', text: 'Write a job acceptance email in the tone of a Nobel Prize winner.' }
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
            {/* Logo and title - fixed width, now clickable */}
            <Link
              to="/"
              className="flex items-center gap-3 flex-shrink-0 animate-scale-in group"
              title="Go to home page"
              style={{ textDecoration: 'none' }}
            >
              <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center transition-shadow duration-200 group-hover:shadow-lg cursor-pointer">
                <img
                  src={nobelLogo}
                  alt="Nobel Logo"
                  className="w-10 h-10 rounded-full object-cover transition-transform duration-200"
                />
              </div>
              <h1 className="text-xl font-bold text-gray-800 whitespace-nowrap group-hover:text-amber-700 transition-colors cursor-pointer">
                NobelLM
              </h1>
            </Link>
            
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
      <div className="flex flex-col items-center justify-center mt-8 mb-6">
        <h1 className="text-4xl font-bold text-gray-800 mb-4 animate-fade-in text-center">NobelLM</h1>
        <div className="w-32 h-32 mb-4 flex items-center justify-center bg-gray-50 rounded-full group transition-transform duration-200">
          <img
            src={nobelLogo}
            alt="Nobel Logo"
            className="w-32 h-32 rounded-full object-cover transition-transform duration-200 hover:-translate-y-1"
            style={{ transition: 'filter 0.2s', filter: 'none' }}
            onMouseOver={e => e.currentTarget.style.filter = 'drop-shadow(0 8px 32px rgba(0,0,0,0.35))'}
            onMouseOut={e => e.currentTarget.style.filter = 'none'}
          />
        </div>
        <h2 className="font-bold text-gray-800 mb-2 animate-fade-in text-center" style={{ animationDelay: '0.1s' }}>
          Meet <span className="font-bold italic">NobelLM</span>, a semantic search engine for Nobel Prize speeches.
        </h2>
        <p className="text-gray-600 text-center max-w-2xl mb-8 animate-fade-in" style={{ animationDelay: '0.2s' }}>
          What do Nobel Prize winners say about war, hope, or humanity? Ask and discover.
        </p>
        <div className="w-full animate-fade-in" style={{ animationDelay: '0.3s' }}>
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