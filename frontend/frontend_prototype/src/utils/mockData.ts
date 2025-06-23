import { Source, SuggestedPrompt, QueryResponse } from '../types';

// Mock suggested prompts
export const suggestedPrompts: SuggestedPrompt[] = [
  { id: 'prompt1', text: 'What lectures mention war?' },
  { id: 'prompt2', text: 'Who spoke about solitude?' },
  { id: 'prompt3', text: 'How have laureates described their creative process?' },
  { id: 'prompt4', text: 'Which themes appear most often in acceptance speeches?' }
];

// Mock sources
export const mockSources: Source[] = [
  {
    id: 'source1',
    year: 1982,
    laureate: 'Gabriel García Márquez',
    category: 'Nobel Lecture',
    excerpt: 'I dare to think that it is this outsized reality, and not just its literary expression, that has deserved the attention of the Swedish Academy of Letters. A reality not of paper, but one that lives within us and determines each instant of our countless daily deaths, and that nourishes a source of insatiable creativity, full of sorrow and beauty.',
    content: 'I dare to think that it is this outsized reality, and not just its literary expression, that has deserved the attention of the Swedish Academy of Letters. A reality not of paper, but one that lives within us and determines each instant of our countless daily deaths, and that nourishes a source of insatiable creativity, full of sorrow and beauty. A reality that is not just the reality of the poet, but the reality of all those who have been inspired to speak the language of magical realism, that is, the language of a reality so foreign to others that it seems fantastical.'
  },
  {
    id: 'source2',
    year: 1950,
    laureate: 'Bertrand Russell',
    category: 'Acceptance Speech',
    excerpt: 'Man is a part of nature, not something contrasted with nature. His thoughts and his bodily movements follow the same laws that describe the motions of stars and atoms.',
    content: 'Man is a part of nature, not something contrasted with nature. His thoughts and his bodily movements follow the same laws that describe the motions of stars and atoms. In this scientific age, when the study of man as part of the natural world has made great progress, it is astonishing how little this integration of man with nature has affected our moral thinking.'
  },
  {
    id: 'source3',
    year: 2006,
    laureate: 'Orhan Pamuk',
    category: 'Ceremony Award',
    excerpt: 'The writer\'s secret is not inspiration – for it is never clear where that comes from – but stubbornness, endurance.',
    content: 'The writer\'s secret is not inspiration – for it is never clear where that comes from – but stubbornness, endurance. The lovely Turkish expression "to dig a well with a needle" seems to me to have been invented with writers in mind. In the old stories, I love the patience of Ferhat, who digs through mountains for his love – and I understand it, too.'
  }
];

// Mock API response function
export const fetchQueryResponse = (query: string): Promise<QueryResponse> => {
  return new Promise((resolve) => {
    // Simulate network delay
    setTimeout(() => {
      if (!query.trim()) {
        resolve({
          answer: '',
          sources: [],
          error: 'Please enter a question to explore Nobel laureate speeches.'
        });
        return;
      }

      if (query.toLowerCase().includes('war')) {
        resolve({
          answer: 'Several Nobel laureates have addressed the theme of war in their lectures. Bertrand Russell, who won the Nobel Prize in Literature in 1950, spoke extensively about the moral responsibility of intellectuals in preventing war. More recently, Orhan Pamuk reflected on how literature helps us understand the human dimensions of conflict. The most powerful anti-war sentiment was perhaps expressed by William Faulkner in his 1949 speech, where he declared his belief that "man will not merely endure: he will prevail" against the fear of war and destruction.',
          sources: mockSources
        });
      } else if (query.toLowerCase().includes('solitude')) {
        resolve({
          answer: 'The theme of solitude is most prominently explored in Gabriel García Márquez\'s Nobel lecture, where he connects it to the Latin American experience. His famous novel "One Hundred Years of Solitude" examines isolation both as a personal condition and as a metaphor for Latin America\'s position in the world. In his lecture, Márquez describes solitude as both a curse and a creative force, something that has shaped the literary tradition of his continent.',
          sources: [mockSources[0], mockSources[2], mockSources[1]]
        });
      } else {
        resolve({
          answer: 'The Nobel Prize lectures represent a remarkable collection of human wisdom and creative reflection. Many laureates have used their platform to address universal themes like the role of literature in society, the search for truth, and the responsibility of writers in times of social change. The lectures often reveal the laureate\'s artistic philosophy and the cultural context that shaped their work. Through these speeches, we can trace the evolution of literary thought across different cultures and time periods.',
          sources: mockSources.slice().reverse()
        });
      }
    }, 1500);
  });
};