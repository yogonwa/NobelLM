import { Link } from 'react-router-dom'

function About() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">About NobelLM</h1>
      <div className="prose max-w-none">
        <p className="text-gray-600 mb-4">
          <strong>NobelLM</strong> is a web app that scrapes, structures, and semantically searches over 100 years of Nobel Literature lectures and speeches. Powered by embeddings and generative AI, it lets users ask open-ended questions and receive grounded responses with citations from real source material.
        </p>
        <p className="text-gray-600 mb-6">
          This project blends cutting-edge AI with timeless human expression—offering a new way to explore the voices of some of the world's greatest writers.
        </p>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">Features</h2>
        <ul className="space-y-2">
          <li>🔍 Semantic search and AI-powered Q&A over a century of Nobel speeches</li>
          <li>📎 Source citations and metadata for every passage</li>
          <li>✨ Clean, minimalist interface for intuitive exploration</li>
          <li>⚙️ Built with a modular Retrieval-Augmented Generation (RAG) system using local embeddings, Modal, qdrant, and OpenAI</li>
        </ul>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">How It Works</h2>
        <ol className="space-y-2">
          <li>Scrape NobelPrize.org for speech and award content</li>
          <li>Structure the data with normalized metadata and filters</li>
          <li>Embed the speech texts using sentence-transformer models</li>
          <li>Search via semantic query matching, citation routing, and LLM generation</li>
        </ol>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">Learn More</h2>
        <p className="text-gray-600 mb-4">
          Curious about how <strong>NobelLM</strong> was built — or why?
        </p>
        <p className="text-gray-600 mb-6">
          Explore the full <a href="https://joegonwa.com/projects/nobellm/" target="_blank" rel="noopener noreferrer" className="text-amber-700 hover:underline">behind-the-scenes blog series</a>, where I share the technical architecture, prompt design decisions, and reflections on building with AI and literature in mind.
        </p>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">Source & License</h2>
        <ul className="space-y-2">
          <li>All data is public and used under fair use for educational purposes.</li>
        </ul>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">GitHub & Contact</h2>
        <ul className="space-y-2">
          <li>🛠 <a href="https://github.com/yogonwa/nobellm" target="_blank" rel="noopener noreferrer" className="text-amber-700 hover:underline">Source Code on GitHub</a></li>
          <li>📫 Maintained by Joe Gonwa</li>
        </ul>
        <div className="mt-8">
          <Link to="/" className="text-amber-700 hover:underline font-medium">← Back to Home</Link>
        </div>
      </div>
    </div>
  )
}

export default About 