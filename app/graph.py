from .state import GraphState
from .node import retriever_node, grade_node, generate_answer_node
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from .route import router_node

graph_builder = StateGraph(GraphState)

graph_builder.add_node("retriever_node",retriever_node)
graph_builder.add_node("grade_node",grade_node)
graph_builder.add_node("generate_answer_node",generate_answer_node)

graph_builder.add_edge(START,"retriever_node")
graph_builder.add_edge("retriever_node","grade_node")

graph_builder.add_conditional_edges(
    "grade_node",
    router_node,
    {
        "retriever_node":"retriever_node",
        "generate_answer_node":"generate_answer_node"
    }
)

graph_builder.add_edge("generate_answer_node",END)

graph = graph_builder.compile(checkpointer=MemorySaver())