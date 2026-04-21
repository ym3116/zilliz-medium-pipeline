# ⚠️Milvus Week: Array of Structs and MAX_SIM

Last week I was building a ColBERT-style retrieval system for a client's internal knowledge base, and I hit the exact problem that probably every ML engineer who's worked with multi-vector search knows: the [vector database](https://zilliz.com/learn/what-is-vector-database?utm_campaign=mediumkoc) kept returning multiple chunks from the same document instead of giving me a ranked list of unique documents. I'd fetch top-10 results, and six of them would be fragments of the same article. The whole post-processing layer I built — grouping by doc_id, deduplicating, reranking — felt exactly like what a database should be handling natively.

Then I saw the [Milvus](https://milvus.io/?utm_campaign=mediumkoc) 2.6.4 release notes and the Array of Structs + MAX_SIM combination. I spent a weekend digging into it. Here's what actually happened.

## The Core Problem: Embeddings Are Not Entities

The architectural gap has always been the same. Most vector databases treat each [embedding](https://zilliz.com/glossary/vector-embeddings?utm_campaign=mediumkoc) as an isolated row. But real applications operate on entities — documents, products, videos, scenes. When you chunk a document into 20 paragraphs and embed each one, you have 20 rows in your index. Ask for top-5, and you might get 5 rows from the same document.

I've patched this problem four different ways across different projects:
- Grouping by metadata field after retrieval
- Setting a max-per-document cap and re-querying if needed
- Running a separate reranking model that penalizes redundancy
- Using ColBERT's late interaction but still handling dedup manually

All of these work. None of them are satisfying. You're pushing application-layer logic into a problem that should be solved at retrieval time.

The use cases where this shows up are consistent:
- [RAG](https://zilliz.com/learn/Retrieval-Augmented-Generation?utm_campaign=mediumkoc) knowledge bases: articles are chunked into paragraph embeddings, so the search engine returns scattered fragments instead of the complete document
- E-commerce recommendation: a product has multiple image embeddings, and your system returns five angles of the same item rather than five unique products
- Video platforms: videos are split into clip embeddings, but search results surface slices of the same video rather than a single consolidated entry
- ColBERT / ColPali-style retrieval: documents expand into hundreds of token or patch-level embeddings, and your results come back as tiny pieces that still require merging

## Array of Structs: One Entity, One Row

Milvus 2.6.4 introduces an Array of Structs field type. A single record now holds an ordered list of Struct elements, where each Struct follows the same predefined schema — it can contain vectors, strings, scalar fields, whatever belongs to that sub-element.

Here's what a document record looks like with this structure:

```python
{
  'id': 0,
  'title': 'Walden',
  'title_vector': [0.1, 0.2, 0.3, 0.4, 0.5],
  'author': 'Henry David Thoreau',
  'year_of_publication': 1845,
  'chunks': [
    {
      'text': 'When I wrote the following pages...',
      'text_vector': [0.3, 0.2, 0.3, 0.2, 0.5],
      'chapter': 'Economy',
    },
    {
      'text': 'I would fain say something, not so much...',
      'text_vector': [0.7, 0.4, 0.2, 0.7, 0.8],
      'chapter': 'Economy'
    }
  ]
}
```

The `chunks` field is the Array of Structs field. Every paragraph that belongs to this entity lives inside one row. No more 1:N explosion of rows per document.

This is the right data model for almost every multi-vector use case I encounter:
- RAG knowledge bases: entire document (all chunks) as one record
- E-commerce: all product images as one record
- Video search: all clip embeddings as one record
- ColPali document search: all patch embeddings as one record

## MAX_SIM: Entity-Level Scoring That Makes Sense

The new field type alone wouldn't be enough. You still need a scoring mechanism that operates at the entity level, not the individual-vector level. That's what MAX_SIM provides.

When you query with MAX_SIM, Milvus compares your query vector (or token vectors) against every vector stored in the entity's Array of Structs field, and takes the maximum similarity as that entity's score. The entity is ranked based on that single score — no duplicate-filled result sets, no complex post-processing.

The Milvus docs walk through a concrete example worth understanding. Say you search for "Machine Learning Beginner Course," which gets tokenized into three vectors: `machine learning`, `beginner`, `course`. Now you have two candidate documents:

- doc_1: "Introduction Guide to Deep Neural Networks with Python"
- doc_2: "Advanced Guide to LLM Paper Reading"

For doc_1, the per-token best matches (using cosine similarity in the [0,1] range) are:
- `machine learning → deep neural networks (0.9)`
- `beginner → introduction (0.8)`
- `course → guide (0.7)`
- Sum = **2.4**

For doc_2:
- `machine learning → LLM (0.9)`
- `beginner → guide (0.6)`
- `course → guide (0.8)`
- Sum = **2.3**

doc_1 wins, which is the intuitive result — it's more of an introductory guide.

Three things to note about how MAX_SIM behaves:

1. **Semantic, not lexical.** "Machine learning" scores high against "deep neural networks" despite zero shared tokens. The scoring lives entirely in embedding space, making it robust to synonyms and paraphrases.
2. **Length-agnostic.** doc_1 has 4 vectors, doc_2 has 5. MAX_SIM doesn't care — it matches each query vector to the best available candidate within each entity, regardless of how many exist.
3. **Every query token contributes.** The sum ensures that a document that matches well on some tokens but poorly on others doesn't unfairly dominate. Lower-quality matches directly reduce the overall score.

## Setting This Up in Milvus: What the Code Looks Like

Here's how you'd define a collection schema with an Array of Structs field and set up retrieval with MAX_SIM:

```python
from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema

client = MilvusClient("milvus.db")

# Define the schema
schema = client.create_schema(
    auto_id=False,
    enable_dynamic_field=True
)

# Entity-level fields
schema.add_field("id", DataType.INT64, is_primary=True)
schema.add_field("title", DataType.VARCHAR, max_length=512)

# Array of Structs field for multi-vector storage
schema.add_field(
    "chunks",
    DataType.ARRAY,
    element_type=DataType.STRUCT,
    struct_fields=[
        FieldSchema("text", DataType.VARCHAR, max_length=4096),
        FieldSchema("text_vector", DataType.FLOAT_VECTOR, dim=768),
        FieldSchema("chapter", DataType.VARCHAR, max_length=256),
    ]
)

# Index params — HNSW index on the nested vector field
index_params = client.prepare_index_params()
index_params.add_index(
    field_name="chunks.text_vector",
    index_type="HNSW",
    metric_type="COSINE"
)

client.create_collection(
    collection_name="documents",
    schema=schema,
    index_params=index_params
)
```

One production consideration worth flagging: with large entities — documents with hundreds of chunks — the memory layout per record changes significantly compared to single-vector schemas. I'd recommend starting with a conservative estimate of average chunks-per-entity and monitoring memory consumption during index build, especially if you're running Milvus on memory-constrained nodes.

## Design Tradeoffs I'm Still Thinking About

Array of Structs + MAX_SIM solves the grouping and deduplication problem cleanly, but it's not a universal drop-in replacement.

**When it works extremely well:**
- ColBERT and ColPali retrieval, where you're doing late interaction across many token or patch vectors
- Document retrieval where you want entity-level ranking from the start
- E-commerce and media, where a "result" is always a single product or video

**Where I'd think twice:**
- If your chunks need to surface individually in the response (you want the specific paragraph, not just the document), you still need to identify the best matching chunk post-retrieval. MAX_SIM tells you which entity wins, not which internal vector was the best match. You'd need a second pass for chunk-level answers.
- Write-heavy pipelines where entities are frequently updated. The field type doesn't change Milvus's segment behavior, but it's worth testing your specific update pattern before committing.

One thing I learned the hard way on a previous RAG project: if your chunking strategy produces wildly variable chunk counts per document — some docs have 3 chunks, others have 300 — the entity-level scores aren't directly comparable. Normalize or filter by entity size if that matters for your recall metrics.

## Where This Fits in a Practical RAG Stack

For the ColBERT-style setup I was building, I'm migrating to Array of Structs with MAX_SIM as the retrieval layer. The change that matters most in production: eliminating the deduplication pass that was running after every [vector search](https://zilliz.com/learn/vector-similarity-search?utm_campaign=mediumkoc) call. In my setup, that post-processing step was adding roughly 40–80ms of latency per query depending on the result set size. With entity-level retrieval built into the database, that cost disappears.

The pattern I'm moving to:
1. At index time: one record per entity, all chunk vectors stored in the Array of Structs field
2. At query time: late-interaction scoring via MAX_SIM, entity-level ranked results returned directly
3. Final step: fetch the stored chunk text fields from the winning entity to build the LLM context window

No intermediate grouping. No dedup. No reranking middleware for deduplication purposes. Just retrieval that returns what the application actually needs.

This is the kind of database-level primitive that makes the application stack simpler. I'll be writing a follow-up once I've run this in a real traffic environment and can share actual recall and latency numbers comparing it to my current post-processing approach.
