import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk
import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import pickle
import os
import heapq
import math


class GraphTool:
    def __init__(self):
        self.graph = nx.Graph()
        self.positions = {}
        self.current_node = 0
        self.map_path = "map.jpg"  # Default map path

    def add_node(self, position):
        self.graph.add_node(self.current_node, pos=position)
        self.positions[self.current_node] = position
        node_id = self.current_node
        self.current_node += 1
        return node_id

    def add_edge(self, node1, node2, weight=None):
        if node1 in self.graph and node2 in self.graph:
            if weight is None:
                # Calculate Euclidean distance if no weight specified
                x1, y1 = self.positions[node1]
                x2, y2 = self.positions[node2]
                weight = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            self.graph.add_edge(node1, node2, weight=weight)

    def _path_visualization(self, path_type, start_node, search_func, map_image_path=None, end_node=None):
        if map_image_path is None:
            map_image_path = self.map_path

        def create_visualization_window():
            new_window = tk.Toplevel()
            new_window.title(f"{path_type} Visualization")
            new_window.geometry("1200x800")

            try:
                map_image = Image.open(map_image_path)
                map_image = map_image.resize((1200, 700), Image.LANCZOS)
                map_photo = ImageTk.PhotoImage(map_image)
            except FileNotFoundError:
                messagebox.showerror("Error", "Map image not found!")
                return

            canvas = tk.Canvas(new_window, width=1200, height=700, bg="white")
            canvas.pack()

            canvas.create_image(0, 0, image=map_photo, anchor=tk.NW)

            # Visualization algorithm
            if end_node is not None:
                result_nodes, result_edges, traversal_order = search_func(start_node, end_node)
            else:
                result_nodes, result_edges, traversal_order = search_func(start_node)

            # Draw all original nodes
            for node, pos in self.positions.items():
                x, y = pos
                canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill="blue", outline="black")
                canvas.create_text(x, y - 15, text=str(node), font=("Arial", 10))

            # Draw all original edges with weights
            for edge in self.graph.edges(data=True):
                node1, node2, data = edge
                x1, y1 = self.positions[node1]
                x2, y2 = self.positions[node2]
                canvas.create_line(x1, y1, x2, y2, fill="orange", width=2)

                # Draw edge weight
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                canvas.create_text(mid_x, mid_y, text=f"{data.get('weight', ''):.2f}",
                                   font=("Arial", 8), fill="red")

            # Create a label to show current traversal information
            info_label = tk.Label(new_window, text="", font=("Arial", 12))
            info_label.pack()

            def animate_search(index=0):
                if index < len(traversal_order):
                    current_node = traversal_order[index]
                    x, y = self.positions[current_node]

                    # Update info label
                    info_label.config(text=f"{path_type}: Exploring node {current_node}")

                    # Highlight current node
                    node_highlight = canvas.create_oval(x - 9, y - 9, x + 9, y + 9, fill="red", outline="black")
                    node_text = canvas.create_text(x, y - 20, text=str(current_node),
                                                   font=("Arial", 12, "bold"), fill="red")

                    # Highlight path edges
                    path_highlights = []
                    for edge in result_edges:
                        if current_node in edge:
                            n1, n2 = edge
                            x1, y1 = self.positions[n1]
                            x2, y2 = self.positions[n2]
                            path_edge = canvas.create_line(x1, y1, x2, y2, fill="green", width=4)
                            path_highlights.append(path_edge)

                    # Schedule next animation
                    new_window.after(800, lambda: cleanup_highlights(node_highlight, node_text, path_highlights))
                    new_window.after(800, animate_search, index + 1)
                else:
                    # Final state - highlight all path nodes and edges
                    info_label.config(text=f"{path_type} Complete")
                    for node in result_nodes:
                        x, y = self.positions[node]
                        if node == end_node and path_type == "A* Search":
                            # Special star mark for A* end node
                            canvas.create_polygon(
                                x, y - 15, x + 5, y - 5, x + 15, y - 5, x + 8, y + 5,
                                   x + 12, y + 15, x, y + 10, x - 12, y + 15, x - 8, y + 5,
                                   x - 15, y - 5, x - 5, y - 5,
                                fill="gold", outline="black"
                            )
                        else:
                            canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill="gold", outline="black")
                        canvas.create_text(x, y - 15, text=str(node), font=("Arial", 10, "bold"))

                    # Highlight final path edges
                    for edge in result_edges:
                        n1, n2 = edge
                        x1, y1 = self.positions[n1]
                        x2, y2 = self.positions[n2]
                        canvas.create_line(x1, y1, x2, y2, fill="green", width=5)

            def cleanup_highlights(node_highlight, node_text, path_highlights):
                canvas.delete(node_highlight)
                canvas.delete(node_text)
                for edge in path_highlights:
                    canvas.delete(edge)

            # Start animation
            animate_search()

            canvas.image = map_photo
            return new_window

        return create_visualization_window()

    def shortest_path(self, start_node, end_node):
        try:
            # Use networkx shortest_path with edge weights
            path = nx.shortest_path(self.graph, source=start_node, target=end_node, weight='weight')
            path_edges = list(zip(path, path[1:]))

            # Modify to match other search method return signature
            return set(path), path_edges, path
        except nx.NetworkXNoPath:
            messagebox.showerror("Error", "No path exists between the nodes.")
            return set(), [], []
        except nx.NodeNotFound:
            messagebox.showerror("Error", "Selected nodes do not exist in the graph.")
            return set(), [], []

    def dijkstra(self, start_node, end_node):
        try:
            # Use Dijkstra's algorithm with path tracking
            path = nx.dijkstra_path(self.graph, source=start_node, target=end_node, weight='weight')
            path_edges = list(zip(path, path[1:]))

            # Get full traversal order
            # Modify to handle traversal order correctly
            traversal_order = [start_node]
            visited = set([start_node])

            # Use a queue for BFS-like traversal to capture order
            queue = [start_node]
            while queue:
                current = queue.pop(0)
                for neighbor in self.graph.neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        traversal_order.append(neighbor)

            return set(path), path_edges, traversal_order
        except nx.NetworkXNoPath:
            messagebox.showerror("Error", "No path exists between the nodes.")
            return set(), [], []
        except nx.NodeNotFound:
            messagebox.showerror("Error", "Selected nodes do not exist in the graph.")
            return set(), [], []

    def bfs(self, start_node, end_node):
        try:
            # Breadth-First Search
            path = list(nx.shortest_path(self.graph, source=start_node, target=end_node))
            path_edges = list(zip(path, path[1:]))

            # Full traversal order
            traversal_order = list(nx.bfs_edges(self.graph, source=start_node))
            traversal_nodes = [start_node] + [edge[1] for edge in traversal_order if edge[0] == start_node]

            return set(path), path_edges, traversal_nodes
        except nx.NetworkXNoPath:
            messagebox.showerror("Error", "No path exists between the nodes.")
            return set(), [], []
        except nx.NodeNotFound:
            messagebox.showerror("Error", "Selected nodes do not exist in the graph.")
            return set(), [], []

    def dfs(self, start_node, end_node):
        try:
            # Depth-First Search
            path = list(nx.shortest_path(self.graph, source=start_node, target=end_node))
            path_edges = list(zip(path, path[1:]))

            # Full traversal order
            traversal_order = list(nx.dfs_edges(self.graph, source=start_node))
            traversal_nodes = [start_node] + [edge[1] for edge in traversal_order if edge[0] == start_node]

            return set(path), path_edges, traversal_nodes
        except nx.NetworkXNoPath:
            messagebox.showerror("Error", "No path exists between the nodes.")
            return set(), [], []
        except nx.NodeNotFound:
            messagebox.showerror("Error", "Selected nodes do not exist in the graph.")
            return set(), [], []

    def astar_search(self, start_node, end_node):
        def heuristic(a, b):
            # Euclidean distance heuristic
            x1, y1 = self.positions[a]
            x2, y2 = self.positions[b]
            return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        try:
            path = nx.astar_path(self.graph, source=start_node, target=end_node,
                                 weight='weight', heuristic=heuristic)
            path_edges = list(zip(path, path[1:]))

            # Tracking traversal order is complex for A*, so we'll use path as traversal order
            return set(path), path_edges, path
        except nx.NetworkXNoPath:
            messagebox.showerror("Error", "No path exists between the nodes.")
            return set(), [], []
        except nx.NodeNotFound:
            messagebox.showerror("Error", "Selected nodes do not exist in the graph.")
            return set(), [], []


class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Graph Visualization Tool")
        self.graph_tool = GraphTool()

        # Enhanced node selection interface
        self.root.geometry("1300x850")

        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas frame
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Load map image
        self.map_photo = self.load_map_image("map.jpg")

        # Create canvas
        self._create_canvas()

        # Create control panel
        self._create_control_panel()

        # Bottom bar with search algorithms
        self._create_search_bar()

        # Initial mode settings
        self.reset_modes()

    def _create_search_bar(self):
        # Create a frame at the bottom for search algorithms
        search_frame = tk.Frame(self.main_frame, relief=tk.RAISED, borderwidth=1)
        search_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # Search algorithm buttons
        search_algorithms = [
            ("Shortest Path", self.find_shortest_path),
            ("Dijkstra", self.find_dijkstra_path),
            ("BFS", self.find_bfs_path),
            ("DFS", self.find_dfs_path),
            ("A* Search", self.find_astar_path)
        ]

        for name, command in search_algorithms:
            btn = tk.Button(search_frame, text=name, command=command,
                            width=10, relief=tk.RAISED)
            btn.pack(side=tk.LEFT, padx=5, pady=5)

    def _create_node_selection_dialog(self, title, search_method):
        if not self.graph_tool.graph.nodes:
            messagebox.showerror("Error", "Graph is empty")
            return

        # Create a node selection dialog
        node_selection_window = tk.Toplevel(self.root)
        node_selection_window.title(title)
        node_selection_window.geometry("300x250")

        # Available nodes
        nodes = list(self.graph_tool.graph.nodes)

        # Start node selection
        tk.Label(node_selection_window, text="Select Start Node:").pack()
        start_var = tk.StringVar(node_selection_window)
        start_var.set(nodes[0])  # default value
        start_dropdown = ttk.Combobox(node_selection_window, textvariable=start_var, values=nodes)
        start_dropdown.pack()

        # End node selection
        tk.Label(node_selection_window, text="Select End Node:").pack()
        end_var = tk.StringVar(node_selection_window)
        end_var.set(nodes[-1])  # default value
        end_dropdown = ttk.Combobox(node_selection_window, textvariable=end_var, values=nodes)
        end_dropdown.pack()

        def on_confirm():
            start = int(start_var.get())
            end = int(end_var.get())

            # Verify nodes exist in the graph
            if start not in nodes or end not in nodes:
                messagebox.showerror("Error", "Selected nodes do not exist in the graph")
                return

            # Close the selection window
            node_selection_window.destroy()

            # Visualize path
            self.graph_tool._path_visualization(
                title,
                start,
                search_method,
                "map.jpg",
                end_node=end
            )

        def on_cancel():
            node_selection_window.destroy()

        # Confirmation buttons
        button_frame = tk.Frame(node_selection_window)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Confirm", command=on_confirm).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)

    def find_shortest_path(self):
        self._create_node_selection_dialog(
            "Shortest Path",
            self.graph_tool.shortest_path
        )

    def find_dijkstra_path(self):
        self._create_node_selection_dialog(
            "Dijkstra Path",
            self.graph_tool.dijkstra
        )

    def find_bfs_path(self):
        self._create_node_selection_dialog(
            "Breadth-First Search",
            self.graph_tool.bfs
        )

    def find_dfs_path(self):
        self._create_node_selection_dialog(
            "Depth-First Search",
            self.graph_tool.dfs
        )

    def find_astar_path(self):
        self._create_node_selection_dialog(
            "A* Search",
            self.graph_tool.astar_search
        )

    def load_map_image(self, map_path):
        try:
            map_image = Image.open(map_path)
            map_image = map_image.resize((1200, 600), Image.LANCZOS)
            return ImageTk.PhotoImage(map_image)
        except FileNotFoundError:
            messagebox.showwarning("Warning", f"Map image {map_path} not found. Using blank canvas.")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Could not load map: {str(e)}")
            return None

    def _create_canvas(self):
        self.canvas = tk.Canvas(self.canvas_frame, width=1200, height=600, bg="white")
        self.canvas.pack(pady=10)

        # Scrollbars for canvas
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=self.h_scrollbar.set,
                              yscrollcommand=self.v_scrollbar.set)

        if self.map_photo:
            self.canvas.create_image(0, 0, image=self.map_photo, anchor=tk.NW)

        # Bind mouse wheel for zooming (basic implementation)
        self.canvas.bind("<MouseWheel>", self.zoom)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = tk.Label(self.canvas_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_control_panel(self):
        # Advanced control panel
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Tabbed interface for different modes
        self.notebook = ttk.Notebook(self.control_frame)
        self.notebook.pack(fill=tk.X)

        # Node Management Tab
        node_frame = tk.Frame(self.notebook)
        self.notebook.add(node_frame, text="Node Management")

        # Buttons for node management
        tk.Button(node_frame, text="Add Node", command=self.toggle_add_node).pack(side=tk.LEFT, padx=5)
        tk.Button(node_frame, text="Add Edge", command=self.toggle_add_edge).pack(side=tk.LEFT, padx=5)
        tk.Button(node_frame, text="Clear Graph", command=self.clear_graph).pack(side=tk.LEFT, padx=5)

        # Graph Management Tab
        graph_frame = tk.Frame(self.notebook)
        self.notebook.add(graph_frame, text="Graph Management")

        # Graph management buttons
        tk.Button(graph_frame, text="Save Graph", command=self.save_graph).pack(side=tk.LEFT, padx=5)
        tk.Button(graph_frame, text="Load Graph", command=self.load_graph).pack(side=tk.LEFT, padx=5)

        # Bind canvas click
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def reset_modes(self):
        self.add_node_mode = False
        self.add_edge_mode = False
        self.first_selected_node = None
        self.status_var.set("Ready")

    def toggle_add_node(self):
        self.reset_modes()
        self.add_node_mode = True
        self.status_var.set("Add Node Mode: Click on canvas to add a node")

    def toggle_add_edge(self):
        self.reset_modes()
        self.add_edge_mode = True
        self.status_var.set("Add Edge Mode: Select two nodes to connect")

    def zoom(self, event):
        # Basic zoom implementation
        scale = 1.0
        if event.delta > 0:
            scale *= 1.1
        else:
            scale /= 1.1

        # Zoom around mouse pointer
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale('all', x, y, scale, scale)

    def on_canvas_click(self, event):
        x, y = event.x, event.y

        if self.add_node_mode:
            node_id = self.graph_tool.add_node((x, y))
            self._update_canvas()
            self.status_var.set(f"Node {node_id} added at ({x}, {y})")

        elif self.add_edge_mode:
            closest_node = self._find_closest_node(x, y)
            if closest_node is not None:
                if self.first_selected_node is not None:
                    # Add edge with weight dialog
                    weight = simpledialog.askfloat("Edge Weight",
                                                   "Enter edge weight (or leave blank for auto):",
                                                   initialvalue=None)
                    self.graph_tool.add_edge(self.first_selected_node, closest_node, weight)
                    self.first_selected_node = None
                    self._update_canvas()
                    self.status_var.set(f"Edge added between nodes {self.first_selected_node} and {closest_node}")
                else:
                    self.first_selected_node = closest_node
                    self.status_var.set(f"First node selected: {closest_node}")

    def _find_closest_node(self, x, y):
        if not self.graph_tool.positions:
            messagebox.showwarning("Warning", "Add nodes first")
            return None

        return min(
            self.graph_tool.positions.keys(),
            key=lambda node: ((self.graph_tool.positions[node][0] - x) ** 2 +
                              (self.graph_tool.positions[node][1] - y) ** 2)
        )

    def save_graph(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".graph",
            filetypes=[("Graph files", "*.graph")]
        )
        if filename:
            with open(filename, 'wb') as f:
                pickle.dump((self.graph_tool.graph, self.graph_tool.positions, self.graph_tool.current_node), f)
            messagebox.showinfo("Success", f"Graph saved as {filename}")
            self.status_var.set(f"Graph saved to {filename}")

    def load_graph(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Graph files", "*.graph")]
        )
        if filename:
            try:
                with open(filename, 'rb') as f:
                    self.graph_tool.graph, self.graph_tool.positions, self.graph_tool.current_node = pickle.load(f)
                self._update_canvas()
                messagebox.showinfo("Success", f"Graph loaded from {filename}")
                self.status_var.set(f"Graph loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load graph: {str(e)}")
                self.status_var.set("Graph load failed")

    def clear_graph(self):
        # Reset graph tool completely
        self.graph_tool = GraphTool()
        self._update_canvas()
        self.status_var.set("Graph cleared")

    def _update_canvas(self):
        # Clear existing canvas content
        self.canvas.delete("all")

        # Redraw map if exists
        if self.map_photo:
            self.canvas.create_image(0, 0, image=self.map_photo, anchor=tk.NW)

        # Draw nodes
        for node, pos in self.graph_tool.positions.items():
            x, y = pos
            self.canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill="blue", outline="black")
            self.canvas.create_text(x, y - 15, text=str(node), font=("Arial", 10))

        # Draw edges with weights
        for edge in self.graph_tool.graph.edges(data=True):
            node1, node2, data = edge
            x1, y1 = self.graph_tool.positions[node1]
            x2, y2 = self.graph_tool.positions[node2]

            # Draw edge
            self.canvas.create_line(x1, y1, x2, y2, fill="orange", width=3)

            # Draw weight
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            self.canvas.create_text(mid_x, mid_y,
                                    text=f"{data.get('weight', ''):.2f}",
                                    font=("Arial", 8),
                                    fill="red")


def main():
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()