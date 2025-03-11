import networkx as nx

def apply_louvain_community_detection(G_super):
    """
    Applies Louvain community detection on the supergraph.

    Parameters:
    - G_super: Weighted NetworkX graph (Supergraph)

    Returns:
    - communities: Dictionary mapping nodes to community labels
    """
    partition = nx.community.louvain_communities(G_super, weight='weight', max_level=10)
    return partition

def write_community_detection_result(communities, file_name):
    """
    Writes the community detection result to a file.
    """
    # csvファイルに書き込む
    with open(file_name, "w") as f:
        for i, community in enumerate(communities):
            # nodeのidをカンマ区切りで書き込む
            f.write(",".join(community))
            f.write("\n")
