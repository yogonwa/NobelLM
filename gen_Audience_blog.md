Exploring Nobel Prize Speeches with AI: A Behind-the-Scenes Look
Imagine being able to ask questions like:

“What themes do American Nobel Literature winners tend to focus on in their speeches?”
“How have women laureates described their work over the years?”

The Nobel Laureate Speech Explorer is a project I’m building to make this possible. At its heart is a system that blends traditional information retrieval with modern AI language models — a method called RAG, or Retrieval-Augmented Generation.

What Is This Project About?
The project collects and analyzes the speeches, bios, and award notes of Nobel Prize winners in Literature. For each laureate, I extract:

Their Nobel Lecture (the main speech)

Their Acceptance Speech

The Committee’s Statement about why they won

Plus structured data like name, country, language, and year

Then, using AI, the system breaks these texts into smaller passages and stores them in a searchable format. This lets you ask big, nuanced questions — and get answers pulled from the actual source material.

How Does Semantic Search Work?
Let’s say you ask:

“How do laureates talk about childhood in their lectures?”

With a traditional search engine, you'd get results only if the exact word “childhood” appeared in the text. But what if someone used “early years” or “formative experiences” instead?

This is where semantic search shines.

Instead of matching exact words, the system looks for meaning.

How? With Embeddings and Vectors
Here’s the magic trick behind the scenes:

Every passage of text is converted into a list of numbers — called a vector embedding. Think of it like plotting the passage on a map of meaning.

The user's question is also turned into a vector and plotted on the same map.

The system finds the nearest passages to the question — based on meaning, not just words.

This means it can surface speeches that use completely different wording but express similar ideas. For example, it might find a passage about “youth” or “growing up” even if you asked about “childhood.”

What Happens After That?
Once the system finds the most relevant passages, it hands them to an AI language model like GPT — which reads them and answers your question in natural language, citing the original sources.

This approach — combining AI’s language ability with your own curated knowledge — is called Retrieval-Augmented Generation. It’s like giving the AI a custom reference book and asking it to explain what it finds inside.

Why I’m Building This
This project is part learning tool, part literary explorer. I wanted to deepen my understanding of modern AI systems by building something real — and I’ve always loved literature and public speeches. Nobel lectures are often profound, and this tool gives us new ways to search across decades of thought, language, and creativity.

Stay tuned — I’ll be opening this up for public exploration once the prototype is ready.







You said:
Ok tech sidebar on chunk embed and vector semantic search stuff 
ChatGPT said:
Here’s a concise Tech Sidebar you can drop into your blog post for readers who want to understand what’s really going on under the hood with chunking, embeddings, and vector search:

Tech Sidebar: How Semantic Search Actually Works
At the heart of this project is a technique called vector-based semantic search. Here's how it works in a nutshell:

1. Chunking the Content
Every speech is broken into smaller passages — called chunks — typically 300–500 words each. This keeps things digestible and helps the AI focus on just a slice of content when answering a question.

Each chunk is also tagged with metadata like:

Who said it

What kind of speech it is (e.g., lecture or acceptance)

When and why it was given

2. Embedding the Chunks
Each chunk is then passed through a sentence embedding model, which converts the passage into a vector — a long list of numbers that represents the meaning of the text in a mathematical space.

Think of this as mapping meaning into coordinates on a huge multi-dimensional landscape.

3. Storing Vectors in FAISS
These vectors are stored in a special database called a vector index, using a library called FAISS (from Facebook AI Research). FAISS makes it lightning-fast to search for nearby vectors — meaning, it can quickly find the chunks that are most similar to your question.

4. Semantic Search in Action
When you ask a question like:

“What themes do American authors explore in their Nobel lectures?”

Here’s what happens:

Your question is embedded into a vector

The system finds the chunks that are closest to that vector (based on cosine similarity)

The top matching passages are fed into an LLM like GPT-3.5

GPT reads the source material and writes a natural-language answer — citing what it found

Why It Works
This approach allows the system to match ideas, not just keywords. A passage about “coming of age” might still be retrieved even if you never used the word “childhood.”

It’s like building a custom search engine where meaning matters more than wording — and where every answer is grounded in real human speech.


---

Blog Roadmap for NobelLM (Nobel Laureate Speech Explorer)
Your blog series has three core tracks, each with different tones and target audiences:

Track 1: The Big Reveal (Narrative + Positioning)
For a general tech-curious audience, peers, and potential collaborators
Goal: Tell the story, explain the value, hook interest.

✅ Intro Post – Why I Built This

What it is, why literature, why RAG, what you hoped to learn

Human motivation + technical aspiration

🔜 Demo + Use Case Showcase

Show off the app with examples: factual, thematic, generative

Use a teaser prompt like: “Ask Toni Morrison about justice”

Include a live link or video walkthrough (if hosted)

🔜 Series Overview Page (optional but helpful)

Index to all blog posts

Organized by track or audience (Builder / Thinker / Explorer)

Track 2: How I Built It (Technical Deep Dives)
For devs, AI builders, or recruiters who want to see how things work
Goal: Show off your thinking, system design, and craft.

🔧 RAG System Architecture Breakdown

Scraping → Chunking → Embedding → Vector Search → Prompting

Diagrams encouraged

Reflect on tradeoffs (MiniLM vs. OpenAI, Streamlit, FAISS, etc.)

🧠 How I Became a Full-Stack Prompt Engineer

Draft is done

Explains intent routing, prompt templating, context shaping

Clarifies that prompt engineering is a system not a sentence

🔄 Lessons Learned: What Surprised Me (post-MVP wrap-up)

What you expected vs. what you learned

Biggest challenges (e.g., scraper DOM fragility, thematic query classification)

Riffs on ambiguity, iteration, and design flexibility

Track 3: Human + Literary Reflection
For thoughtful readers, AI skeptics, and people who care about voice, meaning, and ethics
Goal: Offer a voice of nuance and humanity in the AI space.

✨ What We Choose to Automate, and What We Choose to Revere

Reflects on AI limits with literary/cultural material

Why reading isn’t just consuming, but thinking

How chunking loses voice, and what we sacrifice in favor of speed

Already outlined and partially written

🔮 The Future of Reading with AI (stretch/bonus post)

Could be speculative: What if AI helped us explore Nobel speeches like a map?

The tension between summary and discovery

A reader-centered AI design philosophy

📣 Light Marketing Plan
✅ Who You’re Writing For
Curious builders (like you) who want to learn RAG

Tech peers or recruiters (credibility + craftsmanship)

AI skeptics and literary people looking for thoughtfulness

Yourself—as a record of creative and technical growth

🔁 Where to Share
Personal blog (your domain: joegonwa.com)

LinkedIn posts (highlight lessons, use examples)

Hacker News or Reddit (for tech posts like the architecture and prompt engineering)

Substack cross-posting (optional if you want to build an audience)

Pin a GitHub repo with a clean README + blog links

📆 Cadence Plan
Start with 1 post per week (low pressure, keeps rhythm)

Launch the blog with 2 posts live:

Why I Built This

Use Case + Demo (or Prompt Engineering if Use Case isn’t ready)