from .state import GraphState
from .node import retriever_node, grade_node, generate_answer_node, query_category_node
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from .route import router_after_grade_node, router_after_query_node

graph_builder = StateGraph(GraphState)

graph_builder.add_node("query_category_node",query_category_node)
graph_builder.add_node("retriever_node",retriever_node)
graph_builder.add_node("grade_node",grade_node)
graph_builder.add_node("generate_answer_node",generate_answer_node)

graph_builder.add_edge(START,"query_category_node")

graph_builder.add_conditional_edges(
    "query_category_node",
    router_after_query_node,
    {
        "generate_answer_node":"generate_answer_node",
        "retriever_node":"retriever_node"
    }
)
graph_builder.add_edge("retriever_node","grade_node")

graph_builder.add_conditional_edges(
    "grade_node",
    router_after_grade_node,
    {
        "retriever_node":"retriever_node",
        "generate_answer_node":"generate_answer_node"
    }
)

graph_builder.add_edge("generate_answer_node",END)

graph = graph_builder.compile(checkpointer=MemorySaver())