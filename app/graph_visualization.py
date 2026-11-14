from .graph import graph
import yaml

with open("./config/config.yaml",'r') as f:
    config = yaml.safe_load(f)

graph_image = graph.get_graph().draw_mermaid_png()

with open(config['graph_image_path'], "wb") as f:
    f.write(graph_image)