from dotenv import load_dotenv
load_dotenv()

import os
import yaml
from langchain_groq import ChatGroq
from .prompt import SYSTEM_PROMPT, GRADE_PROMPT, CATEGORY_PROMPT
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from LogHandler.custome_exception import CustomException
from LogHandler.logger import logging
import sys
from .state import GraphState

with open("./config/config.yaml","r") as f:
    config = yaml.safe_load(f)

llm = ChatGroq(
    model=config['openai_model_name']
)

structured_llm = llm.with_structured_output(
    schema=GraphState,
    method="json_mode"
)

vectorstore = Chroma(
    collection_name=config['collection_name'],
    persist_directory=config['persist_directory'],
    embedding_function=HuggingFaceEmbeddings(
        model=config['embedding_model_name']
    )
)

def query_category_node(state:GraphState) -> dict:

    try:
        query = state.original_question

        category = [
            'Compounding_of_Contraventions_under_FEMA',
            'Deposits_and_Accounts',
            'External_Commercial_Borrowings_Trade_Credits_and_Structured_Obligations',
            'Foreign_Investment_in_India',
            'Insurance',
            'Money_Transfer_Service_Scheme',
            'Overseas_Investment'
        ]

        prompt = CATEGORY_PROMPT

        logging.info("Indentifying query category...")

        response = structured_llm.invoke(prompt.format(**{
            "categories":category,
            "query":query
        }))

        return {
            "original_question":response.original_question,
            "categories":response.categories
        }
    
    except Exception as e:
        logging.error(f"Unexpected Error : {e}")
        raise CustomException(e, sys)

        

def retriever_node(state:GraphState) -> dict:

    try:

        query = state.original_question if state.retry == 0 else state.question

        category = state.categories

        if not os.path.exists(config['persist_directory']):
            logging.error("Vector Database not found!")
            raise FileNotFoundError("Vector Database not found!")


        if vectorstore._collection.count() == 0:
            logging.info("Vector Database has no any records!")
            raise ValueError("Vector Database has no any records!")

        logging.info(msg="Finding query relavant chunks from the VectorDB...")

        results = vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=config['top_k'],
            filter={
                "category":{
                    "$in":category
                }
            }
        )

        documents = []
        grades = []

        for doc, grade in results:

            documents.append(doc)
            grades.append(grade)

        context = "\n\n".join(
            doc.page_content for doc in documents
        )

        if state.retry == 0:
            return {
                "original_question":query,
                "documents":documents,
                "context":context,
                "grades":grades
            }
        else:
            return {
                "question":query,
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

        query = state.original_question if state.retry == 0 else state.question
        grade = state.grades
        documents = state.documents
        context = state.context
        retry = state.retry

        prompt = GRADE_PROMPT

        logging.info(msg="Checking chunks relavance score is >= 0.5...")

        response = structured_llm.invoke(prompt.format(**{
            "original_question":query,
            "documents":documents,
            "context":context,
            "retrieval_scores":grade
        }))

        if response.relavance_score >= 0.5 and response.decision == "relevant":
            logging.info("context is more relavant to the question.")
            return {
                "decision": response.decision,
                "relavance_score": response.relavance_score,
                "documents": state.documents,
                "context": state.context
            }
        
        else:
            if retry < 2:
                logging.info("context is less relavant to the question.")
                return{
                    "decision":response.decision,
                    "relavance_score":response.relavance_score,
                    "question":response.question,
                    "retry":retry + 1
                }
            else:
                logging.info(f"context is not found for the {state.original_question}")
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

        category = state.categories
        decision = state.decision

        documents = state.documents
        context = state.context

        retriever_score = state.grades
        grade_relavance_score = state.relavance_score

        if category == ["OTHER"]:
            return {
                "generated_answer": (
                    "Sorry, I can only answer questions related "
                    "to the available RBI and financial regulatory guidelines."
                ),
                "retry": 0,
                "question": "",
                "grades": []
            }

        if decision == "not_found":
            return {
                "generated_answer": (
                    "Sorry, I couldn't find relevant information "
                    "to answer your question in the available documents."
                ),
                "retry": 0,
                "question": "",
                "grades": []
            }

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

        answer_relevance = responce.evaluation.answer_relevance
        faithfulness = responce.evaluation.faithfulness
        completeness = responce.evaluation.completeness

        overall_score = round((answer_relevance + faithfulness + completeness) / 3,ndigits=2)


        return {
            "generated_answer":responce.generated_answer,
            "source":responce.source,
            "evaluation":responce.evaluation,
            "overall_score":overall_score
        }
    
    except KeyError as e:
        logging.exception("Required key missing in GraphState.")
        raise CustomException(e, sys) from e

    except Exception as e:
        logging.exception("Error occurred in Generate Answer Node.")
        raise CustomException(e, sys) from e
