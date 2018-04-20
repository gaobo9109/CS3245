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
from collections import Counter, namedtuple, defaultdict
try:
    import cPickle as pickle
except:
    import pickle

stop_words = set(stopwords.words('english'))

Document = namedtuple('Document', ('title', 'length', 'court'))
Entry = namedtuple('Entry', ('offset', 'frequency'))

def search(dictionary_file, postings_file, query_file, output_file, document_file):
    start = time.time()
    out_file = open(output_file, 'w')
    post_file = open(postings_file, 'r')
    dictionary = pickle.load(open(dictionary_file, 'rb'))
    doc_info = pickle.load(open(document_file, 'rb'))

    with open(query_file, 'r') as file:
        for query in file:
            query = query.rstrip()
            if query:
                result = process_query(query, dictionary, post_file, doc_info)
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
    offset = dictionary[term].offset
    post_file.seek(offset)
    data = post_file.readline()
    posting_list = data.split(';')
    return posting_list


def process_query(query, dictionary, post_file, doc_info):
    queries = map(lambda s: s.strip(), query.split('AND'))
    doc_list = []

    for q in queries:
        if q[0] == q[-1] == '"':
            # TODO phrasal query
            pass
        else:
            query_weight = compute_query_weight(query, dictionary, len(doc_info))

            if len(query_weight) > 0:
                term_postings = {term: load_posting_list(term, dictionary, post_file) for term in query_weight}
                cos_score = compute_cos_similarity(query_weight, term_postings, doc_info)
                print(cos_score)
                result = []
                for key in sorted(cos_score, key=cos_score.get, reverse=True):
                    result.append(key)

                doc_list.append(result)

    if len(doc_list) == 1:
        doc_list = doc_list[0]
    else:
        # TODO, combine multiple lists
        pass

    return doc_list


# return a dictioary where key is doc_id,
# and value is cos similarity score for that doc
def compute_cos_similarity(query_weight, term_postings, doc_info):
    cos_score = {}

    for term in query_weight:
        posting = term_postings[term]
        for pair in posting:
            # format of docID-tf string pair: docID,tf
            doc_id, tf = pair.split(',')

            if doc_id in cos_score:
                cos_score[doc_id] += query_weight[term] * float(tf) / doc_info[doc_id].length
            else:
                cos_score[doc_id] = query_weight[term] * float(tf) / doc_info[doc_id].length

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


def process_term(term):
    stemmer = PorterStemmer()
    word = stemmer.stem(term.lower().translate(None, string.punctuation))
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

document_file = 'documents.pkl'
search(dictionary_file, postings_file, file_of_queries, file_of_output, document_file)

