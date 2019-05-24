import numpy as np

from gensim import corpora, models, matutils
from pandas import Series

import preprocess
from sklearn.metrics.pairwise import cosine_similarity


def compute_sparse(x1, x2):
    union = len(set(x1).union(set(x2)))
    return 1 - len(set(x1).intersection(set(x2))) / union if union else 0

def aq_distance(corpus):
    c, q_t, a_t = preprocess.preprocessing_pipeline(corpus)

    chunking_index = []
    count = 0

    for i in range(len(q_t)):
        if i < len(q_t) - 1 and compute_sparse(a_t[i], q_t[i+1]) > 0.75:
            chunking_index.append(count)
            count += 1
        else:
            chunking_index.append(count)

    c['id'] = Series(chunking_index, index=c.index)
    c['Content'] = c['Questions'] + '\n' + c['Answers']
    c.drop(['Questions', 'Answers'], axis=1, inplace=True)
    c = c.groupby('id').agg({'File': lambda x: x.iloc[0], 'Content': '\n'.join})
    return c

def chunk_distance(corpus):
    c, q_t, a_t = preprocess.preprocessing_pipeline(corpus)
    c['Content'] = c['Questions'] + '\n' + c['Answers']
    c.drop(['Questions', 'Answers'], axis=1, inplace=True)
    t = [q + a for q, a in zip(q_t, a_t)]

    chunking_index = []
    count = 0

    for i in range(len(t)):
        if i < len(t) - 1 and compute_sparse(t[i], t[i + 1]) > 0.75:
            chunking_index.append(count)
            count += 1
        else:
            chunking_index.append(count)

    c['id'] = Series(chunking_index, index=c.index)
    c = c.groupby('id').agg({'File': lambda x: x.iloc[0], 'Content': '\n'.join})
    return c

def aq_cosine(corpus):
    c, q_t, a_t = preprocess.preprocessing_pipeline(corpus)

    dictionary = corpora.Dictionary(q_t)
    dictionary.add_documents(a_t)

    q_bow = [dictionary.doc2bow(doc) for doc in q_t]
    q_tfidf = models.TfidfModel(q_bow, smartirs="ntn")
    q_X = matutils.corpus2csc(q_tfidf[q_bow], dtype=np.float, num_terms=len(
        dictionary)).T

    a_bow = [dictionary.doc2bow(doc) for doc in a_t]
    a_tfidf = models.TfidfModel(a_bow, smartirs="ntn")
    a_X = matutils.corpus2csc(a_tfidf[a_bow], dtype=np.float, num_terms=len(
        dictionary)).T

    chunking_index = []
    count = 0

    for i in range(q_X.shape[0]):
        if i < q_X.shape[0] - 1 and cosine_similarity(a_X[i], q_X[i + 1])[0][0]\
                < 0.50:
            chunking_index.append(count)
            count += 1
        else:
            chunking_index.append(count)

    c['id'] = Series(chunking_index, index=c.index)
    c['Content'] = c['Questions'] + '\n' + c['Answers']
    c.drop(['Questions', 'Answers'], axis=1, inplace=True)
    c = c.groupby('id').agg({'File': lambda x: x.iloc[0], 'Content': '\n'.join})
    return c

def chunk_cosine(corpus):
    c, q_t, a_t = preprocess.preprocessing_pipeline(corpus)

    c['Content'] = c['Questions'] + '\n' + c['Answers']
    c.drop(['Questions', 'Answers'], axis=1, inplace=True)
    t = [q + a for q, a in zip(q_t, a_t)]

    dictionary = corpora.Dictionary(q_t)
    dictionary.add_documents(a_t)

    bow = [dictionary.doc2bow(doc) for doc in t]
    tfidf = models.TfidfModel(bow, smartirs="ntn")
    X = matutils.corpus2csc(tfidf[bow], dtype=np.float, num_terms=len(
        dictionary)).T

    chunking_index = []
    count = 0

    for i in range(X.shape[0]):
        if i < X.shape[0] - 1 and cosine_similarity(X[i], X[i + 1])[0][0] < \
                0.50:
            chunking_index.append(count)
            count += 1
        else:
            chunking_index.append(count)

    c['id'] = Series(chunking_index, index=c.index)
    c = c.groupby('id').agg({'File': lambda x: x.iloc[0], 'Content': '\n'.join})
    return c