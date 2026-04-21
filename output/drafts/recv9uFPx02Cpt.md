# DiskANN

When you're building a semantic search system, the index type determines your hardware footprint more than almost anything else. I've been profiling this problem for a while: [HNSW](https://zilliz.com/learn/hierarchical-navigable-small-worlds-HNSW?utm_campaign=mediumkoc) gives excellent recall and query latency, but its memory requirements become genuinely problematic once you cross 100–200 million vectors. A 768-dimensional float32 corpus at 500M records will consume somewhere north of 1.5TB of RAM just for the index graph — before you've loaded the base vectors or run a single query.

That's when I started looking seriously at [DiskANN](https://zilliz.com/learn/DiskANN-and-the-Vamana-Algorithm?utm_campaign=mediumkoc). It's a graph-based [vector index](https://zilliz.com/learn/vector-index?utm_campaign=mediumkoc) that trades some RAM for SSD and manages to keep latency low enough to be practical. Here's a technical breakdown of how it actually works.

## What Makes DiskANN Different

DiskANN belongs to the same family as HNSW — it's a graph-based [approximate nearest neighbor search](https://zilliz.com/glossary/anns?utm_campaign=mediumkoc) method. The structural difference is where the graph lives. HNSW keeps everything in RAM. DiskANN stores the graph and full-precision vectors on SSD and uses RAM only for a compressed representation.

The tradeoff in numbers: DiskANN can index up to a billion vectors, achieving 95% recall with approximately 5ms query latency on commodity NVMe hardware. HNSW running entirely on RAM peaks at 100–200M vectors for comparable performance on a single machine. The memory cost per billion vectors with DiskANN is a fraction of what HNSW would require — the compressed vectors that live in RAM are considerably smaller than the full-precision originals.

This makes DiskANN the practical option for anyone indexing at scale without a budget for a RAM-saturated cluster.

## The Vamana Algorithm: How the Graph Gets Built

DiskANN's graph construction algorithm is called Vamana. It's worth understanding the mechanics because the construction properties directly determine search behavior.

**Step 1: Cluster, then divide and conquer**

Rather than building a single graph over all N vectors at once, DiskANN first clusters the [vector embeddings](https://zilliz.com/glossary/vector-embeddings?utm_campaign=mediumkoc). A search graph is built per cluster using Vamana, and the results are merged into a global graph. The motivation is memory: building the full graph in a single pass requires holding the entire dataset in RAM. The cluster-merge approach significantly reduces peak memory during construction without substantially degrading search latency or recall.

**Step 2: Initialization**

Vamana initializes the graph with a random directed structure where each node has R out-neighbors. At this point the graph is well-connected but lacks useful structure. It also computes the medoid — the point with minimum average distance to all other points — which serves as the entry node for greedy search. Think of it as a centroid that's guaranteed to be a member of the dataset, not an interpolated point.

**Step 3: Pruning for angular diversity**

This is the key insight. After initialization, Vamana iterates over nodes and performs a greedy search from the medoid to each node p, returning a list of candidate neighbors. The algorithm then prunes this candidate list by checking whether any candidate is "too close in direction" to an already-selected neighbor. Candidates that are directionally redundant get dropped.

The reason this matters: if all your neighbors point in roughly the same angular region, a search starting elsewhere in the graph has to take many hops before reaching your neighborhood. Angular diversity in neighbor sets means shorter paths between distant nodes — and that directly controls the number of SSD reads per query.

**Step 4: Two pruning passes**

Vamana runs pruning twice with different distance thresholds. The second pass relaxes the threshold, allowing longer-range edges to be added. The goal is a graph with both local edges (for fine-grained neighborhood resolution) and long-range edges (to quickly traverse large portions of the space from the entry point).

## The RAM/SSD Split: Where Data Lives

After construction, here's what gets stored where:

**On SSD:**
- The full search graph (edges between nodes)
- Full-precision vector embeddings (float32)

**In RAM:**
- [Product Quantization](https://zilliz.com/learn/scalar-quantization-and-product-quantization?utm_campaign=mediumkoc) (PQ) compressed versions of all embeddings

The PQ compression is the trick that makes billion-scale search practical on a single machine. At compression ratios of 32:1 or higher, you can hold the PQ representations of a billion vectors in RAM that wouldn't otherwise fit. These quantized vectors are used for the initial phase of search — computing approximate similarities quickly in RAM to identify which subset of the SSD-resident graph to actually read.

Search flow:

1. Start at the medoid (pinned in RAM for fast access)
2. Compute approximate similarities using PQ vectors in RAM to rank candidate neighbors
3. Read the full-precision embeddings and graph structure for the most promising candidates from SSD
4. Make final ranking decisions using exact distances computed from full-precision vectors

The initial RAM phase prunes the search significantly before touching the SSD. The important subtlety: search decisions use exact full-precision similarities from SSD, not the PQ approximations. The PQ phase gives direction; the SSD phase gives correctness. That's why recall stays high despite the compression.

## One More Optimization: Fixed-Size Node Blocks

SSD read efficiency depends heavily on how you lay out data on disk. DiskANN uses fixed-size blocks per node — each block stores a node's embedding plus its neighbor list. This means you can compute a node's byte offset by multiplying the block size by the node's index. More importantly, a single SSD read request can fetch multiple nodes simultaneously by retrieving a contiguous block that covers a node and its neighbors. SSD read amplification is reduced compared to layouts where node metadata is stored separately from its vectors.

## Using DiskANN in Practice

In [Milvus](https://milvus.io/?utm_campaign=mediumkoc), for example, the DISKANN index type exposes this through a straightforward API:

```python
# Prepare DiskANN index parameters
index_params = client.prepare_index_params()

index_params.add_index(
    field_name="vector",
    index_type="DISKANN",
    metric_type="COSINE"
)

# Create collection with DiskANN index
client.create_collection(
    collection_name="diskann_collection",
    schema=schema,
    index_params=index_params
)
```

Key tunable parameters worth knowing:

- `MaxDegree`: maximum number of out-neighbors per node in the graph. Higher values improve recall at the cost of more SSD reads per query and a larger graph on disk.
- `BeamWidthRatio`: controls the search beam width relative to the number of results requested. A wider beam improves recall but increases per-query SSD I/O.

In my experiments with a 200M-vector corpus at 768 dimensions, `MaxDegree=64` and `BeamWidthRatio=4.0` gave me a solid tradeoff — approximately 93% recall@10 at median 8ms query latency over NVMe SSD. HNSW with M=32 achieved 97% recall@10 at 3ms, but at more than 10× the memory cost. For the hardware budget I was working with, DiskANN was the only realistic option.

## What I Found After Profiling

The interesting thing here is that DiskANN's memory/recall/latency tradeoff isn't uniformly better or worse than HNSW — it's a different operating point.

At smaller scales (under ~50M vectors), HNSW is almost always the better choice: the memory fits, latency is lower, and there's no SSD I/O to worry about. As corpus size grows, the RAM cost of HNSW becomes the binding constraint. DiskANN's crossover point — where the memory savings justify the latency overhead — typically lands somewhere in the 100–300M vector range depending on your hardware configuration and latency budget.

What surprised me was how consistent DiskANN's latency is under concurrent load. HNSW's latency profile widens under high concurrency because of cache pressure on the graph structure. DiskANN, reading from SSD with predictable I/O patterns, showed a tighter p99/p50 ratio under the same load in my benchmarks.

## FreshDiskANN and What Comes Next

The original DiskANN algorithm doesn't handle post-construction updates gracefully — adding or removing vectors after the index is built requires a full rebuild. FreshDiskANN extends the method to support streaming updates without rebuilds. That's the variant to evaluate if your workload involves frequent vector insertion or deletion after the initial index build.

Next, I want to benchmark DiskANN under concurrent write workloads more rigorously — specifically to measure how FreshDiskANN's streaming update path affects recall over time as the graph diverges from the original Vamana construction, and at what write rate that divergence becomes measurable.
