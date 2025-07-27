/**
 * Loading quotes and trivia for NobelLM
 * 
 * These quotes are shown during loading states to make the wait more engaging
 * and add personality to the NobelLM experience.
 */

export interface LoadingQuote {
  id: string;
  text: string;
  category: 'fact' | 'quote' | 'trivia';
  author?: string;
  year?: number;
}

export const loadingQuotes: LoadingQuote[] = [
  // Nobel Facts
  {
    id: 'fact-1',
    text: 'Toni Morrison won the Nobel in 1993 — the first Black woman to do so.',
    category: 'fact',
    year: 1993
  },
  {
    id: 'fact-2',
    text: 'Sartre refused his Nobel Prize in 1964.',
    category: 'fact',
    year: 1964
  },
  {
    id: 'fact-3',
    text: 'Bob Dylan won the Nobel Prize in Literature in 2016.',
    category: 'fact',
    year: 2016
  },
  {
    id: 'fact-4',
    text: 'The Nobel Prize in Literature has been awarded 116 times to 120 laureates.',
    category: 'fact'
  },
  {
    id: 'fact-5',
    text: 'Sweden has produced 8 Nobel literature laureates.',
    category: 'fact'
  },
  
  // Famous Quotes
  {
    id: 'quote-1',
    text: '"All art is a kind of confession."',
    category: 'quote',
    author: 'Camus',
    year: 1957
  },
  {
    id: 'quote-2',
    text: '"The only way to deal with an unfree world is to become so absolutely free that your very existence is an act of rebellion."',
    category: 'quote',
    author: 'Camus'
  },
  {
    id: 'quote-3',
    text: '"Words are all we have."',
    category: 'quote',
    author: 'Beckett',
    year: 1969
  },
  {
    id: 'quote-4',
    text: '"The truth is rarely pure and never simple."',
    category: 'quote',
    author: 'Wilde'
  },
  {
    id: 'quote-5',
    text: '"The only thing necessary for the triumph of evil is for good men to do nothing."',
    category: 'quote',
    author: 'Burke'
  },
  
  // Fun Trivia
  {
    id: 'trivia-1',
    text: 'Embedding poetic truth… Please stand by 🧠',
    category: 'trivia'
  },
  {
    id: 'trivia-2',
    text: 'Searching through 120+ years of literary wisdom...',
    category: 'trivia'
  },
  {
    id: 'trivia-3',
    text: 'Warming up the Nobel brain...',
    category: 'trivia'
  },
  {
    id: 'trivia-4',
    text: 'Consulting the laureates...',
    category: 'trivia'
  },
  {
    id: 'trivia-5',
    text: 'Diving into the archives of human thought...',
    category: 'trivia'
  },
  {
    id: 'trivia-6',
    text: 'Exploring the minds of Nobel winners...',
    category: 'trivia'
  },
  {
    id: 'trivia-7',
    text: 'Processing literary genius...',
    category: 'trivia'
  },
  {
    id: 'trivia-8',
    text: 'Unlocking the wisdom of laureates...',
    category: 'trivia'
  }
];

/**
 * Get a random loading quote
 * @param excludeId - Optional ID to exclude from selection
 * @returns A random loading quote
 */
export const getRandomLoadingQuote = (excludeId?: string): LoadingQuote => {
  const availableQuotes = excludeId 
    ? loadingQuotes.filter(quote => quote.id !== excludeId)
    : loadingQuotes;
  
  const randomIndex = Math.floor(Math.random() * availableQuotes.length);
  return availableQuotes[randomIndex];
};

/**
 * Get a loading quote by category
 * @param category - The category to filter by
 * @returns A random quote from the specified category
 */
export const getLoadingQuoteByCategory = (category: LoadingQuote['category']): LoadingQuote => {
  const categoryQuotes = loadingQuotes.filter(quote => quote.category === category);
  const randomIndex = Math.floor(Math.random() * categoryQuotes.length);
  return categoryQuotes[randomIndex];
}; 