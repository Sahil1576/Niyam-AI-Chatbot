# RUN ONLY ONCE BECAUSE OF IT CREATE VECTOR DATABASE USING PDF's SPLITTED CHUNKS.


from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
import sys
import os
from LogHandler.logger import logging
from LogHandler.custome_exception import CustomException
from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib
import yaml


files = ['Compounding_of_Contraventions_under_FEMA.pdf','Diposits_and_Accounts.pdf',
         'External_Commercial_Borrowings_Trade_Credits_and_Structured_Obligations.pdf',
         'Foreign_Investment_in_India.pdf','Insurance.pdf','Money_Transfer_Service_Scheme.pdf',
         'Overseas_Investment.pdf']


class IngestConfig:

    def __init__(self):
        with open(file="./config/config.yaml", mode="r") as f:
            config = yaml.safe_load(f)

        self.chunk_size = config['chunk_size']
        self.chunk_overlap = config['chunk_overlap']

        self.pdf_directory_path = config['pdf_directory_path']
        self.persist_directory = config['persist_directory']
        self.collection_name = config['collection_name']

        self.embedding_model_name = config['embedding_model_name']

        
class Ingest:

    def __init__(self):
        self.config = IngestConfig()

    def text_splitter(self, documents:list[dict]):

        # creating splitter that split the documnets
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        
        # split the documnets and create chunks
        chunks = splitter.split_documents(
            documents=documents
        )

        return chunks



    def generate_chunk_id(source, page, content):

        unique_string = f"{source}_{page}_{content}"

        chunk_id = hashlib.md5(
            unique_string.encode()
        ).hexdigest()

        return chunk_id


    def create_vectoredb(self, files:list):
        """
        Creates and persists a ChromaDB vector database from multiple PDF files.

        This function loads PDF documents from the data directory,
        splits them into smaller text chunks, generates vector
        embeddings using a HuggingFace model, and stores them
        in a persistent ChromaDB collection for semantic search.

        Args:
            files (list): List of PDF filenames to process.

        Returns:
            Chroma: A ChromaDB vector store containing document
            embeddings, text chunks, and metadata such as
            PDF source and page number.

        Raises:
            ValueError: If no text chunks are generated.
            OSError: If a PDF file cannot be accessed or
            the embedding model fails to load.
        """
        try:

            logging.info("Checking chromadb is available or not...")

            if os.path.exists(self.config.persist_directory):
                
                vectorstore = Chroma(
                    collection_name=self.config.collection_name,
                    embedding_function=HuggingFaceEmbeddings(
                        model_name=self.config.embedding_model_name
                    ),
                    persist_directory=self.config.persist_directory
                )

                count = vectorstore._collection.count()

                if count > 0:
                    logging.info("VectorDB have already data, Don't need to create.")
                    return {
                        "message":"VectorDB have already data, Don't need to create.",
                        "collection":count
                    }

            documents = []

            pdf_directory = self.config.pdf_directory_path

            logging.info(msg="Reading all pdf's content.")

            for file in files:

                pdf_path = os.path.join(pdf_directory, file)

                if not os.path.exists(pdf_path):
                    logging.info(msg=f"{file} Not Found!")
                    raise FileNotFoundError("No pdf Documents Found!")

                # read pdf
                data = PyPDFLoader(pdf_path)

                # load pdf
                doc = data.load()

                # extend pdf document in documents
                documents.extend(doc)

            logging.info(msg="Creating text splitter and split the documents.")

            # creating splitter that split the documnets
            chunks = self.text_splitter(documents=documents)

            # Generate Stable Chunks ID's
            chunk_ids = []

            for chunk in chunks:

                source = chunk.metadata["source"]
                page = chunk.metadata["page"]
                content = chunk.page_content

                chunk_id = self.generate_chunk_id(
                    source,
                    page,
                    content
                )

                chunk_ids.append(chunk_id)


            logging.info(msg="Loading HuggingFaceEmbeddings model.")
                
            # using hugging face embedding model
            embedding_model = HuggingFaceEmbeddings(
                model_name=self.config.embedding_model_name
            )
            
            logging.info(msg="Creating ChromaDB database and save content it.")

            if not chunks:
                raise ValueError("No chunks found!")

            # create persist directory for vectorDB
            PERSIST_DIRECTORY = self.config.persist_directory

            # create vectorstore database
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embedding_model,
                persist_directory=PERSIST_DIRECTORY,
                collection_name=self.config['collection_name'],
                ids=chunk_ids
            )


        except OSError as e:
            logging.exception("Vector database creation failed.")
            raise CustomException(e, sys) from e

# if __name__ == "__main__":
#     import warnings
#     warnings.filterwarnings("ignore")
#     from rich import print

#     vectorstore = Chroma(
#         collection_name="Niyam_AI_Chatbot",
#         embedding_function=HuggingFaceEmbeddings(
#             model_name="sentence-transformers/all-MiniLM-L6-v2"
#         ),
#         persist_directory="./chromadb"
#     )

#     answer = vectorstore.similarity_search(
#         query="What is the minimum Net Owned Funds requirement for an Indian Agent?",
#         k=5
#     )

#     print(f"Answer : {answer}")

    # ing = Ingest()
    # print(ing.create_vectoredb(files=files))