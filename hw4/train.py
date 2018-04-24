import nltk
import csv
import re
from itertools import imap
from gensim.models import word2vec
from sanitizer import Sanitizer
from collections import Counter, namedtuple, defaultdict

csv.field_size_limit(2**30)
sanitizer = Sanitizer()
filename = 'dataset.csv'


class Sentences:
    def __init__(self, filename):
        self.filename = filename
        self.reader = csv.reader(open(filename, 'rb'))
        self.reader.next()
        self.sentences = []
    
    def __iter__(self):
        return Sentences(self.filename)

    def next(self):
        if not self.sentences:
            document_id, title, content, date_posted, court = self.reader.next()
            judgement = sanitizer.extract_judgement(content)            
            self.sentences = nltk.sent_tokenize(unicode(judgement, errors='ignore'))
            
        return sanitizer.tokenize(self.sentences.pop())

    __next__ = next # Python 3 compatibility


def train():
    model = word2vec.Word2Vec(
        Sentences(filename), sg=1, size=200, window=5, min_count=5, iter=5, workers=8)
    model.save('vectors.model')

if __name__ == "__main__":
    train()
