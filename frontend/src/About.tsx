import { Link } from 'react-router-dom'

function About() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">About NobelLM</h1>
      <div className="prose max-w-none">
        <p className="text-gray-600 mb-4">
          The <strong>NobelLM</strong> is a data-driven tool for exploring, searching, and analyzing speeches and metadata from Nobel Prize laureates, with an initial focus on Literature.
        </p>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">Features</h2>
        <ul>
          <li>Semantic search and Q&A over a century of Nobel Laureate lectures and speeches</li>
          <li>Rich metadata and source citations</li>
          <li>Modern, minimalist UI</li>
          <li>Powered by local embeddings, FAISS, and OpenAI (RAG)</li>
        </ul>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">How it works</h2>
        <ol>
          <li>Scrapes and normalizes NobelPrize.org data</li>
          <li>Chunks and embeds speech text for semantic search</li>
          <li>Retrieves relevant passages and generates answers using LLMs</li>
        </ol>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">Source & License</h2>
        <ul>
          <li>All data is public and used under fair use for educational purposes.</li>
          <li><a href="https://github.com/yogonwa/nobellm" target="_blank" rel="noopener noreferrer">GitHub Repository</a></li>
        </ul>
        <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">Contact</h2>
        <ul>
          <li>Maintained by Joe Gonwa</li>
          <li>For questions or contributions, open an issue on GitHub.</li>
        </ul>
        <div className="mt-8">
          <Link to="/" className="text-amber-700 hover:underline font-medium">← Back to Home</Link>
        </div>
      </div>
    </div>
  )
}

export default About 