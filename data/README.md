# Data Directory

This directory contains the source PDF documents and graph images used by the Niyam AI Chatbot.

## Directory structure

```text
data/
├── README.md
├── PDF_Documents/
│   ├── Compounding_of_Contraventions_under_FEMA.pdf
│   ├── Deposits_and_Accounts.pdf
│   ├── External_Commercial_Borrowings_Trade_Credits_and_Structured_Obligations.pdf
│   ├── Foreign_Investment_in_India.pdf
│   ├── Insurance.pdf
│   ├── Money_Transfer_Service_Scheme.pdf
│   └── Overseas_Investment.pdf
└── Graph/
    └── graph.png
```

Folder names should match the paths configured in the project. The filenames above identify the seven supported document categories.

## PDF knowledge base

The seven PDFs form the chatbot's document-grounded knowledge base:

| PDF | Category value |
|---|---|
| `Compounding_of_Contraventions_under_FEMA.pdf` | `Compounding_of_Contraventions_under_FEMA` |
| `Deposits_and_Accounts.pdf` | `Deposits_and_Accounts` |
| `External_Commercial_Borrowings_Trade_Credits_and_Structured_Obligations.pdf` | `External_Commercial_Borrowings_Trade_Credits_and_Structured_Obligations` |
| `Foreign_Investment_in_India.pdf` | `Foreign_Investment_in_India` |
| `Insurance.pdf` | `Insurance` |
| `Money_Transfer_Service_Scheme.pdf` | `Money_Transfer_Service_Scheme` |
| `Overseas_Investment.pdf` | `Overseas_Investment` |

These documents are used to:

- Load and extract PDF page text.
- Split page content into overlapping chunks.
- Preserve source and page metadata.
- Attach a category value to each page before chunking, so the category is carried into each chunk.
- Generate HuggingFace embeddings.
- Store chunks, embeddings, and metadata in ChromaDB.
- Retrieve chunks by semantic similarity within one or more selected categories.
- Generate answers grounded in the retrieved PDF content with source references.

### Chunk metadata

Each stored chunk should include metadata in this form:

```python
{
    "source": "Insurance.pdf",
    "page": 2,
    "category": "Insurance"
}
```

The `category` value must exactly match the category strings used by the query-category node. The retriever uses the category list to filter ChromaDB results. For multiple categories, the filter can use Chroma's `$in` operator.

If category metadata is added to an existing ingestion pipeline, rebuild the vector database so every stored chunk contains the category field.

## Graph directory

The `Graph/` directory contains the PNG workflow visualization used to document the LangGraph execution flow. The diagram should reflect the current workflow:

1. `query_category_node` classifies the query.
2. `OTHER` routes directly to `generate_answer_node`.
3. Supported categories route to `retriever_node`, which applies the category metadata filter.
4. `grade_node` evaluates retrieved context.
5. Relevant context routes to answer generation; a rewrite decision loops back to retrieval while retries remain; a not-found outcome routes to answer generation for the fallback response.
6. `generate_answer_node` returns the answer or the appropriate fallback, then the graph ends.

## Purpose

The `data/` directory keeps the source knowledge documents and workflow visualization together. PDF files are the evidence source for retrieval and answer generation; the graph image documents the current LangGraph routing behavior.
