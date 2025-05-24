from constants import FACEBOOK_DIR_PATH

def get_community_detection_result(timestamp: int):
    """
    Get the community detection (DynaMo) result from the csv file.
    """
    # ファイルから読み込む
    # fname = f"{FACEBOOK_DIR_PATH}coms/runDynamicModularity_Cit-HepPh_com_{timestamp}_nodes.csv"
    fname = f"{FACEBOOK_DIR_PATH}coms/runDynamicModularity_facebook_com_{timestamp}_nodes.csv"

    communities = []
    with open(fname, "r") as f:
        for line in f:
            # 各行が各communitiyに属するnode_idがカンマ区切りで記載されている
            community = line.strip().split(",")
            communities.append(set(community))
    
    return communities
