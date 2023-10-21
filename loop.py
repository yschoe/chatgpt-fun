import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from graphviz import Digraph

def count_loops(adj_matrix, k):
    n = len(adj_matrix)
    graph = nx.DiGraph()

    # Create a graph from the adjacency matrix
    for i in range(n):
        for j in range(n):
            if adj_matrix[i][j] == 1:
                graph.add_edge(i, j)

    # Count loops of k hops
    loop_count = 0
    for node in graph.nodes():
        for path in nx.all_simple_paths(graph, source=node, target=node, cutoff=k):
            if len(path) == k + 1:
                loop_count += 1

    return loop_count

# Define the adjacency matrix (8x8 example)
n = 8
adjacency_matrix = np.array([
    [0, 1, 0, 0, 0, 0, 0, 1],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0, 0]
])

# Set up Graphviz for visualization
dot = Digraph(comment='Directed Graph')
for i in range(n):
    for j in range(n):
        if adjacency_matrix[i][j] == 1:
            dot.edge(str(i), str(j))

# Visualize the graph
dot.render('directed_graph')

# Count loops for different values of k
for k in range(1, n + 1):
    loop_count = count_loops(adjacency_matrix, k)
    print(f"Loops of {k} hops: {loop_count}")

# Uncomment the line below to view the generated graph visualization
dot.view()
