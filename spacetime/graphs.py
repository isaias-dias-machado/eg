import networkx as nx

from spacetime.ast import RecvEventRefined, RefinedAst, SendEventRefined

graph = nx.DiGraph()

def generate_cfg(ast: RefinedAst):
    events_list = ast.history.events
    for event in events_list:
        match event:
            case SendEventRefined(temporal_pos):
                graph.add_node(event, label=f"Send {temporal_pos}")
            case RecvEventRefined(temporal_pos):
                graph.add_node(event, label=f"Recv {temporal_pos}")



