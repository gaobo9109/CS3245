#!/usr/bin/python
import re
import nltk
import sys
import getopt
import time
from nltk.stem import *
from nltk.corpus import stopwords
import string
import math
import heapq
import collections
try:
    import cPickle as pickle
except:
    import pickle

stop_words = set(stopwords.words('english'))

def search(dictionary_file, postings_file, query_file, output_file, doc_norm_file):
    start = time.time()
    out_file = open(output_file, 'w')
    post_file = open(postings_file, 'rb')
    dictionary = pickle.load(open(dictionary_file, 'rb'))
    doc_norm = pickle.load(open(doc_norm_file, 'rb'))

    with open(query_file, 'r') as file:
        for query in file:
            query = query.rstrip()
            if query:
                result = process_query(query, dictionary, post_file, doc_norm)
                docID = ''
                for term in result:
                    docID += str(term) + ' '
                docID = docID[0:-1] + '\n'
                out_file.write(docID)

    end = time.time()
    print(end-start)

    out_file.close()
    post_file.close()


def load_posting_list(term, dictionary, post_file):
    freq, offset, length = dictionary[term]
    post_file.seek(offset)
    data = post_file.read(length)
    posting_list = pickle.loads(data)
    return posting_list


def process_query(query, dictionary, post_file, doc_norm):
    query_weight = compute_query_weight(query, dictionary, len(doc_norm))
    if len(query_weight) == 0:
        return []
    else:
        term_postings = {term: load_posting_list(term, dictionary, post_file) for term in query_weight}
        cos_score = compute_cos_similarity(query_weight, term_postings, doc_norm)
        doc_list = find_top_k_match(10, cos_score)
        return doc_list

# return a dictioary where key is doc_id,
# and value is cos similarity score for that doc
def compute_cos_similarity(query_weight, term_postings, doc_norm):
    cos_score = {}

    for term in query_weight:
        posting = term_postings[term]
        for doc_id, tf in posting:
            if doc_id in cos_score:
                cos_score[doc_id] += query_weight[term] * tf / doc_norm[doc_id]
            else:
                cos_score[doc_id] = query_weight[term] * tf / doc_norm[doc_id]

    # preserve doc ordering, for breaking ties when cos score same
    cos_score = collections.OrderedDict(sorted(cos_score.items()))

    for doc_id in cos_score:
        print(doc_norm[doc_id])
    return cos_score


# return a dictionary where the key is a query term, 
# and value is tf-idf weight for that term
def compute_query_weight(query, dictionary, num_doc):
    term_weight = {}
    for term in query.split():
        term = process_term(term)
        if term in term_weight:
            term_weight[term] += 1
        elif term in dictionary and term not in stop_words:
            term_weight[term] = 1

    for term, freq in term_weight.iteritems():
        df = dictionary[term][0]
        idf_wt = math.log(float(num_doc) / df, 10)
        tf_wt = 1 + math.log(freq, 10)
        wt = idf_wt * tf_wt
        term_weight[term] = wt

    return term_weight

def find_top_k_match(num_results, cos_score):
    num_results = num_results if len(cos_score) > num_results else len(cos_score)

    print(cos_score)
    reverse_map = {v: k for k, v in cos_score.items()}
    heap = map(lambda x: -x, reverse_map.keys())
    heapq.heapify(heap)

    result = []
    for i in range(num_results):
        cos_score = -heapq.heappop(heap)
        result.append(reverse_map[cos_score])
    return result

def process_term(term):
    stemmer = PorterStemmer()
    word = stemmer.stem(term.translate(None, string.punctuation))
    return word


def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

dictionary_file = postings_file = file_of_queries = output_file_of_results = None
	
try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

doc_norm_file = 'lengths.txt'
search(dictionary_file, postings_file, file_of_queries, file_of_output, doc_norm_file)

