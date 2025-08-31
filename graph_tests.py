from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx

from program_searcher.program_model import Program, Statement

warm_start_program = Program(program_name="test", program_arg_names=["a", "b", "d"])
warm_start_program.insert_statement(Statement(["a", "b"], func="sub"))  # x1
warm_start_program.insert_statement(Statement(["a"], func="negate"))  # x2
warm_start_program.insert_statement(Statement(["a", "x2"], func="mul"))  # x3
warm_start_program.insert_statement(Statement(["x1", "x3"], func="mul"))  # x4
warm_start_program.insert_statement(Statement(["a", "b"], func="add"))  # x4

warm_start_program.insert_statement(Statement(["x4"], func="return"))

warm_start_program.generate_code()
print(warm_start_program.program_str)

H = warm_start_program.generate_graph()


def plot_graph_top_down(G: nx.DiGraph):
    levels = defaultdict(list)
    node_levels = {}

    # topologicznie od końca (reverse)
    for n in reversed(list(nx.topological_sort(G))):
        d = G.nodes[n]
        successors = list(G.successors(n))
        if not successors:  # brak następników → return / output
            node_levels[n] = 0
        else:
            node_levels[n] = min(node_levels[s] for s in successors) - 1
        levels[node_levels[n]].append(n)

    # przesuwamy poziomy tak, żeby najniższy był na 0
    min_level = min(node_levels.values())
    for n in node_levels:
        node_levels[n] -= min_level
    levels = defaultdict(list)
    for n, lvl in node_levels.items():
        levels[lvl].append(n)

    pos = {}
    for lvl, nodes in levels.items():
        x_spacing = 0.0005
        y = lvl * 2
        for i, n in enumerate(nodes):
            x = i * x_spacing
            pos[n] = (x, y)

    # rysowanie
    plt.figure(figsize=(10, 6))
    nx.draw(
        G, pos, with_labels=False, node_color="lightblue", arrows=True, node_size=2000
    )
    node_labels = {n: d.get("label", n) for n, d in G.nodes(data=True)}

    nx.draw_networkx_labels(
        G, pos, labels=node_labels, font_color="black", font_size=12
    )
    edge_labels = {(u, v): d.get("arg_pos", "") for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("computation_graph_manual.png", dpi=300)


plot_graph_top_down(H)
