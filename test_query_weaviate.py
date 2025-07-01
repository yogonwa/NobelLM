from query_weaviate import query_weaviate

query = "What do laureates say about the creative process?"
results = query_weaviate(query_text=query, top_k=5)

print(f"\n🔍 Query: {query}\n")
for r in results:
    print(f"🎯 Rank {r['rank']} — {r.get('laureate')} ({r.get('year_awarded')})")
    print(f"📝 {r.get('text', '')[:200]}...\n")
