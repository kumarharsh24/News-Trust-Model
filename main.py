import numpy as np
import pandas as pd
import heapq
from collections import defaultdict
from urllib.parse import urlparse
import streamlit as st
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
from st_link_analysis.component.icons import SUPPORTED_ICONS
import Tokenizer_Trie as tk_t
import web_scrapper as ws

DEPTH_THRESHOLD = 5
INFLUENCE = 0.85

def is_valid_url(url):
    return isinstance(url, str) and url.startswith(('http://', 'https://'))

def get_site(url):
    if is_valid_url(url):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]

        if domain.startswith("edition"): #cnn is edition.cnn
            domain = domain[8:]
        
        return domain.split('.')[0].lower()
    
    else:
        return ""

# Class for Graph Nodes
class GraphNode:
    def __init__(self, name, score):
        self.site_name = name
        self.score = round(score, 2)
        self.T_node = -1
        self.depth = 0

# Class for Site data
class Site:
    def __init__(self, score, url, node, weight):
        self.trust_score = score
        self.url = url
        self.node = node
        self.weight = weight

# Class for Graph
class Graph:
    def __init__(self):
        self.adj_list = defaultdict(list)
        self.list_of_sites = {}
        self.start_node = None
        self.trie_obj = None
        self.Web_Search_Flag = False
        
    def __load_csv(self, path):
        data = pd.read_csv(path)
        columns = data.columns.tolist()
        data = data.set_index(columns[0])
        return data
    
    def __get_score_from_data(self, site_name):
        data = self.__load_csv("data.csv")
        if site_name in data.index:
            return data.loc[site_name.lower(), "Scores"]
        else:
            return 0.5
    
    def __append(self, site_name, url, prev_node=None, edge_weight=0):
        # get score from data.csv
        score = self.__get_score_from_data(site_name)

        # create a node, make a connection list from site and update the list of sites
        new_node = GraphNode(site_name, round(score,2))
        self.adj_list[new_node] = []
        self.list_of_sites[site_name] = Site(score, url, new_node, edge_weight)
        
        if prev_node is None:
            new_node.depth = 0
            self.start_node = new_node
        else:
            new_node.depth = prev_node.depth + 1
            self.adj_list[prev_node].append((new_node, edge_weight))

        return new_node
    
    def __create_graph(self, url, prev_node=None):
        if not is_valid_url(url):
            return
        
        else:
            site_name = get_site(url)
            
            if site_name in self.list_of_sites:
                flg = False
                for edge in self.adj_list[prev_node]:
                    if edge[0].site_name == site_name or site_name == prev_node.site_name:
                        flg = True
                        break
                if not flg:
                    self.adj_list[prev_node].append((self.list_of_sites[site_name].node, self.list_of_sites[site_name].weight))
                return
            
            else:
                data, flag = ws.get_page(url, self.Web_Search_Flag)
                self.Web_Search_Flag = flag or self.Web_Search_Flag
                weight = 0.5
                links=[]

                if len(data["headline"])>0:
                    content = data["content"]
                    weight = tk_t.compare_data(self.trie_obj, content)
                
                links = data["citations"]
                new_node = self.__append(site_name, url, prev_node, weight)
                    
                if new_node.depth < DEPTH_THRESHOLD and not (self.Web_Search_Flag and len(links)==0):
                    for link in links:
                        self.__create_graph(link, new_node)
            
    def __dfs_visit(self, node, ancestor):
        if node.T_node != -1:
            return node.T_node
        
        ancestor[node] = True
        score = INFLUENCE * node.score
        propagated_score = 0
        total_weights = 0
        
        for neighbor, weight in self.adj_list[node]:
            if neighbor in ancestor and ancestor[neighbor]:
                total_weights += weight
                propagated_score += neighbor.score
            else:
                total_weights += weight
                propagated_score += self.__dfs_visit(neighbor, ancestor) * weight
        
        if total_weights:
            score += (1 - INFLUENCE) * (propagated_score / total_weights)
        
        node.T_node = score
        ancestor[node] = False
        return score
    
    def create(self, url):
        if not is_valid_url(url):
            return
        
        data, flag = ws.get_page(url)
        self.Web_Search_Flag = flag or self.Web_Search_Flag
        links = data["citations"]
        original_news = data["content"]
        self.trie_obj = tk_t.extract_keywords(original_news, True)

        site_name = get_site(url)
        new_node = self.__append(site_name, url, None, 1)
        
        for link in links:
            if (get_site(link) != site_name):
                self.__create_graph(link, new_node)
    
    def get_score(self):
        ancestor = {}
        return self.__dfs_visit(self.start_node, ancestor)
    
    def get_top_sites(self):
        pq = [(-site.node.T_node, site.url) for site in self.list_of_sites.values()]
        heapq.heapify(pq)
        
        result = []
        i = 5
        while (i):
            if not pq:
                break
            score, url = heapq.heappop(pq)
            if url:
                i-=1
                result.append((url, -score))
        
        return result
    
    def clear_graph(self):
        self.adj_list.clear()
        self.list_of_sites.clear()
        self.start_node = None
    
    def __del__(self):
        self.clear_graph()

def graph_to_stlink_elements(graph: Graph):
    """Convert Graph instance to st_link_analysis format"""
    nodes = []
    edges = []

    for site_name, site_data in graph.list_of_sites.items():
        node = site_data.node
        nodes.append({
            "data": {
                "id": site_name,
                "label": site_name,
                "name": site_name,
                "score": f"{round(node.score, 2)}"
            }
        })

    id = 101
    for src_node, neighbors in graph.adj_list.items():
        src_name = src_node.site_name
        for dst_node, weight in neighbors:
            dst_name = dst_node.site_name
            weight = f"{round(weight, 2)}"
            id+=1
            edges.append({
                "data": {
                    "id": id,
                    "label": weight,
                    "source": src_name,
                    "target": dst_name,
                    "weight": weight
                }
            })

    return {"nodes": nodes, "edges": edges}

def update_vis_graph(graph):
    graph_data = graph_to_stlink_elements(graph)
    nodes = graph_data["nodes"] 
    edges = graph_data["edges"]
   
    # Define styles for nodes using real favicons
    node_styles = []
    for node in nodes:
        site_name = node["data"]["label"]
        node_styles.append(NodeStyle(site_name, "#309A60", "name", "news"))

    # Use the actual weight as the edge label
    edge_styles = []
    for edge in edges:
        weight = edge["data"]["label"]
        edge_styles.append(EdgeStyle(weight, labeled=True, directed=True))

    layout = {"name": "cose", "animate": "end", "nodeDimensionsIncludeLabels": False}

    st_link_analysis(
        elements={"nodes": nodes, "edges": edges},
        node_styles=node_styles,
        edge_styles=edge_styles,
        layout=layout,
        key="xyz"
    )

if __name__ == "__main__":
    st.set_page_config(page_title="News Trust", layout="wide")
    st.title("📰 News Trust")
    st.markdown("Analyze the trustworthiness of a news article using graph-based insights.")

    st.sidebar.title("📘 About News Trust")
    st.sidebar.markdown("""
    **News Trust** is an open-source Streamlit app designed to assess the **credibility of news articles** using **graph-based analysis**.
    
    ---
    
    🧠 **How it works**  
    - Analyzes **citations** and cross-references in the article  
    - Detects **content similarity** with reputable sources  
    - Uses **PageRank** over a trust graph to score trustworthiness  
    - Automatically suggests external corroborations when references are missing  
    
    ---
    
    🚀 **Why use it?**  
    - Combat misinformation with data-backed trust scores  
    - Gain visual insight into how reliable an article is  

    ---

    👨‍💻 **Project Details**  
    🛠️ **Authors**  
    - [Shreyansh Agarwal](https://github.com/Shreyansh9878)  
    - [Malav Parekh](https://github.com/b23me1029)  
    - [Ishan Rajpurohit](https://github.com/ishanrajpurohit-iitj)
    - [Kumar Harsh](https://github.com/kumarharsh24)

    ---

    💻 **GitHub**: [github.com/Shreyansh9878/News-Trust-Model](https://github.com/Shreyansh9878/News-Trust-Model)  
    📬 **Contact**: [2shreyansh@gmail.com]  
    
    ---
    🧩 *Built with [Streamlit](https://streamlit.io), powered by Python, and driven by trust in journalism.*  
    🌐 *If you like it, give it a ⭐ on GitHub and share with your community!*

    ---

    ### ⚠️ Disclaimer

    - The dataset used in this project may contain inaccuracies or biases and should not be considered a definitive source of truth.
    - Web scraping is used to extract citation and content data; however, some websites prohibit automated access in their Terms of Service. Users are responsible for ensuring compliance with such policies.
    - The trust scores and graph-based insights are **automated estimations**, not verified facts.
    - The authors are not responsible for any consequences arising from the use of this tool.
    - By using this tool, you acknowledge that you understand and accept these terms.
""")

    if st.session_state.get("reset_url_input", False):
        st.session_state.news_url_input = ""
        st.session_state.reset_url_input = False
    
    # Input
    url = st.text_input("🔗 Enter a news article URL:", key="news_url_input")

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        if url:  # Only proceed if user entered a URL
            st.session_state.url = url
            st.session_state.submitted = True
            st.rerun()
    
    else:
        url = st.session_state.url  # Pull back the URL safely
        wait_placeholder = st.empty()
        wait_placeholder.info("Processing... Please wait ⏳")
        
        graph = Graph()
        graph.create(url)

        update_vis_graph(graph)

        final_score = graph.get_score()
        top_sites = graph.get_top_sites()
        graph.clear_graph()

        wait_placeholder.empty()

        st.markdown(f"### ✅ Final Trust Score: `{round(final_score, 2)*100}%`")
        
        st.markdown("### 🌐 Top Referenced Sites")
        for site in top_sites:
            st.markdown(f"- [{get_site(site[0])}]({site[0]}) — Score: **{round(site[1], 2)*100}%**")

        if st.button("🔁 Analyze another URL"):
            st.session_state.submitted = False
            st.session_state.url = ""
            st.session_state.reset_url_input = True
            st.rerun()