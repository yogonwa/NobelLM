import React from 'react';
import { GraduationCap, MessageSquare, Award, FileText } from 'lucide-react';
import type { Source } from '../types';

interface SourceCitationProps {
  sources: Source[];
}

const SourceCitation: React.FC<SourceCitationProps> = ({ sources }) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  const getCategoryInfo = (sourceType: string) => {
    switch (sourceType) {
      case 'nobel_lecture':
        return { label: 'Nobel Lecture', icon: <GraduationCap className="w-3 h-3" />, emoji: '🎓' };
      case 'acceptance_speech':
        return { label: 'Acceptance Speech', icon: <MessageSquare className="w-3 h-3" />, emoji: '💬' };
      case 'ceremony_speech':
        return { label: 'Ceremony Award', icon: <Award className="w-3 h-3" />, emoji: '🏆' };
      default:
        return { label: sourceType || 'Document', icon: <FileText className="w-3 h-3" />, emoji: '📄' };
    }
  };

  const truncateText = (text: string, maxLength: number = 50) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8 transition-all hover-lift">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Sources</h3>
      <div className="space-y-4">
        {sources.map((source, index) => {
          const categoryInfo = getCategoryInfo(source.source_type || '');
          const truncatedExcerpt = truncateText(source.text || source.excerpt || source.content || '', 50);
          const cardKey = source.chunk_id || source.id || index;
          
          return (
            <div key={cardKey} className="border border-gray-200 rounded-lg p-4 hover:border-amber-300 transition-all hover-lift">
              {/* Header: Laureate Name - Country Flag - Year - Category Pill */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-800">{source.laureate}</span>
                  {source.country_flag && (
                    <span className="text-lg">{source.country_flag}</span>
                  )}
                  <span className="text-gray-600">•</span>
                  <span className="text-gray-600">{source.year}</span>
                </div>
                
                {/* Category Pill/Tag */}
                <div className="flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-medium">
                  <span>{categoryInfo.emoji}</span>
                  <span>{categoryInfo.label}</span>
                </div>
              </div>
              
              {/* Body: First 50 characters of chunk */}
              <div className="text-gray-700 text-sm leading-relaxed">
                "{truncatedExcerpt}"
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SourceCitation; 