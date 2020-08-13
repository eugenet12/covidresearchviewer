import numpy as np
import random
from scipy.spatial.distance import cdist, cosine

CORPUS_BASELINE = 0.5022927110761003 # this is the baseline for df_covid_with_text

def get_average_pairwise_distance(df, n=1000):
    """Get average pairwise distance for a group of embeddings. Smaller number means closer together.
    
    With n=1000, this function is generally precise within 0.01

    Parameters
    ----------
    df: DataFrame
        input data
    n: int
        number of random pairs to calculate distances for
    
    Returns
    -------
    float
        the average pairwise cosine distance between the random pairs in df

    """
    l1 = range(len(df))
    l2 = range(len(df))
    distances = []
    for i in range(n):
        i1, i2 = random.choice(l1), random.choice(l2)
        distances.append(cosine(df["embedding"].iloc[i1], df["embedding"].iloc[i2]))
    return np.mean(distances)