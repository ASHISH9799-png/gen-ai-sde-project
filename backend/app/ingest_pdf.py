import os
from pypdf import PdfReader

# Import your insert function from your existing vector_store.py script
from app.vector_store import insert_rule


def extract_and_chunk_pdf(
    pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 200
):
    """
    Reads a local RBI PDF circular file, extarcts text,
    amd chunks it safely to preserve legal definitions.
    """
    if not os.path.exists(pdf_path):
        print(f" Error: File not found at {pdf_path}")
        return

    print(f" Reading PDF: {pdf_path}...")
    reader = PdfReader(pdf_path)
    full_text = ""

    # 1. Loop through every page and pull raw text
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    print("Splitting document into compliance chunks...")
    words = full_text.split()
    chunks = []

    words_chunk_size = chunk_size // 4
    words_overlap = chunk_overlap // 4

    for i in range(0, len(words), words_chunk_size - words_overlap):
        chunk_words = words[i : i + words_chunk_size]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)

    print(f"Generated {len(chunks)} chunks.")

    print("Indexing chunks into ChromaDB...")
    for index, chunk in enumerate(chunks):
        chunk_id = f"{os.path.basename(pdf_path)}_chunk_{index}"
        file_name = os.path.basename(pdf_path)

        # Using our real imported insert_rule function!
        insert_rule(
            text=chunk,
            doc_name=file_name,
            section=f"Chunk Level Data Partition {index}",
            rule_id=chunk_id,
        )
        print(f"Indexed: {chunk_id}")


print("Ingestion complete! ALL chunks securely stored in ChromaDB.")


if __name__ == "__main__":
    # 1. Enforce our target backend data directory
    folder = "backend/data"

    # 2. Get a list of every file present in that folder
    all_files = os.listdir(folder)

    # 3. Initialize our Hash Map (Dictionary)
    pdf_files_map = {}

    # 4. Populate the Hash Map with metadata
    for filename in all_files:
        if filename.endswith(".pdf"):
            # The filename is the KEY, a dictionary of details is the VALUE
            pdf_files_map[filename] = {
                "full_path": os.path.join(folder, filename),
                "status": "pending",
            }
    print(f"Hash map initialized with {len(pdf_files_map)} PDF files.")

    # 5. Scan and process by iterating over the Hash Map keys and values
    for filename, metadata in pdf_files_map.items():
        print(f"Processing key[{filename}] with path: {metadata['full_path']}")

        # Execute our working chunking pipeline
        extract_and_chunk_pdf(metadata["full_path"])

        # Update the hash map status when done (useful for production tracking)
        metadata["status"] = "Completed"

    print("Hash map directory scanning completed successfully!")
