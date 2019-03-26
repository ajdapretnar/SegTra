import numpy as np

from gensim import corpora, models, matutils
from pandas import Series

import preprocess


def compute_sparse(x1, x2):
    xi_ind = set(x1.indices)
    union = len(xi_ind.union(x2.indices))
    return 1 - len(xi_ind.intersection(x2.indices)) / union if union else 0

def simple_distance(corpus):
    c, t = preprocess.preprocessing_pipeline(corpus)

    dictionary = corpora.Dictionary(t)

    bow = [dictionary.doc2bow(doc) for doc in t]

    # binary tfidf, nnn for count, ntn for tfidf
    # tfidf = models.TfidfModel(bow, smartirs="bnn")
    tfidf = models.TfidfModel(bow, smartirs="nnn")
    X = matutils.corpus2csc(tfidf[bow], dtype=np.float, num_terms=len(
        dictionary)).T

    chunking_index = []
    count = 0

    for i in range(X.shape[0]):
        if i < X.shape[0] - 1 and compute_sparse(X[i], X[i+1]) < 0.95:
            chunking_index.append(count)
            count += 1

        else:
            chunking_index.append(count)

    c['id'] = Series(chunking_index, index=c.index)
    c = c.groupby('id').agg({'File': lambda x: x.iloc[0],
                         'Content': '\n'.join})
    return c
