# check_index.py
import faiss
index = faiss.read_index('data/faiss_index_bge-large/index.faiss')
print('Index type:', type(index))
print('Index n_total:', index.ntotal)
print('Index is_trained:', getattr(index, 'is_trained', 'N/A'))
print('Index metric type:', getattr(index, 'metric_type', 'N/A'))
