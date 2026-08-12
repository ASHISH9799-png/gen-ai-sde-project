import os
import contextlib
import chromadb
from chromadb.config import Settings


# function to supress un silenceable third party print outputs
def initialize_clean_client():
    with open(os.devnull, "w") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            client = chromadb.PersistentClient(
                path="./rbi_vector_db", settings=Settings(anonymized_telemetry=False)
            )
            # this line is here to catch its background thread warning:
            db_collection = client.get_or_create_collection(name="rbi_rules")
            return client, db_collection


# create your clean client instance
chroma_client, collection = initialize_clean_client()


def insert_rule(text: str, doc_name: str, section: str, rule_id: str):
    """Saves an RBI compliance rule with its official citation metadata."""
    collection.add(
        documents=[text],
        metadatas=[{"source": doc_name, "section": section}],
        ids=[rule_id],
    )


def query_rules(query_text: str, n_results: int = 1):
    """
    Queries the local Chroma vector collection using semantic similarity search.
    """
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return results


def query_rules(user_query: str):
    """Searches the database for the closest matching banking rule."""
    results = collection.query(query_texts=[user_query], n_results=1)
    return results


# this block allws us to run this file directly to test it
if __name__ == "__main__":
    import os
    import contextlib

    print("Initializing test database seed...")

    # silence the background collection worker threads during seeding
    with open(os.devnull, "w") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            # seeding one real RBI rule into our vector database
            insert_rule(
                text="All commercial banks must maintain a Cash Reserve Ratio (CRR) of 4.50 percent of thier Net Demand and Time Liabilities.",
                doc_name="RBI Master Direction 2024",
                section="Chapter II - CRR Obligations",
                rule_id="rbi_crr_rule_01",
            )

    print("Database seeded successfully!")

    # ---Test Query Block---
    print("\nExecuting Vector Database Semantic Search Test...")
    search_query = "What is the requirement for the cash reserve ratio?"

    # function for muting unwanted telemetry event
    with (
        open(os.devnull, "w") as devnull,
        contextlib.redirect_stdout(devnull),
        contextlib.redirect_stderr(devnull),
    ):
        search_results = query_rules(search_query)

    print("\n--- [SEARCH RESULT MATCH] ---")
    print(search_results["documents"][0][0])
    print("-----------------------------\n")
