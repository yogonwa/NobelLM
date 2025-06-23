import React from 'react';
import { SuggestedPrompt } from '../types';

interface SuggestedPromptsProps {
  prompts: SuggestedPrompt[];
  onPromptClick: (prompt: string) => void;
  isLoading: boolean;
}

const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({ 
  prompts, 
  onPromptClick,
  isLoading
}) => {
  return (
    <div className="w-full max-w-3xl mx-auto mb-12">
      <h2 className="text-lg font-medium text-gray-700 mb-3">Try asking about:</h2>
      <div className="flex flex-wrap gap-3">
        {prompts.map((prompt) => (
          <button
            key={prompt.id}
            onClick={() => onPromptClick(prompt.text)}
            disabled={isLoading}
            className="px-4 py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 rounded-full text-sm font-medium transition-colors disabled:opacity-50"
          >
            {prompt.text}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SuggestedPrompts;