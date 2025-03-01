import networkx as nx
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from collections import deque
import groq

# Set Groq API key (Make sure to use environment variables for security)
os.environ["GROQ_API_KEY"] = "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"
groq_client = groq.Groq()

class GraphRAGExcelChatbot:
    def __init__(self):
        # Initializes an empty graph and data storage.
        self.graph = nx.Graph()
        self.data = {}

    def upload_and_process(self, file):
        # Uploads an Excel file and processes it into a structured knowledge graph.
        excel_file = pd.ExcelFile(file)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file, sheet_name=sheet_name)
            self.data[sheet_name] = df

            # Add sheet as a node
            self.graph.add_node(sheet_name, type="sheet")

            # Add column nodes & establish relationships
            for column in df.columns:
                col_node = f"{sheet_name}_{column}"
                self.graph.add_node(col_node, type="column")
                self.graph.add_edge(sheet_name, col_node, relation="contains")

                # Add value nodes (limit per column for efficiency)
                for value in df[column].dropna().unique():
                    value_node = f"{column}_{value}"
                    self.graph.add_node(value_node, type="value")
                    self.graph.add_edge(col_node, value_node, relation="has_value")

    def visualize_graph(self):
        # Displays a structured knowledge graph.
        plt.figure(figsize=(14, 10))

        pos = nx.spring_layout(self.graph, k=0.5, seed=42)

        node_colors = []
        for node in self.graph.nodes:
            node_type = self.graph.nodes[node].get("type", "")
            if node_type == "sheet":
                node_colors.append("skyblue")   # Sheets → Blue
            elif node_type == "column":
                node_colors.append("lightgreen")  # Columns → Green
            elif node_type == "value":
                node_colors.append("lightcoral")  # Values → Coral
            else:
                node_colors.append("gray")  # Unknown nodes

        nx.draw_networkx_nodes(self.graph, pos, node_color=node_colors, node_size=1600, edgecolors="black", alpha=0.9)
        nx.draw_networkx_edges(self.graph, pos, alpha=0.6, width=1.5)

        labels = {node: node if self.graph.nodes[node]["type"] != "value" else "" for node in self.graph.nodes}
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=10, font_family="Arial", font_weight="bold")

        edge_labels = nx.get_edge_attributes(self.graph, "relation")
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=8, alpha=0.7)

        plt.title("Knowledge Graph of Excel Data", fontsize=15, fontweight="bold")
        plt.savefig("graph.png")
        plt.close()

    def find_relevant_nodes(self, query):
        # Finds relevant nodes using keyword matching.
        return [node for node in self.graph.nodes if any(word.lower() in node.lower() for word in query.split())]

    def bfs_traverse(self, start_nodes):
        # Performs BFS to explore relationships and gather contextual information.
        visited = set()
        queue = deque(start_nodes)
        traversal_result = []

        while queue:
            node = queue.popleft()
            if node not in visited:
                visited.add(node)
                traversal_result.append(node)
                queue.extend(self.graph.neighbors(node))

        return traversal_result

    def ask_question(self, question):
        # Queries the graph and retrieves an answer.
        relevant_nodes = self.find_relevant_nodes(question)
        if not relevant_nodes:
            return "No relevant data found in the graph.", "No relevant nodes identified."

        traversal_path = self.bfs_traverse(relevant_nodes)
        if not traversal_path:
            return "No meaningful connections found.", "No traversal path identified."

        # Context for LLM
        context = "\n".join([f"{node} (Type: {self.graph.nodes[node]['type']})" for node in traversal_path])

        # LLM Query
        prompt = f"""
        You have structured data from an Excel file represented as a knowledge graph.
        Here are the relationships identified for the question:
        {context}

        Question: {question}
        Provide a specific, accurate answer based on the structured data and graph relationships.
        """
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.1,
        )

        return response.choices[0].message.content, context
