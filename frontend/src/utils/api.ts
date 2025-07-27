import type { QueryResponse } from '../types';

// API base URL configuration
const getApiBaseUrl = (): string => {
  // Use environment variable if available (for production deployments)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // In production, use the deployed API URL
  if (import.meta.env.PROD) {
    return 'https://nobellm-api.fly.dev';
  }
  // In development, use the proxy configured in vite.config.ts
  return '';
};

// Mock sources for development/testing
export const mockSources = [
  {
    id: 'source1',
    year: 1982,
    laureate: 'Gabriel García Márquez',
    category: 'Nobel Lecture' as const,
    excerpt: 'I dare to think that it is this outsized reality, and not just its literary expression, that has deserved the attention of the Swedish Academy of Letters.',
    content: 'I dare to think that it is this outsized reality, and not just its literary expression, that has deserved the attention of the Swedish Academy of Letters. A reality not of paper, but one that lives within us and determines each instant of our countless daily deaths, and that nourishes a source of insatiable creativity, full of sorrow and beauty.'
  },
  {
    id: 'source2',
    year: 1950,
    laureate: 'Bertrand Russell',
    category: 'Acceptance Speech' as const,
    excerpt: 'Man is a part of nature, not something contrasted with nature. His thoughts and his bodily movements follow the same laws that describe the motions of stars and atoms.',
    content: 'Man is a part of nature, not something contrasted with nature. His thoughts and his bodily movements follow the same laws that describe the motions of stars and atoms. In this scientific age, when the study of man as part of the natural world has made great progress, it is astonishing how little this integration of man with nature has affected our moral thinking.'
  }
];

// API function to fetch query response with enhanced error handling
export const fetchQueryResponse = async (query: string): Promise<QueryResponse> => {
  if (!query.trim()) {
    return {
      answer: '',
      sources: [],
      error: 'Please enter a question to explore Nobel laureate speeches.'
    };
  }

  const start = performance.now();

  // Create a timeout promise
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error('Request timeout')), 45000); // 45 second timeout
  });

  const attemptRequest = async (isRetry: boolean = false): Promise<Response> => {
    const apiUrl = `${getApiBaseUrl()}/api/query`;
    const response = await Promise.race([
      fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() }),
      }),
      timeoutPromise
    ]);

    // Check if we should retry
    if (isRetry === false && (response.status === 502 || response.status === 504 || response.status === 503)) {
      // Wait 2 seconds before retry
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Show retry message to user (this will be handled by the UI)
      console.log('🔄 Warming up the Nobel brain 🧠... trying again...');
      
      // Retry the request
      return attemptRequest(true);
    }

    return response;
  };

  try {
    const response = await attemptRequest();

    if (!response.ok) {
      let errorMessage = 'An error occurred while processing your request.';
      
      if (response.status === 404) {
        errorMessage = 'The search service is currently unavailable. Please try again later.';
      } else if (response.status === 429) {
        errorMessage = 'Too many requests. Please wait a moment and try again.';
      } else if (response.status >= 500) {
        errorMessage = 'Server error. Please try again later.';
      } else if (response.status === 400) {
        errorMessage = 'Invalid request. Please check your question and try again.';
      }
      
      throw new Error(errorMessage);
    }

    const data = await response.json();
    
    // Validate response structure
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid response format from server.');
    }
    
    // Transform the backend response to match our frontend interface
    const result = {
      answer: data.answer || '',
      sources: data.sources?.map((source: any, index: number) => ({
        ...source,
        id: source.chunk_id || `source-${index}`,
        year: source.year_awarded || source.year,
      })) || [],
      error: data.error || undefined,
      answer_type: data.answer_type,
      metadata_answer: data.metadata_answer
    };

    const duration = performance.now() - start;
    console.log(`⏱ Query completed in ${duration.toFixed(1)}ms`);
    
    return result;
  } catch (error) {
    console.error('API Error:', error);
    
    let errorMessage = 'An error occurred while processing your request. Please try again.';
    
    if (error instanceof Error) {
      if (error.message === 'Request timeout') {
        errorMessage = 'Request timed out. Please try again with a shorter question.';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (error.message.includes('JSON')) {
        errorMessage = 'Invalid response from server. Please try again.';
      } else {
        errorMessage = error.message;
      }
    }
    
    const duration = performance.now() - start;
    console.log(`⏱ Query failed after ${duration.toFixed(1)}ms`);
    
    return {
      answer: '',
      sources: [],
      error: errorMessage
    };
  }
};

// Warm-up functions for service initialization
export const warmUpServices = async (): Promise<{ backend: boolean; modal: boolean }> => {
  const results = { backend: false, modal: false };
  const start = performance.now();

  try {
    // Warm up backend using /api/readyz endpoint
    const backendUrl = `${getApiBaseUrl()}/api/readyz`;
    const backendResponse = await fetch(backendUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    
    if (backendResponse.ok) {
      results.backend = true;
      console.log('✅ Backend service warmed up');
    }
  } catch (error) {
    console.warn('⚠️ Backend warm-up failed:', error);
  }
  
  try {
    // Warm up Modal service
    const modalUrl = `${getApiBaseUrl()}/api/modal/warmup`;
    const modalResponse = await fetch(modalUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    
    if (modalResponse.ok || modalResponse.status === 204) {
      results.modal = true;
      console.log('✅ Modal service warmed up');
    }
  } catch (error) {
    console.warn('⚠️ Modal warm-up failed:', error);
  }
  
  const duration = performance.now() - start;
  console.log(`⏱ Warm-up completed in ${duration.toFixed(1)}ms`);
  return results;
}; 