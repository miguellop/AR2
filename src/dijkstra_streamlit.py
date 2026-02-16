import random
import string
import heapq
import math

import matplotlib.pyplot as plt
import streamlit as st


def format_pair(distance, predecessor):
    distance_text = "∞" if distance == float("inf") else str(int(distance))
    predecessor_text = predecessor if predecessor is not None else "-"
    return f"{distance_text}, {predecessor_text}"


def strike_text(text: str):
    return "".join(f"{char}\u0336" for char in text)


def get_node_positions(nodes):
    n = len(nodes)
    pos = {}
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n
        pos[node] = (math.cos(angle), math.sin(angle))
    return pos


def segment_intersection_t(p1, p2, p3, p4, eps=1e-9):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    rx, ry = x2 - x1, y2 - y1
    sx, sy = x4 - x3, y4 - y3
    den = rx * sy - ry * sx
    if abs(den) < eps:
        return None

    qpx, qpy = x3 - x1, y3 - y1
    t = (qpx * sy - qpy * sx) / den
    u = (qpx * ry - qpy * rx) / den

    if eps < t < 1 - eps and eps < u < 1 - eps:
        return t
    return None


def pick_label_t(crossing_ts):
    candidates = [0.5, 0.35, 0.65, 0.2, 0.8]
    safe_margin = 0.1

    for t in candidates:
        if all(abs(t - c) >= safe_margin for c in crossing_ts):
            return t

    if not crossing_ts:
        return 0.5

    return max(candidates, key=lambda t: min(abs(t - c) for c in crossing_ts))


def dijkstra_with_steps(graph: dict[str, dict[str, int]], start: str, node_order: list[str]):
    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    settled = set()
    distances[start] = 0
    steps = []
    visual_steps = []

    def format_cell(node):
        return format_pair(distances[node], previous[node])

    def format_settled():
        if not settled:
            return "{}"
        return "{" + ", ".join(sorted(settled)) + "}"

    priority_queue = [(0, start)]
    step_number = 0

    while priority_queue and len(settled) < len(graph):
        current_distance, current_node = heapq.heappop(priority_queue)
        if current_node in settled:
            continue
        if current_distance > distances[current_node]:
            continue

        settled.add(current_node)
        updated = {}
        eliminated = {}

        for neighbor, weight in graph[current_node].items():
            if neighbor in settled:
                continue
            candidate = current_distance + weight
            if candidate < distances[neighbor]:
                old_pair = format_pair(distances[neighbor], previous[neighbor])
                distances[neighbor] = candidate
                previous[neighbor] = current_node
                heapq.heappush(priority_queue, (candidate, neighbor))
                new_pair = format_pair(distances[neighbor], previous[neighbor])
                updated[neighbor] = new_pair
                if old_pair != "∞, -":
                    eliminated[neighbor] = old_pair

        row = {"Paso": step_number, "Definitivos": format_settled(), "_settled_nodes": tuple(sorted(settled))}
        for node in node_order:
            row[node] = format_cell(node)
        steps.append(row)
        visual_steps.append(
            {
                "step": step_number,
                "current_node": current_node,
                "settled_nodes": tuple(sorted(settled)),
                "pairs": {node: format_cell(node) for node in node_order},
                "updated": updated,
                "eliminated": eliminated,
            }
        )
        step_number += 1

    return distances, previous, steps, visual_steps


def build_path_from_previous(previous, source, target):
    path = []
    current = target
    while current is not None:
        path.append(current)
        if current == source:
            break
        current = previous[current]

    if not path or path[-1] != source:
        return []
    return list(reversed(path))


def build_routing_table(nodes, source, distances, previous):
    rows = []
    for destination in nodes:
        if destination == source:
            continue
        path = build_path_from_previous(previous, source, destination)
        if not path:
            rows.append(
                {
                    "Destino": destination,
                    "Siguiente salto": "-",
                    "Costo total": "∞",
                    "Ruta": "No alcanzable",
                }
            )
            continue

        next_hop = path[1] if len(path) > 1 else "-"
        cost = distances[destination]
        rows.append(
            {
                "Destino": destination,
                "Siguiente salto": next_hop,
                "Costo total": int(cost) if cost != float("inf") else "∞",
                "Ruta": " -> ".join(path),
            }
        )
    return rows


def build_aggregated_next_hop_table(routing_rows):
    groups = {}
    for row in routing_rows:
        next_hop = row["Siguiente salto"]
        destination = row["Destino"]
        if next_hop not in groups:
            groups[next_hop] = []
        groups[next_hop].append(destination)

    aggregated = []
    for next_hop in sorted(groups.keys()):
        destinations = sorted(groups[next_hop])
        aggregated.append(
            {
                "Destino(s)": ", ".join(destinations),
                "Siguiente salto": next_hop,
                "_count": len(destinations),
            }
        )

    aggregated.sort(key=lambda row: (row["_count"], row["Siguiente salto"]))
    if aggregated:
        aggregated[-1]["Destino(s)"] = "default"

    for row in aggregated:
        row.pop("_count", None)
    return aggregated


def generate_connected_graph(num_nodes: int, connectivity_level: int):
    nodes = list(string.ascii_lowercase[:num_nodes])
    graph = {node: {} for node in nodes}
    edges = []

    # Primero se garantiza conectividad con un arbol aleatorio.
    connected = [nodes[0]]
    for node in nodes[1:]:
        neighbor = random.choice(connected)
        weight = random.randint(1, 10)
        graph[node][neighbor] = weight
        graph[neighbor][node] = weight
        edges.append((node, neighbor, weight))
        connected.append(node)

    min_edges = num_nodes - 1
    max_edges = num_nodes * (num_nodes - 1) // 2
    target_edges = round(min_edges + (connectivity_level / 100) * (max_edges - min_edges))
    target_edges = max(min_edges, min(target_edges, max_edges))
    existing = {tuple(sorted((u, v))) for u, v, _ in edges}

    while len(edges) < target_edges:
        u, v = random.sample(nodes, 2)
        key = tuple(sorted((u, v)))
        if key in existing:
            continue
        existing.add(key)
        weight = random.randint(1, 10)
        graph[u][v] = weight
        graph[v][u] = weight
        edges.append((u, v, weight))

    return nodes, edges, graph


def draw_graph(nodes, edges, source=None, tree_edges=None):
    pos = get_node_positions(nodes)

    tree_edges = tree_edges or []
    tree_edges = {tuple(sorted(edge)) for edge in tree_edges}
    edge_points = [(u, v, w, pos[u], pos[v]) for u, v, w in edges]

    fig, ax = plt.subplots(figsize=(8, 6))
    for i, (u, v, w, p1, p2) in enumerate(edge_points):
        x1, y1 = p1
        x2, y2 = p2
        is_tree_edge = tuple(sorted((u, v))) in tree_edges
        ax.plot(
            [x1, x2],
            [y1, y2],
            color="#ff6b6b" if is_tree_edge else "#7a7a7a",
            linewidth=3.0 if is_tree_edge else 1.8,
            zorder=1,
        )
        crossing_ts = []
        for j, (u2, v2, _w2, q1, q2) in enumerate(edge_points):
            if i == j:
                continue
            if {u, v} & {u2, v2}:
                continue
            t = segment_intersection_t(p1, p2, q1, q2)
            if t is not None:
                crossing_ts.append(t)

        label_t = pick_label_t(crossing_ts)
        mx = x1 + (x2 - x1) * label_t
        my = y1 + (y2 - y1) * label_t

        ax.text(
            mx,
            my,
            str(w),
            fontsize=10,
            ha="center",
            va="center",
            zorder=4,
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#333333", "lw": 0.8, "alpha": 0.85},
        )

    for node in nodes:
        x, y = pos[node]
        node_color = "#8fd694" if node == source else "#cfe8ff"
        ax.scatter(x, y, s=850, color=node_color, edgecolor="#2b2b2b", zorder=2)
        if node == source:
            ax.scatter(x, y, s=1150, facecolors="none", edgecolors="#2b2b2b", linewidths=2.0, zorder=3)
        ax.text(x, y, node, fontsize=12, ha="center", va="center", zorder=3)

    ax.set_title("Grafo aleatorio con pesos (arbol de caminos minimos resaltado)")
    ax.axis("off")
    return fig


def draw_step_graph(nodes, edges, source, step_data):
    pos = get_node_positions(nodes)
    settled_nodes = set(step_data["settled_nodes"])
    current_node = step_data["current_node"]
    updated = step_data["updated"]
    eliminated = step_data["eliminated"]
    pairs = step_data["pairs"]

    fig, ax = plt.subplots(figsize=(8, 6))

    for u, v, w in edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], color="#8a8a8a", linewidth=1.6, zorder=1)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(
            mx,
            my,
            str(w),
            fontsize=9,
            ha="center",
            va="center",
            zorder=2,
            bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "#444444", "lw": 0.7, "alpha": 0.9},
        )

    for node in nodes:
        x, y = pos[node]
        if node == current_node:
            node_color = "#ffd166"
        elif node in settled_nodes:
            node_color = "#8fd694"
        elif node == source:
            node_color = "#bcd4ff"
        else:
            node_color = "#cfe8ff"

        ax.scatter(x, y, s=850, color=node_color, edgecolor="#2b2b2b", zorder=3)
        if node == source:
            ax.scatter(x, y, s=1150, facecolors="none", edgecolors="#2b2b2b", linewidths=2.0, zorder=4)
        ax.text(x, y, node, fontsize=12, ha="center", va="center", zorder=4)

        norm = math.hypot(x, y)
        if norm == 0:
            ox, oy = 0.0, -0.24
        else:
            ox, oy = (x / norm) * 0.25, (y / norm) * 0.25

        if node in eliminated:
            label = f"{strike_text(eliminated[node])}\n{updated[node]}"
            text_color = "#1f4e79"
        elif node in updated:
            label = updated[node]
            text_color = "#1f4e79"
        else:
            label = pairs[node]
            text_color = "#222222"

        ax.text(
            x + ox,
            y + oy,
            label,
            fontsize=9,
            ha="center",
            va="center",
            zorder=5,
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#555555", "lw": 0.7, "alpha": 0.95},
        )

    ax.set_title(f"Paso {step_data['step']} - Nodo seleccionado: {current_node}")
    ax.axis("off")
    return fig


def draw_expansion_tree(nodes, graph, source, previous):
    pos = get_node_positions(nodes)
    tree_edges = [(node, predecessor) for node, predecessor in previous.items() if predecessor is not None]

    fig, ax = plt.subplots(figsize=(8, 6))

    for u, v in tree_edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], color="#2c7fb8", linewidth=2.8, zorder=1)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(
            mx,
            my,
            str(graph[u][v]),
            fontsize=10,
            ha="center",
            va="center",
            zorder=2,
            bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "#2c7fb8", "lw": 0.8, "alpha": 0.95},
        )

    for node in nodes:
        x, y = pos[node]
        node_color = "#8fd694" if node == source else "#cfe8ff"
        ax.scatter(x, y, s=850, color=node_color, edgecolor="#2b2b2b", zorder=3)
        if node == source:
            ax.scatter(x, y, s=1150, facecolors="none", edgecolors="#2b2b2b", linewidths=2.0, zorder=4)
        ax.text(x, y, node, fontsize=12, ha="center", va="center", zorder=5)

    ax.set_title("Arbol de expansion generado por Dijkstra")
    ax.axis("off")
    return fig


st.set_page_config(page_title="Dijkstra en grafos", page_icon="🧭")
st.title("Algoritmo de Dijkstra sobre un grafo aleatorio")

num_nodes = st.slider("Numero de nodos", min_value=2, max_value=26, value=6, step=1)
connectivity_level = st.slider(
    "Nivel de conectividad (%)",
    min_value=0,
    max_value=100,
    value=50,
    step=5,
)

if (
    "graph_data" not in st.session_state
    or st.session_state.get("num_nodes") != num_nodes
    or st.session_state.get("connectivity_level") != connectivity_level
):
    st.session_state.graph_data = generate_connected_graph(num_nodes, connectivity_level)
    st.session_state.num_nodes = num_nodes
    st.session_state.connectivity_level = connectivity_level

if st.button("Generar nuevo grafo"):
    st.session_state.graph_data = generate_connected_graph(num_nodes, connectivity_level)

nodes, edges, graph = st.session_state.graph_data
st.caption(f"Enlaces generados: {len(edges)}")
st.pyplot(draw_graph(nodes, edges))

source = st.selectbox("Selecciona un unico nodo origen para aplicar Dijkstra", options=nodes, index=0)

distances, previous, steps, visual_steps = dijkstra_with_steps(graph, source, nodes)
tree_edges = [(node, predecessor) for node, predecessor in previous.items() if predecessor is not None]

st.success("Distancias minimas calculadas desde el nodo origen hacia todos los nodos.")

st.pyplot(draw_graph(nodes, edges, source, tree_edges))

st.subheader("Pasos del algoritmo de Dijkstra")
destination_nodes = [node for node in nodes if node != source]
definitive_step = {}
for row in steps:
    settled_nodes = set(row["_settled_nodes"])
    for node in destination_nodes:
        if node in settled_nodes and node not in definitive_step:
            definitive_step[node] = row["Paso"]

steps_view = []
for row in steps:
    view_row = {"Paso": row["Paso"], "Definitivos": row["Definitivos"]}
    for node in destination_nodes:
        if row["Paso"] <= definitive_step.get(node, float("inf")):
            view_row[f"D({node}),p({node})"] = row[node]
        else:
            view_row[f"D({node}),p({node})"] = ""
    steps_view.append(view_row)
st.dataframe(steps_view, use_container_width=True)

st.subheader("Representacion grafica secuencial de los pasos")
for step_data in visual_steps:
    st.pyplot(draw_step_graph(nodes, edges, source, step_data))

st.subheader("Arbol de expansion generado")
st.pyplot(draw_expansion_tree(nodes, graph, source, previous))

st.subheader(f"Tabla de encaminamiento del nodo origen ({source})")
routing_table = build_routing_table(nodes, source, distances, previous)
st.dataframe(routing_table, use_container_width=True)

st.subheader(f"Tabla agregada por siguiente salto del nodo origen ({source})")
aggregated_table = build_aggregated_next_hop_table(routing_table)
st.dataframe(aggregated_table, use_container_width=True)
