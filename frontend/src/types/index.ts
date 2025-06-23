export interface Source {
  id: string;
  year: number;
  laureate: string;
  excerpt: string;
  content: string;
  category: 'Nobel Lecture' | 'Acceptance Speech' | 'Ceremony Award' | 'Metadata';
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  isLoading?: boolean;
  error?: string;
}

export interface SuggestedPrompt {
  id: string;
  text: string;
} 