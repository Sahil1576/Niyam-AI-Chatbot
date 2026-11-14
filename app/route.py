from .state import GraphState
from LogHandler.logger import logging
from LogHandler.custome_exception import CustomException
import sys


def router_node(state:GraphState) -> str:

    try:

        decision = state.decision

        if decision == "rewrite":
            return "retriever_node"

        elif decision == "relevant":
            return "generate_answer_node"

        else:
            return "generate_answer_node"

    except Exception as e:
        logging.exception(f"Unexpected Error : {e}")
        raise CustomException(e, sys)