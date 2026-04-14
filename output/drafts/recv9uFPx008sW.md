# Blog: LangChain 1.0 and Milvus: How to Build Production-Ready Agents with Real Long-Term Memory

Last week I was debugging an agent that kept "forgetting" things. We'd ask it to recall a decision from three sessions ago — the kind of thing that would be obvious to any human support engineer — and it confidently stated it had no record of it. The data existed somewhere. But our agent couldn't reach it. The reasoning was fine; the memory architecture was not.

That pushed me to do a proper audit of our stack. We were running an older LangChain setup with its Chain-based patterns, and a lot of the production problems we'd been fighting — context overflows, state loss between restarts, boilerplate code every time we swapped model providers — traced back to design choices baked into that older version.

Here's what I found when I actually dug into LangChain 1.0 and paired it with Milvus for persistent memory.

## Why the Chain-Based Design Was a Problem in Production

The original Chain-based design in LangChain 0.x worked well for prototypes. Wire up a `SimpleSequentialChain`, add a prompt template and an [LLM](https://zilliz.com/glossary/large-language-models-(llms)?utm_campaign=mediumkoc) call, and something works in half an hour. That's genuinely useful when you're validating an idea.

But chains are rigid. They define a fixed execution path. The moment your logic needs to branch — retry with different context, choose a different tool based on an intermediate result — you're fighting the framework. I've seen teams end up with deeply nested custom chains that nobody could debug. Others bypassed LangChain entirely and called the API directly.

The other issue was production control. Chains had no built-in concept of middleware or execution hooks. PII redaction? Write it yourself. Token limit handling? Your problem. Human-in-the-loop approval? Figure it out and wire it manually.

## LangChain 1.0: The ReAct Loop as the Default

The core shift in LangChain 1.0 is committing fully to the ReAct pattern: Reason → Tool Call → Observe → Decide. The team analyzed production agent implementations across the ecosystem and found that successful agents converge on this loop regardless of use case. So they made it the standard.

The entry point is `create_agent()`:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_knowledge_base, query_crm],
    system_prompt="You are a support agent. Use the tools to answer customer questions accurately."
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What's the status of order #12345?"}]
})
```

Three parameters. A working agent. Under the hood this runs on LangGraph, which gives you state persistence, interruption recovery, and streaming without writing any of that infrastructure yourself.

One thing worth noting: the `model` parameter accepts either a string identifier or a pre-instantiated model object. In production, you'll often need the object form — you may need to configure timeouts, retry settings, or API keys that aren't the defaults. Pass the object.

## Middleware: Where Production Control Lives

What made LangChain 1.0 immediately useful for our team was the Middleware system. It exposes hooks at strategic points in the ReAct loop — before model calls, after tool responses, at termination — so you can inject logic without modifying core agent code.

**PII detection** is one of the prebuilt options. We use it to redact sensitive fields before they reach third-party models:

```python
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
        PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block"),
    ],
)
```

**Summarization** is the other one I use constantly. When conversation history approaches token limits, it automatically condenses older messages:

```python
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[weather_tool, crm_tool],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            max_tokens_before_summary=4000,
            messages_to_keep=20,
        ),
    ],
)
```

Here's the design tradeoff that matters: summarization reduces token usage but loses precision. Summaries flatten detail. For domains where specific facts matter — exact figures, previous commitments, specific case notes — you need a complementary store that preserves raw details even after context gets compressed. That's where Milvus comes in.

**Tool retry** with configurable exponential backoff is also worth setting up early:

```python
from langchain.agents.middleware import ToolRetryMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[database_tool, search_tool],
    middleware=[
        ToolRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
            max_delay=60.0,
            jitter=True,
        ),
    ],
)
```

Add `jitter=True`. Without it, multiple agent instances will all retry a failed service at the same moment and you'll amplify the problem instead of recovering from it.

## Wiring Up Long-Term Memory with Milvus

The summarization tradeoff I mentioned above is real. Once you summarize a long session, detailed context — specific resolutions, exact numbers, prior decisions — gets compressed or dropped. An agent trying to recall something from a past session can't reach it.

The fix is pairing short-term context management with a proper long-term memory layer backed by [vector search](https://zilliz.com/learn/vector-similarity-search?utm_campaign=mediumkoc). I used [Milvus](https://milvus.io/?utm_campaign=mediumkoc) as the [vector database](https://zilliz.com/learn/what-is-vector-database?utm_campaign=mediumkoc) for this. The `langchain_milvus` package wraps it as a standard `VectorStore`:

```python
from langchain.agents import create_agent
from langchain_milvus import Milvus
from langchain_openai import OpenAIEmbeddings
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver

long_term_memory = Milvus(
    embedding=OpenAIEmbeddings(),
    collection_name="agent_memory",
    connection_args={"uri": "http://localhost:19530"}
)

agent = create_agent(
    model="openai:gpt-4o",
    tools=[
        long_term_memory.as_retriever().as_tool(
            name="recall_memory",
            description="Retrieve relevant historical context and past decisions"
        ),
        query_crm,
    ],
    checkpointer=InMemorySaver(),
    middleware=[
        SummarizationMiddleware(
            model="openai:gpt-4o-mini",
            max_tokens_before_summary=4000,
        )
    ],
    system_prompt="You have access to historical context. Use recall_memory when you need to retrieve past interactions."
)
```

The pattern: short-term context lives in LangGraph's checkpointer (fast, in-session), while important interactions get vectorized and stored in Milvus for cross-session recall. When the agent needs something from a past session, it calls `recall_memory`, which runs a [semantic search](https://zilliz.com/glossary/semantic-search?utm_campaign=mediumkoc) against the Milvus collection and returns the most relevant chunks.

One thing I learned the hard way: be deliberate about what you write to long-term memory. We initially stored every message, which flooded retrieval with noise. The signal degraded fast. We switched to writing only resolved interactions, key decisions, and explicitly stated user preferences. Retrieval quality improved noticeably.

## Structured Output Without the Per-Provider Boilerplate

This is a smaller win but a real one. Before LangChain 1.0, getting structured output from an agent meant writing provider-specific code. OpenAI has a native JSON mode; other models require tool-call workarounds. Every model switch meant rewriting adapters.

Now you define a Pydantic schema and pass it as `response_format`:

```python
from langchain.agents import create_agent
from pydantic import BaseModel, Field

class TicketSummary(BaseModel):
    issue_category: str = Field(description="Category of the support issue")
    resolution: str = Field(description="How the issue was resolved")
    follow_up_required: bool = Field(description="Whether follow-up action is needed")

agent = create_agent(
    model="openai:gpt-4o",
    tools=[query_crm],
    response_format=TicketSummary,
    system_prompt="After resolving an issue, return a structured summary."
)
```

LangChain detects whether the model supports native structured output and selects the enforcement strategy automatically. Switch from GPT-4o to another model and this code doesn't change.

## LangChain vs LangGraph: Choosing the Right Layer

A question that comes up: when do you use `create_agent()` versus building directly in LangGraph?

`create_agent()` covers the majority of standard agent scenarios — a single agent that reasons, calls tools, and returns a result. LangGraph becomes necessary when you need custom state machines: agent A handles step one, passes state to agent B for step two, with conditional routing based on intermediate results. That's outside what `create_agent()` is designed for.

The practical thing is that they're complementary. You can start with `create_agent()` and introduce LangGraph for the specific parts of your workflow that need finer control. There's no need to choose one and commit upfront.

## Production Considerations Before You Ship

A few things that matter once you leave local testing:

**[Embedding model](https://zilliz.com/blog/choosing-the-right-embedding-model-for-your-data?utm_campaign=mediumkoc) versioning**: If you vectorize new documents with a different model version than what your existing index was built with, retrieval quality silently degrades. Version-lock your embedding model and record which version each Milvus collection was indexed with. This sounds obvious until you've lost a week debugging retrieval regressions to a model version bump.

**Milvus deployment mode**: For development, Milvus Lite runs in-process with no server required. For production, you need a standalone or distributed deployment — or a managed option like [Zilliz Cloud](https://zilliz.com/cloud?utm_campaign=mediumkoc) if you'd rather not handle the operational overhead. The connection args change; your application code doesn't.

**Retrieval latency in the loop**: Each tool call adds a round trip. If your agent calls Milvus on every turn, you'll feel the latency accumulate. Keep frequently-needed context in short-term memory and only fall back to Milvus retrieval when in-session context doesn't cover the query. Profile your agent's tool call patterns early.

The combination of LangChain 1.0's structured ReAct loop, composable middleware, and Milvus for durable long-term memory covers most of what we needed to move from reactive firefighting to building reliable features on top of a stable agent architecture. The memory problem that started this investigation is solved — and the production controls we'd been writing from scratch are now just configuration.
