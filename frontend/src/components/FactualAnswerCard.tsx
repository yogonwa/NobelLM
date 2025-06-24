import React from 'react';
import { Calendar, MapPin, BookOpen, Atom, Heart, Briefcase, Leaf, Trophy } from 'lucide-react';
import nobelLogo from '../assets/nobel_logo.png';

interface LaureateMetadata {
  laureate?: string;
  year_awarded?: number;
  country?: string;
  country_flag?: string;
  category?: string;
  prize_motivation?: string;
}

interface FactualAnswerCardProps {
  metadata: LaureateMetadata;
}

const getCategoryIcon = (category: string | undefined) => {
  const categoryIcons = {
    'Literature': { icon: BookOpen, emoji: '📚', color: 'text-blue-600' },
    'Physics': { icon: Atom, emoji: '⚛️', color: 'text-purple-600' },
    'Chemistry': { icon: Atom, emoji: '🧪', color: 'text-green-600' },
    'Medicine': { icon: Heart, emoji: '🏥', color: 'text-red-600' },
    'Peace': { icon: Trophy, emoji: '🕊️', color: 'text-amber-600' },
    'Economics': { icon: Briefcase, emoji: '💰', color: 'text-indigo-600' },
    'Physiology or Medicine': { icon: Heart, emoji: '🏥', color: 'text-red-600' }
  };
  if (!category) return { icon: Trophy, emoji: '🏆', color: 'text-gray-600' };
  return categoryIcons[category as keyof typeof categoryIcons] || { icon: Trophy, emoji: '🏆', color: 'text-gray-600' };
};

const FactualAnswerCard: React.FC<FactualAnswerCardProps> = ({ metadata }) => {
  const categoryInfo = getCategoryIcon(metadata.category);
  const CategoryIcon = categoryInfo.icon;
  const countryFlag = metadata.country_flag || '🌍';

  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl shadow-lg border border-amber-200 p-8 mb-8 transition-all duration-300 ease-in-out">
      {/* Header with NobelLM logo */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center shadow-md">
          <img src={nobelLogo} alt="NobelLM Logo" className="w-7 h-7 object-contain" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Nobel Prize Winner</h2>
          <p className="text-amber-700 font-medium">Factual Information</p>
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Left column - Laureate info */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-amber-100">
            <div className="flex items-center gap-2 mb-2">
              <Trophy className="w-5 h-5 text-amber-600" />
              <span className="text-sm font-medium text-gray-600 uppercase tracking-wide">Laureate</span>
            </div>
            <p className="text-2xl font-bold text-gray-800">{metadata.laureate || 'Unknown'}</p>
          </div>

          <div className="bg-white rounded-lg p-4 shadow-sm border border-amber-100">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-5 h-5 text-amber-600" />
              <span className="text-sm font-medium text-gray-600 uppercase tracking-wide">Year Awarded</span>
            </div>
            <p className="text-xl font-semibold text-gray-800">{metadata.year_awarded || 'Unknown'}</p>
          </div>
        </div>

        {/* Right column - Category and country */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-amber-100">
            <div className="flex items-center gap-2 mb-2">
              <CategoryIcon className={`w-5 h-5 ${categoryInfo.color}`} />
              <span className="text-sm font-medium text-gray-600 uppercase tracking-wide">Category</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg">{categoryInfo.emoji}</span>
              <p className="text-xl font-semibold text-gray-800">{metadata.category || 'Unknown'}</p>
            </div>
          </div>

          <div className="bg-white rounded-lg p-4 shadow-sm border border-amber-100">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-amber-600" />
              <span className="text-sm font-medium text-gray-600 uppercase tracking-wide">Country</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg">{countryFlag}</span>
              <p className="text-xl font-semibold text-gray-800">{metadata.country || 'Unknown'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Prize motivation - full width */}
      <div className="mt-6 bg-white rounded-lg p-4 shadow-sm border border-amber-100">
        <div className="flex items-center gap-2 mb-3">
          <Leaf className="w-5 h-5 text-amber-600" />
          <span className="text-sm font-medium text-gray-600 uppercase tracking-wide">Prize Motivation</span>
        </div>
        <blockquote className="text-gray-700 italic text-lg leading-relaxed">
          {metadata.prize_motivation || 'No prize motivation available.'}
        </blockquote>
      </div>

      {/* Summary text */}
      <div className="mt-6 pt-4 border-t border-amber-200">
        <p className="text-gray-700 leading-relaxed">
          <span className="font-semibold">The winner was:</span> {metadata.laureate || 'Unknown'}. 
          <span className="font-semibold"> The laureate was recognized for:</span> {metadata.prize_motivation || 'No prize motivation available.'}
        </p>
      </div>
    </div>
  );
};

export default FactualAnswerCard;