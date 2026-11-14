from dotenv import load_dotenv
load_dotenv()

import os
import yaml
from langchain_groq import ChatGroq
from .prompt import SYSTEM_PROMPT, GRADE_PROMPT
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from LogHandler.custome_exception import CustomException
from LogHandler.logger import logging
import sys
from .state import GraphState

with open("./config/config.yaml","r") as f:
    config = yaml.safe_load(f)

llm = ChatGroq(
    model=config['groq_model_name']
)

structured_llm = llm.with_structured_output(
    schema=GraphState,
    method="json_mode"
)

        

def retriever_node(state:GraphState) -> dict:

    try:

        query = state.original_question if state.retry == 0 else state.question

        if not os.path.exists(config['persist_directory']):
            logging.error("Vector Database not found!")
            raise FileNotFoundError("Vector Database not found!")

        logging.info("Loading existing VectorDB...")

        vectorstore = Chroma(
            collection_name=config['collection_name'],
            persist_directory=config['persist_directory'],
            embedding_function=HuggingFaceEmbeddings(
                model=config['embedding_model_name']
            )
        )

        if vectorstore._collection.count() == 0:
            logging.info("Vector Database has no any records!")
            raise ValueError("Vector Database has no any records!")

        logging.info(msg="Finding query relavant chunks from the VectorDB...")

        results = vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=config['top_k']
        )

        documents = []
        grades = []

        for doc, grade in results:

            documents.append(doc)
            grades.append(grade)

        context = "\n\n".join(
            doc.page_content for doc in documents
        )

        return {
            "original_question":query,
            "documents":documents,
            "context":context,
            "grades":grades
        }

    except Exception as e:
        logging.error(f"Unexpected Error : {e}")
        raise CustomException(e, sys)


def grade_node(state:GraphState) -> dict:

    try:

        logging.info("Extract details from state...")

        original_question = state.original_question
        grade = state.grades
        documents = state.documents
        context = state.context
        retry = state.retry

        prompt = GRADE_PROMPT

        logging.info(msg="Checking chunks relavance score is >= 0.5...")

        response = structured_llm.invoke(prompt.format(**{
            "original_question":original_question,
            "documents":documents,
            "context":context,
            "retrieval_scores":grade
        }))

        if response.relavance_score >= 0.4 and response.decision == "rewrite":
            logging.info("context is more relavant to the question.")
            return {
                "decision": response.decision,
                "relavance_score": response.relavance_score,
                "question": state.original_question,
                "documents": state.documents,
                "context": state.context
            }
        
        else:
            if retry <= 2:
                logging.info("context is less relavant to the question.")
                return{
                    "decision":response.decision,
                    "relavance_score":response.relavance_score,
                    "question":response.question,
                    "retry":retry + 1
                }
            else:
                logging.info(f"context is not found for the {original_question}")
                return{
                    "decision":"Not Found",
                    "generated_answer":"Sorry, no relevant information found in the provided documents."
                }
    except Exception as e:
        logging.error(f"Unexpected Error : {e}")
        CustomException(e,sys)



def generate_answer_node(state:GraphState) -> dict:

    try:

        original_question = state.original_question
        rewritten_question = state.question

        documents = state.documents
        context = state.context

        retriever_score = state.grades
        grade_relavance_score = state.relavance_score

        prompt = SYSTEM_PROMPT

        logging.info("Fully final answer is generating...")

        responce = structured_llm.invoke(prompt.format(**{
            "original_question":original_question,
            "rewritten_question":rewritten_question,
            "documents":documents,
            "context":context,
            "retrieval_scores":retriever_score,
            "relevance_score":grade_relavance_score
        }))


        return {
            "generated_answer":responce.generated_answer,
            "source":responce.source,
            "evaluation":responce.evaluation,
            "overall_score":responce.overall_score
        }
    
    except KeyError as e:
        logging.exception("Required key missing in GraphState.")
        raise CustomException(e, sys) from e

    except Exception as e:
        logging.exception("Error occurred in Generate Answer Node.")
        raise CustomException(e, sys) from e