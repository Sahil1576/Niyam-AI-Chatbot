# Data Directory

This directory contains the PDF documents and graph images used in the Niyam AI Chatbot project.

## 📁 Directory Structure

```text
data/
│
├── README.md
│
├── PDF Documents/
│   ├── FEMA.pdf
│   ├── Insurance.pdf
│   ├── Money_Transfer_Service_Scheme.pdf
│   └── ...
│
└── Graphs/
    ├── graph_1.png
    ├── graph_2.png
    └── ...
```

## 📄 PDF Documents

This folder contains PDF documents that serve as the knowledge base for the Niyam AI Chatbot.

These documents are used for:

- Extracting textual information.
- Document processing and text chunking.
- Generating embeddings using HuggingFace Embeddings.
- Storing document vectors in ChromaDB.
- Retrieving relevant information based on user queries.
- Generating context-based answers with source references.

Each PDF document provides information that can be retrieved by the RAG pipeline to answer user questions.

## 📊 Graph Images

This folder contains PNG images representing the graphical diagrams and workflow visualizations associated with the project.

These images are maintained for:

- Visual representation of project workflows.
- Understanding the system architecture.
- Understanding the LangGraph execution flow.
- Documenting different stages of the RAG pipeline.

## 🎯 Purpose

The `data/` directory maintains the project-related source documents and graphical resources in one place.

PDF documents are used as the knowledge source for retrieval and answer generation, while PNG images provide visual references for understanding and documenting the project.

