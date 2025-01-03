# FHNW RAG Chatbot Prototype

The FHNW RAG chatbot demonstrates the practical implementation of Retrieval-Augmented Generation (RAG) through a prototype chatbot for retrieving accurate, domain-specific responses from FHNW's official website.

## Repository Structure
- **`backend/`**: Contains Flask API implementation for handling query processing, retrieval, and response generation.
- **`data_gathering_and_indexing/`**: Contains scripts for web scraping, cleaning, chunking, and embedding the data for graph and vector databases.
- **`evaluation/`**: Contains test datasets, evaluation scripts, and results for assessing chatbot performance and retrieval accuracy.
- **`frontend/`**: Contains the Next.js-based user interface, including components and styling for a seamless user experience.

## Key Features
- **Domain-Specific Retrieval:** Answers questions on admission, student regulations, and organizational details with direct links to source pages.
- **Enhanced RAG Approach:** Combines vector similarity search with graph-based refinement for high retrieval accuracy.
- **Efficient User Interaction:** Supports conversational context and real-time response streaming in markdown format.

## Architecture
- **Frontend:** Built with Next.js, Tailwind CSS, and Shadcn UI for an intuitive and responsive interface.
- **Backend:** Python Flask API leveraging Neo4j for graph-based retrieval and ChromaDB for semantic search.
- **Data Processing:** Website data scraped, cleaned, chunked, and embedded using OpenAI models.

## Deployment
- Hosted on a secure physical server with separate virtual machines for frontend and backend.
- Publicly accessible at [chatfhnw.bulpost.com](https://chatfhnw.bulpost.com).
