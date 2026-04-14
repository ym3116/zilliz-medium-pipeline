# Backlink Rules

When any keyword in the table below appears in a rewritten article, wrap its **first occurrence** with the corresponding URL.

## Rules
1. **First occurrence only** — link each keyword at most once per article.
2. **Append UTM** — all URLs must have `?utm_campaign=mediumkoc` appended.
3. **Skip code blocks** — do not link keywords that appear inside fenced code blocks (` ``` `).
4. **Skip headings** — do not link keywords inside `#` headings.
5. **Case-insensitive match** — match regardless of case; preserve the original casing in the rendered link text.
6. **No nested links** — if a keyword is already inside a markdown link, skip it.
7. **Longest match first** — prefer the more specific keyword (e.g., "Zilliz Cloud" before "Zilliz").

---

## Keyword → URL Table

### Product / Brand

| Keyword(s) | URL |
|---|---|
| Zilliz | https://zilliz.com/ |
| Zilliz Cloud | https://zilliz.com/cloud |
| Managed Milvus | https://zilliz.com/cloud |
| What is Milvus | https://zilliz.com/what-is-milvus |
| Milvus | https://milvus.io/ |
| Milvus Lite | https://milvus.io/blog/introducing-milvus-lite.md |
| How to Choose Milvus versions | https://zilliz.com/blog/choose-the-right-milvus-deployment-mode-ai-applications |
| Zilliz vs Milvus | https://zilliz.com/zilliz-vs-milvus |
| pinecone vs milvus | https://zilliz.com/comparison/pinecone-vs-zilliz-vs-milvus |
| serverless vector database | https://zilliz.com/serverless |

### Vector Database

| Keyword(s) | URL |
|---|---|
| Vector Database Benchmark | https://zilliz.com/vector-database-benchmark-tool?database=ZillizCloud%2CMilvus%2CElasticCloud%2CPgVector%2CPinecone%2CQdrantCloud%2CWeaviateCloud&dataset=medium&filter=none%2Clow%2Chigh&tab=1 |
| vector databases comparison | https://zilliz.com/comparison |
| open source vector database | https://zilliz.com/product/open-source-vector-database |
| vector database cost | https://zilliz.com/blog/cost-of-open-source-vector-databases-an-engineer-guide |
| cheap vector database | https://zilliz.com/blog/cost-of-open-source-vector-databases-an-engineer-guide |
| What is a vector database | https://zilliz.com/learn/what-is-vector-database |
| vector database | https://zilliz.com/learn/what-is-vector-database |

### Use Cases

| Keyword(s) | URL |
|---|---|
| vector similarity search | https://zilliz.com/learn/vector-similarity-search |
| similarity search | https://zilliz.com/learn/vector-similarity-search |
| vector search | https://zilliz.com/learn/vector-similarity-search |
| image search | https://zilliz.com/vector-database-use-cases/image-similarity-search |
| image similarity search | https://zilliz.com/vector-database-use-cases/image-similarity-search |
| semantic search | https://zilliz.com/glossary/semantic-search |
| recommender system | https://zilliz.com/vector-database-use-cases/recommender-system |
| multimodal vector database retrieval | https://zilliz.com/ai-faq/what-is-a-multimodal-vector-database |

### RAG

| Keyword(s) | URL |
|---|---|
| retrieval augmented generation | https://zilliz.com/learn/Retrieval-Augmented-Generation |
| RAG | https://zilliz.com/learn/Retrieval-Augmented-Generation |
| RAG cost | https://zilliz.com/rag-cost-calculator/ |
| RAG Cost Calculator | https://zilliz.com/rag-cost-calculator/ |
| Multimodal RAG | https://zilliz.com/blog/multimodal-rag-expanding-beyond-text-for-smarter-ai |
| Agentic RAG | https://zilliz.com/blog/build-your-voice-assistant-agentic-rag-with-milvus-and-llama-3-2 |

### Embedding

| Keyword(s) | URL |
|---|---|
| vector embeddings | https://zilliz.com/glossary/vector-embeddings |
| embedding | https://zilliz.com/glossary/vector-embeddings |
| unstructured data | https://zilliz.com/learn/introduction-to-unstructured-data |
| dense embedding | https://zilliz.com/learn/sparse-and-dense-embeddings |
| sparse vs dense | https://zilliz.com/learn/sparse-and-dense-embeddings |
| embedding model | https://zilliz.com/blog/choosing-the-right-embedding-model-for-your-data |

### AI

| Keyword(s) | URL |
|---|---|
| large language model | https://zilliz.com/glossary/large-language-models-(llms) |
| LLM | https://zilliz.com/glossary/large-language-models-(llms) |
| generative AI | https://zilliz.com/learn/generative-ai |
| GenAI | https://zilliz.com/learn/generative-ai |
| AI hallucination | https://zilliz.com/glossary/ai-hallucination |
| natural language processing | https://zilliz.com/learn/A-Beginner-Guide-to-Natural-Language-Processing |
| NLP | https://zilliz.com/learn/A-Beginner-Guide-to-Natural-Language-Processing |
| neural network | https://zilliz.com/glossary/neural-networks |

### Algorithms / Index

| Keyword(s) | URL |
|---|---|
| approximate nearest neighbor search | https://zilliz.com/glossary/anns |
| ANNS | https://zilliz.com/glossary/anns |
| hierarchical navigable small worlds | https://zilliz.com/learn/hierarchical-navigable-small-worlds-HNSW |
| HNSW | https://zilliz.com/learn/hierarchical-navigable-small-worlds-HNSW |
| Annoy | https://zilliz.com/learn/approximate-nearest-neighbor-oh-yeah-ANNOY |
| Scalar Quantization | https://zilliz.com/learn/scalar-quantization-and-product-quantization |
| Product Quantization | https://zilliz.com/learn/scalar-quantization-and-product-quantization |
| cosine similarity | https://zilliz.com/blog/similarity-metrics-for-vector-search |
| cosine distance | https://zilliz.com/blog/similarity-metrics-for-vector-search |
| k nearest neighbor | https://zilliz.com/blog/k-nearest-neighbor-algorithm-for-machine-learning |
| KNN | https://zilliz.com/blog/k-nearest-neighbor-algorithm-for-machine-learning |
| DiskANN | https://zilliz.com/learn/DiskANN-and-the-Vamana-Algorithm |
| vector index | https://zilliz.com/learn/vector-index |
| information retrieval | https://zilliz.com/learn/what-is-information-retrieval |

---

## Matching Priority

When multiple keywords could match at the same position, match the **longest keyword first** to avoid partial overlaps. Recommended priority order for overlapping terms:

1. `Zilliz Cloud` before `Zilliz`
2. `Managed Milvus` / `Milvus Lite` before `Milvus`
3. `retrieval augmented generation` before `RAG`
4. `large language model` before `LLM`
5. `approximate nearest neighbor search` before `ANNS`
6. `hierarchical navigable small worlds` before `HNSW`
7. `vector similarity search` → `similarity search` → `vector search`
8. `serverless vector database` / `open source vector database` / `vector database cost` / `What is a vector database` before `vector database`
9. `vector embeddings` before `embedding`
10. `natural language processing` before `NLP`
11. `Multimodal RAG` / `Agentic RAG` / `RAG cost` / `RAG Cost Calculator` before `RAG`

---

## Example Output

Input:
`"...using HNSW for approximate nearest neighbor search in our vector database..."`

Output:
`"...using [HNSW](https://zilliz.com/learn/hierarchical-navigable-small-worlds-HNSW?utm_campaign=mediumkoc) for [approximate nearest neighbor search](https://zilliz.com/glossary/anns?utm_campaign=mediumkoc) in our [vector database](https://zilliz.com/learn/what-is-vector-database?utm_campaign=mediumkoc)..."`
