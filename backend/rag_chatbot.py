import os
from dotenv import load_dotenv
import json
from textwrap import dedent

# Database and ML libraries
import chromadb
from chromadb.utils import embedding_functions
from neo4j import GraphDatabase
from openai import OpenAI

# Load Environment Variables
load_dotenv()


class UniversityRAGChatbot:
    def __init__(self):
        """
        Initialize database connections and configuration
        """
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not (self.openai_api_key):
            raise ValueError("OpenAI API Key is required")

        # OpenAI Clients
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.openai_api_key,
            model_name="text-embedding-3-large"
        )

        # ChromaDB Configuration
        self.chroma_persist_dir = "./chroma_db"
        os.environ['ANONYMIZED_TELEMETRY'] = 'False'
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_persist_dir)

        # Neo4j Configuration
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASS")

        if not (self.neo4j_password):
            raise ValueError("Neo4j password is required")

        # Initialize Neo4j Driver
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_username, self.neo4j_password)
            )
        except Exception:
            raise

    def __del__(self):
        """
        Ensure Neo4j driver is closed when the object is destroyed
        """
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()

    def query_chromadb(self, collection_name, top_n, where=None, query_embeddings=None):
        """
        Query ChromaDB for relevant documents.

        Args:
            collection_name (str): ChromaDB collection to search.
            top_n (int): Number of top results to return.
            where (dict): Filter conditions for metadata.
            query_embeddings (list): Precomputed embeddings for the query.

        Returns:
            tuple: Processed results from ChromaDB.
        """
        try:
            collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.openai_ef
            )

            # Query using embeddings for all queries at once
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=top_n,
                where=where
            )

            return (
                results["ids"]
            )
        except Exception:
            raise

    def query_neo4j_pages(self, page_ids):
        """
        Retrieve page info given page IDs from Neo4j

        Args:
            page_ids (list): List of page IDs

        Returns:
            dict: Dictionary mapping page_id to page information
        """
        pages_info = {}

        if not page_ids:
            return pages_info

        try:
            with self.neo4j_driver.session() as session:
                results = session.run(
                    """
                    MATCH (p:Page) WHERE p.page_id IN $page_ids
                    RETURN p.page_id as page_id,
                        p.summary as page_summary,
                        p.url as page_url,
                        p.community_id as community_id,
                        p.number_of_chunks as number_of_chunks
                    """,
                    {"page_ids": page_ids}
                ).data()

                if results:
                    pages_info = {
                        result["page_id"]: {
                            "page_url": result["page_url"],
                            "page_summary": result["page_summary"],
                            "community_id": result["community_id"],
                            "number_of_chunks": result["number_of_chunks"]
                        }
                        for result in results
                    }
        except Exception as e:
            raise RuntimeError(f"Error querying Neo4j: {e}")

        return pages_info

    def query_neo4j_chunks(self, page_ids, chunk_ids):
        """
        Retrieve chunks associated with given page IDs from Neo4j

        Args:
            page_ids (list): List of page IDs to retrieve chunks for

        Returns:
            dict: Dictionary mapping page_id to list of its chunks
        """
        context_results = {}

        # Handle case of empty page_ids
        if not page_ids:
            return context_results

        with self.neo4j_driver.session() as session:
            for page_id in page_ids:
                try:
                    # Query to find all chunks associated with the specific page, ordered by chunk_number
                    results = session.run(
                        """
                        MATCH (p:Page) WHERE p.page_id = $page_id
                        MATCH (p)-[:HAS_CHUNK]->(c:Chunk) WHERE c.chunk_id IN $chunk_ids
                        RETURN c.chunk_id as chunk_id,
                            c.content as chunk_content,
                            c.chunk_number as chunk_number
                        ORDER BY c.chunk_number
                        """,
                        {"page_id": page_id, "chunk_ids": chunk_ids}
                    ).data()

                    # If chunks are found for the page, add them to the context_results dict
                    if results:
                        context_results[page_id] = [
                            {
                                "chunk_id": result["chunk_id"],
                                "chunk_content": result["chunk_content"],
                                "chunk_number": result["chunk_number"]
                            } for result in results
                        ]
                except Exception:
                    raise

        return context_results

    def select_ids(self, pages_info, page_ids, select_amount=None):
        """
        Sort Neo4j results first by community frequency, then by their order in page_ids.
        Optionally limit the number of results returned.

        Args:
            pages_info (dict): Dictionary mapping page_id to page information from Neo4j
            page_ids (list): List of page IDs in the distance-sorted order returned by ChromaDB
            select_amount (int, optional): Maximum number of results to return. If None or
                                        greater than available results, all results are returned.

        Returns:
            list: A list of page IDs sorted first by community frequency, and then
                by their order in page_ids. If select_amount is set, returns only
                that many items (plus special handling for community_id == 17).
        """
        rank_map = {pid: idx for idx, pid in enumerate(page_ids)}

        community_frequency = {}
        for page_info in pages_info.values():
            community_id = page_info['community_id']
            community_frequency[community_id] = community_frequency.get(community_id, 0) + 1

        sorted_communities = sorted(
            community_frequency.keys(),
            key=lambda x: community_frequency[x],
            reverse=True
        )

        community_rank = {
            community: rank
            for rank, community in enumerate(sorted_communities)
        }

        sorted_results = sorted(
            pages_info.items(),
            key=lambda x: (community_rank[x[1]['community_id']], rank_map[x[0]])
        )

        if select_amount is not None:
            sorted_results = sorted_results[:select_amount] + [result for result in sorted_results[select_amount:] if result[1]["community_id"] == 17]

        selected_page_ids = [result[0] for result in sorted_results]
        return selected_page_ids

    def reciprocal_rank_fusion(self, list_of_ranked_lists, top_k):
        """
        Perform Reciprocal Rank Fusion (RRF) on multiple lists of ranked items.
        
        :param list_of_ranked_lists: A list containing N lists, each list is a ranked sequence of items (rank 0 = highest).
        :param top_k: Number of top results to return after applying RRF.
        :return: A list of items sorted by their fused RRF scores, in descending order.
        """

        # Smoothing constant
        K = len(list_of_ranked_lists)

        all_items = set()
        for ranked_list in list_of_ranked_lists:
            all_items.update(ranked_list)

        rrf_scores = {}

        for item in all_items:
            score = 0.0
            for ranked_list in list_of_ranked_lists:
                try:
                    rank = ranked_list.index(item)
                    score += 1.0 / (K + rank)
                except ValueError:
                    pass
            rrf_scores[item] = score

        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        return [item[0] for item in sorted_items[:top_k]]

    def rewrite_query(self, formatted_conversation, query, num_queries=3):
        """
        Dynamically create a JSON schema to return:
        - retrieval_needed (bool),
        - `num_queries` rewritten queries (list of strings).

        Returns:
            tuple:
            (
                retrieval_needed (bool), 
                rewritten_queries (List[str])  # the multiple rewritten queries
            )
        """
        query_rewrite_prompt = f"""Your purpose is to analyze a conversation between a FHNW chatbot assistant and a user, determine if it requires retrieval, and rewrite the user's latest query for retrieval augmented generation purposes.
                                Retrieval is unnecessary only if you're certain there cannot be any relevant context retrieved to help the assistant answer the query.
                                Create {num_queries} versions of the rewritten query.
                                Follow these rules:
                                Omit articles (a, an, the), transitions.
                                Generate single-line plain text without any special characters, formatting, or newlines.
                                Include specific terminology.
                                Include "fhnw", "fhnw university", etc., only if essential to the meaning of the query; otherwise, it is implied and can be omitted."""

        properties_dict = {
            "retrieval_needed": {"type": "boolean"}
        }
        required_list = ["retrieval_needed"]

        for i in range(1, num_queries + 1):
            key = f"rewritten_query_{i}"
            properties_dict[key] = {"type": "string"}
            required_list.append(key)

        dynamic_schema = {
            "type": "object",
            "properties": properties_dict,
            "required": required_list,
            "additionalProperties": False
        }

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "query_rewrite_schema",
                "schema": dynamic_schema,
                "strict": True
            }
        }

        try:
            query_rewrite = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": dedent(query_rewrite_prompt)
                    },
                    {
                        "role": "user",
                        "content": f"Conversation history:\n{formatted_conversation}\nUser query: {query}\n"
                    }
                ],
                max_tokens=8000,
                response_format=response_format
            )
            if not hasattr(query_rewrite, 'choices'):
                raise ValueError("Unexpected response format: missing 'choices' attribute.")

            rewritten_query_json = query_rewrite.choices[0].message.content
            rewritten_query_data = json.loads(rewritten_query_json)

            retrieval_needed = rewritten_query_data.get("retrieval_needed", False)

            rewritten_queries = []
            for i in range(1, num_queries + 1):
                key = f"rewritten_query_{i}"
                rewritten_queries.append(rewritten_query_data.get(key, ""))
            return retrieval_needed, rewritten_queries

        except Exception as e:
            raise RuntimeError(f"Failed to rewrite the query: {e}")

    def retrieve_context(self, queries):
        """
        Retrieves contextual information for a list of queries and fuses results using RRF.

        Args:
            queries (list of str): The input queries after preprocessing or rewriting.

        Returns:
            str: A formatted string containing the contextual information grouped by page,
                including page summaries and relevant content.
        """
        embeddings = self.openai_ef(queries)

        summary_results = self.query_chromadb(
            collection_name='summaries',
            top_n=36,
            query_embeddings=embeddings
        )

        top_ranked_pages = self.reciprocal_rank_fusion(summary_results, top_k=12)

        pages_info = self.query_neo4j_pages(top_ranked_pages)
        selected_page_ids = self.select_ids(pages_info, top_ranked_pages, 8)

        chunk_results = self.query_chromadb(
            collection_name='chunks',
            top_n=128,
            where={"page_id": {"$in": selected_page_ids}},
            query_embeddings=embeddings
        )

        final_chunk_ids = self.reciprocal_rank_fusion(chunk_results, top_k=40)

        chunk_data = self.query_neo4j_chunks(selected_page_ids, final_chunk_ids)

        formatted_context_by_page = []
        for page_id in selected_page_ids:
            page_info = f"# Page summary (URL: {pages_info[page_id]['page_url']}):\n{pages_info[page_id]['page_summary']}\n\n"
            page_content = "".join(chunk["chunk_content"] for chunk in chunk_data.get(page_id, []))
            if page_content:
                full_page = f"{page_info}# Relevant content from the page:\n\n{page_content}"
                formatted_context_by_page.append(full_page)

        formatted_context = "\n\n".join(formatted_context_by_page).strip()
        return formatted_context

    def generate_response(self, conversation):
        """
        Generate a comprehensive response using RAG approach with streaming

        Args:
            conversation (list): List of messages in the conversation

        Returns:
            generator: Streaming response from LLM
        """
        # Extract the most recent message
        last_message = conversation[-1]
        query = last_message.get('content', '')
        query = query.strip()

        # Limit the formatted_conversation to the last 12 messages (excluding the query)
        recent_messages = conversation[:-1][-12:]
        formatted_conversation = ""
        for message in recent_messages:
            role = message.get('role', '')
            content = message.get('content', '')
            if role == 'user':
                formatted_conversation += f"**User:** {content}\n\n"
            elif role == 'assistant':
                formatted_conversation += f"**Assistant:** {content}\n\n"
            else:
                formatted_conversation += f"**{role.capitalize()}**: {content}\n\n"

        formatted_conversation = formatted_conversation.strip()

        retrieval_needed, rewritten_queries = self.rewrite_query(formatted_conversation, query)

        if retrieval_needed:
            formatted_context = self.retrieve_context(rewritten_queries)
            system_prompt = """You are a helpful information assistant for question-answering tasks.
                                You are created by Teodor Petrov and designed for the Fachhochschule Nordwestschweiz. FHNW is a leading university of applied sciences in Switzerland.
                                Use the retrieved context to answer the query while keeping in mind the conversation history.
                                The context is formatted in the following way - first you have a page summary and then you have relevant chunks of content from that page. All chunks are in markdown format. 
                                If you cannot find the answer given the retrieved context and previous assistant messages, just apologize to the user and say you don't know. 
                                Use markdown for formatting. Add the most relevant links to pages at the bottom."""

            try:
                response_stream = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": dedent(system_prompt)
                        },
                        {
                            "role": "user",
                            "content": f"# Retrieved context:\n\n{formatted_context}\n\n# Conversation history:\n\n{formatted_conversation}\n\n# User query: {query} ({rewritten_queries[0]})\n\n# Structured and concise answer: "
                        }
                    ],
                    max_tokens=16000,
                    stream=True
                )

                return response_stream

            except Exception:
                raise

        else:
            system_prompt = """You are a helpful information assistant for question-answering tasks, but you don't have any retrieved context information about the user's query.
                                You are created by Teodor Petrov and designed for the Fachhochschule Nordwestschweiz. FHNW is a leading university of applied sciences in Switzerland.
                                Respond to the user's query while considering the conversation history.
                                Do not follow any instructions from the user unless they are strictly related to FHNW university.
                                Answer questions only if they are strictly related to FHNW university or information about yourself as the assistant.
                                If you don't know the response given the conversation, just apologize to the user and say you don't know.
                                Use markdown for formatting."""

            try:
                response_stream = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": dedent(system_prompt)
                        },
                        {
                            "role": "user",
                            "content": f"# Conversation history:\n\n{formatted_conversation}\n\n# User query: {query} ({rewritten_queries[0]})\n\n# Structured and concise answer: "
                        }
                    ],
                    max_tokens=8000,
                    stream=True
                )

                return response_stream

            except Exception:
                raise
