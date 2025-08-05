from constants import CIT_HEP_PH_DIR_PATH as DATA_DIR_PATH  # データ変更
import data_process.CitHepPh as data_process  # データ変更


DATASET_NAME = data_process.DATASET_NAME


def get_community_detection_result(timestamp: int):
    """
    Get the community detection (DynaMo) result from the csv file.
    """
    # ファイルから読み込む
    fname = f"{DATA_DIR_PATH}coms/runDynamicModularity_{DATASET_NAME}_com_{timestamp}_nodes.csv"

    communities = []
    with open(fname, "r") as f:
        for line in f:
            # 各行が各communitiyに属するnode_idがカンマ区切りで記載されている
            community = line.strip().split(",")
            communities.append(set(community))

    return communities
