import os
import re
import logging
import csv
import sys
import nltk
from itertools import imap
from gensim.models import word2vec
from sanitizer import Sanitizer
from collections import Counter, namedtuple, defaultdict
from multiprocessing import Pool

Document = namedtuple('Document', ('document_id', 'title', 'length', 'court'))
Entry = namedtuple('Entry', ('offset', 'frequency'))
Posting = namedtuple('Posting', ('id', 'positions', 'weighted_tf'))
DatasetRow = namedtuple('DatasetRow', ('document_id', 'title', 'content', 'date_posted', 'court'))

csv.field_size_limit(2**30)
sanitizer = Sanitizer()

def generate_sentence(args):
    id, row = args
    document_id = int(row.document_id)
    print(document_id)

    # Counter stores the count of every word
    content = sanitizer.extract_judgement(row.content)
    return nltk.sent_tokenize(content)

class Sentences(object):
    def __init__(self, path=None):
        if not path:
            path = "corpus"
        self.path = path

    def __iter__(self):
        pool = Pool()
        file_name = self.path + '/dataset.csv'
        with open(file_name, 'rb') as f:
            reader = imap(lambda row: DatasetRow(*row), csv.reader(f))
            reader.next()

            results = imap(generate_sentence, enumerate(reader))
            for sentences in results:
                for sentence in sentences:
                    yield sentence.split()

def train():
    sentences = Sentences()
    model = word2vec.Word2Vec(
        sentences, sg=1, size=200, window=5, min_count=5, iter=5)
    model.save('vectors.model')

if __name__ == "__main__":
    train()
