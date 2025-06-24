import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { Source } from '../types';

interface SourceCitationProps {
  sources: Source[];
}

const getCategoryBadge = (category: Source['category']) => {
  const badges = {
    'Nobel Lecture': {
      emoji: '🎓',
      bgColor: 'bg-blue-100',
      textColor: 'text-blue-800',
      borderColor: 'border-blue-200'
    },
    'Acceptance Speech': {
      emoji: '🏆',
      bgColor: 'bg-amber-100',
      textColor: 'text-amber-800',
      borderColor: 'border-amber-200'
    },
    'Ceremony Award': {
      emoji: '🎖️',
      bgColor: 'bg-purple-100',
      textColor: 'text-purple-800',
      borderColor: 'border-purple-200'
    },
    'Metadata': {
      emoji: '📊',
      bgColor: 'bg-gray-100',
      textColor: 'text-gray-800',
      borderColor: 'border-gray-200'
    }
  };

  const badge = badges[category];
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${badge.bgColor} ${badge.textColor} ${badge.borderColor}`}>
      <span className="text-sm">{badge.emoji}</span>
      {category}
    </span>
  );
};

const SourceCitation: React.FC<SourceCitationProps> = ({ sources }) => {
  const [expandedSourceId, setExpandedSourceId] = useState<string | null>(null);

  if (!sources.length) {
    return null;
  }

  const toggleSource = (id: string) => {
    if (expandedSourceId === id) {
      setExpandedSourceId(null);
    } else {
      setExpandedSourceId(id);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Sources</h2>
      <div className="space-y-4">
        {sources.map((source) => (
          <div key={source.id} className="border border-gray-200 rounded-md overflow-hidden">
            <div 
              className="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => toggleSource(source.id)}
            >
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-medium text-gray-800">
                    {source.year} – {source.laureate}
                  </span>
                  {getCategoryBadge(source.category)}
                </div>
                <p className="text-gray-600 text-sm">{source.excerpt}</p>
              </div>
              <div className="ml-4 flex-shrink-0">
                {expandedSourceId === source.id ? (
                  <ChevronUp className="h-5 w-5 text-gray-500" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-gray-500" />
                )}
              </div>
            </div>
            {expandedSourceId === source.id && (
              <div className="p-4 bg-gray-50 border-t border-gray-200">
                <p className="text-gray-700">{source.content}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SourceCitation;