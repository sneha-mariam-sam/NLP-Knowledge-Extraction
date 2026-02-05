import sys
import networkx as nx


def clean_webIsALod(input_file: str, conf_threshold: float = 0.3) -> str:
    """
    Cleans the WebIsALOD raw data.
    Keeps only lines with confidence > conf_threshold and hyponyms not starting with '%'.
    Returns the path to the final processed file.
    """
    output_file = "cleaned_data.txt"
    final_file = "processed_data.txt"

    with open(input_file, "r", encoding="utf8") as f1, open(output_file, "w", encoding="utf8") as f2:
        for line in f1:
            comps = line.rstrip().rsplit(";")
            hyponym = comps[0].replace("_"," ").replace("%2F"," ").replace("+"," ")\
                               .replace("%3E"," ").replace("%27","").replace("%3D","")\
                               .replace("%24","").replace("%2B"," ").replace("%3C","")\
                               .replace("%5D"," ").strip()
            hypernym = comps[1].rsplit("\t")[0].replace("_"," ").replace("+"," ").replace("%3D","").strip()
            conf = comps[1].rsplit("\t")[1]

            try:
                conf_value = float(conf)
            except ValueError:
                continue  # skip malformed lines

            if conf_value > conf_threshold and hyponym and hyponym[0] != "%":
                f2.write(f"{hyponym}\t{hypernym}\t{conf_value}\n")

    # Sort the cleaned data
    with open(output_file, "r", encoding="utf8") as f3, open(final_file, "w", encoding="utf8") as f4:
        lines = sorted(f3.readlines())
        for line in lines:
            f4.write(line)

    return final_file


def highest_confidence(req_hyponym: str, processed_data: str) -> str:
    """
    Returns the hypernym with the highest confidence value for a given hyponym.
    """
    hyper = ""
    max_conf = -1.0

    with open(processed_data, "r", encoding="utf8") as fin:
        for line in fin:
            comps = line.rstrip().split("\t")
            hyponym, hypernym, conf = comps[0].strip(), comps[1].strip(), comps[2].strip()
            try:
                conf_value = float(conf)
            except ValueError:
                continue

            if hyponym == req_hyponym and conf_value > max_conf:
                max_conf = conf_value
                hyper = hypernym

    return hyper


def taxonomy_induction(input_file: str, processed_data: str):
    """
    Build a taxonomy graph using the highest confidence hypernym relations.
    Saves the graph as 'taxonomy.png'.
    """
    with open(input_file, "r", encoding="utf8") as fin:
        entities = [line.strip() for line in fin if line.strip()]

    G = nx.DiGraph()
    ROOT_NODE = "ROOT_ENTITY"

    # First pass: add all entities and their highest-confidence hypernym
    new_entities = entities.copy()
    for entity in new_entities:
        G.add_node(entity)
        hyper = highest_confidence(entity, processed_data)
        if not hyper:  # no hypernym found
            G.add_edge(entity, ROOT_NODE)
        else:
            G.add_edge(entity, hyper)
            if hyper not in G.nodes:
                G.add_node(hyper)

    # Remove self-loops
    G.remove_edges_from(nx.selfloop_edges(G))

    # Ensure all leaves point to root if disconnected
    for node in G.nodes:
        if len(list(G.successors(node))) == 0 and node != ROOT_NODE:
            G.add_edge(node, ROOT_NODE)

    # Save graph as PNG
    p = nx.drawing.nx_pydot.to_pydot(G)
    p.write_png("taxonomy.png")
    print(f"Taxonomy graph saved as 'taxonomy.png' with {len(G.nodes)} nodes and {len(G.edges)} edges.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError("Expected exactly 1 argument: input file")

    input_file = sys.argv[1]
    processed_data_file = clean_webIsALod("webisalod-pairs.txt")
    taxonomy_induction(input_file, processed_data_file)

# References:
# https://networkx.org/documentation/stable/tutorial.html
# https://stackoverflow.com/questions/49427638/removing-self-loops-from-undirected-networkx-graph
# https://networkx.org/documentation/stable/reference/drawing.html
# https://stackoverflow.com/questions/29586520/can-one-get-hierarchical-graphs-from-networkx-with-python-3
