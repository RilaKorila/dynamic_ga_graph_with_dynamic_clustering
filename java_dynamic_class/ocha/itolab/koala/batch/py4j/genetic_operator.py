import random


def single_point_crossover(gene1, gene2):
    """
    1つの遺伝子から、ランダムでnodeの座標を選択する。
    他方の遺伝子の同じ位置のnodeとその座標情報を交換する
    """
    random_x = random.randint(0, len(gene1) - 2)
    random_y = random_x + 1

    tmp_x, tmp_y = (
        gene1[random_x],
        gene1[random_y],
    )
    gene1[random_x] = gene2[random_x]
    gene1[random_y] = gene2[random_y]
    gene2[random_x] = tmp_x
    gene2[random_y] = tmp_y

    return gene1, gene2
