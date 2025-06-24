export interface Source {
  id: string;
  year: number;
  laureate: string;
  excerpt: string;
  content: string;
  text: string;
  category: 'Nobel Lecture' | 'Acceptance Speech' | 'Ceremony Award' | 'Metadata';
  // Additional fields from backend
  score?: number;
  source_type?: string;
  country?: string;
  country_flag?: string;
  prize_motivation?: string;
  chunk_id?: string;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  isLoading?: boolean;
  error?: string;
  // Enhanced fields from backend
  answer_type?: 'metadata' | 'rag';
  metadata_answer?: {
    laureate?: string;
    year_awarded?: number;
    country?: string;
    country_flag?: string;
    category?: string;
    prize_motivation?: string;
    source?: { rule: string };
  };
}

export interface SuggestedPrompt {
  id: string;
  text: string;
} 