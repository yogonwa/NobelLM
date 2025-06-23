import React from 'react';

const About: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">About NobelLM</h1>
      
      <div className="prose max-w-none">
        <p className="text-gray-600 mb-4">
          NobelLM is an innovative platform that leverages artificial intelligence to explore and analyze Nobel Prize acceptance speeches. Our system uses advanced language models to help users discover insights and connections across over a century of Nobel laureate wisdom.
        </p>
        
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">How It Works</h2>
        <p className="text-gray-600 mb-4">
          Using a combination of retrieval-augmented generation (RAG) and natural language processing, NobelLM allows users to ask questions about Nobel Prize speeches and receive detailed, contextually relevant answers. Each response is grounded in the original source material, with direct citations to specific speeches.
        </p>
        
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">Our Mission</h2>
        <p className="text-gray-600 mb-4">
          We aim to make the profound insights and historical significance of Nobel Prize speeches more accessible to researchers, students, and curious minds worldwide. By combining cutting-edge AI technology with this valuable historical archive, we hope to foster deeper understanding and appreciation of human achievement across disciplines.
        </p>
      </div>
    </div>
  );
};

export default About;