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

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Nobel Lecture':
        return <GraduationCap className="w-4 h-4" />;
      case 'Acceptance Speech':
        return <MessageSquare className="w-4 h-4" />;
      case 'Ceremony Award':
        return <Award className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8 transition-all hover-lift">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Sources</h3>
      <div className="space-y-4">
        {sources.map((source, index) => (
          <div key={source.id || index} className="border border-gray-200 rounded-lg p-4 hover:border-amber-300 transition-all hover-lift">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-gray-600">{getCategoryIcon(source.category)}</span>
                <span className="text-sm font-medium text-gray-600">{source.category}</span>
              </div>
              <div className="text-sm text-gray-500">
                {source.year} • {source.laureate}
              </div>
            </div>
            <div className="text-gray-700 text-sm leading-relaxed">
              "{source.excerpt}"
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SourceCitation; 