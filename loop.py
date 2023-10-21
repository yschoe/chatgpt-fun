# Generated with ChatGPT
# Here's the full prompt that led to this version.
#   https://chat.openai.com/share/813580a4-244c-4fb9-a8bf-8ca9bc9757c8
#

import numpy as np
import random
import networkx as nx
from graphviz import Digraph

def generate_random_adjacency_matrix(n, num_connections, min_self_connections):
    # Create an empty adjacency matrix
    adjacency_matrix = np.zeros((n, n), dtype=int)

    # Add at least min_self_connections self-connections
    for i in range(min_self_connections):
        node = random.randint(0, n - 1)
        adjacency_matrix[node][node] = 1

    # Add remaining connections
    remaining_connections = num_connections - min_self_connections
    while remaining_connections > 0:
        source = random.randint(0, n - 1)
        dest = random.randint(0, n - 1)
        if source != dest and adjacency_matrix[source][dest] == 0:
            adjacency_matrix[source][dest] = 1
            remaining_connections -= 1

    return adjacency_matrix

def count_loops(adj_matrix, k):
    n = len(adj_matrix)
    graph = nx.DiGraph()

    # Create a graph from the adjacency matrix
    for i in range(n):
        for j in range(n):
            if adj_matrix[i][j] == 1:
                graph.add_edge(i, j)

    # Count loops using nx.simple_cycles
    loop_count = 0
    for cycle in nx.simple_cycles(graph):
        if len(cycle) == k:
            loop_count += 1

    return loop_count

# Define the size of the adjacency matrix
n = 8  # Change this to the desired size
num_connections = 25
min_self_connections = 3

# Generate a random adjacency matrix with the specified properties
adjacency_matrix = generate_random_adjacency_matrix(n, num_connections, min_self_connections)

# Set up Graphviz for visualization
dot = Digraph(comment='Directed Graph')
for i in range(n):
    for j in range(n):
        if adjacency_matrix[i][j] == 1:
            dot.edge(str(i), str(j))

# Visualize the graph
dot.render('random_directed_graph')

# Count loops for different values of k
for k in range(1, n + 1):
    loop_count = count_loops(adjacency_matrix, k)
    print(f"Loops of {k} hops: {loop_count}")

# Uncomment the line below to view the generated graph visualization
dot.view()
