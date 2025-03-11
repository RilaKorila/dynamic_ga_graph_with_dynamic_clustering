import random
from itertools import repeat

try:
    from collections.abc import Sequence
except ImportError:
    from collections import Sequence


def muSmall(individual, up, low):
    """幅の狭い擬似乱数を用いて突然変異の動きを狭める。

    :param individual: :term:`Sequence <sequence>` individual to be mutated.
    :param low: A value or a :term:`python:sequence` of values that is the lower bound of the search space.
    :param up: A value or a :term:`python:sequence` of values that is the upper bound of the search space.
    """
    size = len(individual)

    if not isinstance(low, Sequence):
        low = repeat(low, size)
    elif len(low) < size:
        raise IndexError(
            "low must be at least the size of individual: %d < %d" % (len(low), size)
        )
    if not isinstance(up, Sequence):
        up = repeat(up, size)
    elif len(up) < size:
        raise IndexError(
            "up must be at least the size of individual: %d < %d" % (len(up), size)
        )

    rand = random.random()

    for i, xl, xu in zip(range(size), low, up):
        pos = individual[i]

        if rand > 0.5:
            # 乱数を加える
            pos = pos + rand * 0.1
        else:
            # 乱数をひく
            pos = pos - rand * 0.1

        pos = min(max(pos, xl), xu)
        individual[i] = pos

    return (individual,)
