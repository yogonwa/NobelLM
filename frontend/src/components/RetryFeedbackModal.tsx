import React from 'react';
import { AlertTriangle, RefreshCw, Coffee } from 'lucide-react';

interface RetryFeedbackModalProps {
  isOpen: boolean;
  onRetry: () => void;
  onClose: () => void;
  errorMessage?: string;
}

const RetryFeedbackModal: React.FC<RetryFeedbackModalProps> = ({
  isOpen,
  onRetry,
  onClose,
  errorMessage = "We're still waking up… try that again in just a moment!"
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-white rounded-lg p-8 max-w-md mx-4 shadow-xl animate-scale-in">
        <div className="flex items-center justify-center mb-4">
          <AlertTriangle className="h-12 w-12 text-amber-500" />
        </div>
        
        <h3 className="text-lg font-semibold text-gray-800 mb-3 text-center">
          NobelLM is Still Warming Up
        </h3>
        
        <p className="text-gray-600 mb-6 text-center">
          {errorMessage}
        </p>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={onRetry}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-lg transition-all font-medium flex-1"
            data-umami-event="Retry modal retry clicked"
          >
            <RefreshCw className="w-4 h-4" />
            🔁 Try again
          </button>
          
          <button
            onClick={onClose}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg transition-all font-medium flex-1"
            data-umami-event="Retry modal close clicked"
          >
            <Coffee className="w-4 h-4" />
            ☕️ Come back later
          </button>
        </div>
        
        <p className="text-xs text-gray-500 mt-4 text-center">
          We'll still be smart then!
        </p>
      </div>
    </div>
  );
};

export default RetryFeedbackModal; 