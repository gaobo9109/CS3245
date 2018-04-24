import nltk
import csv
import re
from itertools import imap
from gensim.models import word2vec
from sanitizer import Sanitizer
from collections import Counter, namedtuple, defaultdict

csv.field_size_limit(2**30)
sanitizer = Sanitizer()
filename = 'sentences.txt'


def train():
    with open(filename) as f:
        sentences = map(lambda s: s.strip().split(), f)
    
    model = word2vec.Word2Vec(
        sentences, sg=1, size=200, window=5, min_count=5, iter=5, workers=8)
    model.save('vectors.model')

if __name__ == "__main__":
    train()
