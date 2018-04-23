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
from index import Document, Entry

try:
    import cPickle as pickle
except:
    import pickle

stop_words = set(stopwords.words('english'))

court_list_1 = ['SG Court of Appeal', 'SG Privy Council', 'UK House of Lords', 
                'UK Supreme Court', 'High Court of Australia', 'CA Supreme Court']

court_list_2 = ['SG High Court', 'Singapore International Commercial Court', 'HK High Court',
                'HK Court of First Instance', 'UK Crown Court', 'UK Court of Appeal',
                'UK High Court', 'Federal Court of Australia', 'NSW Court of Appeal',
                'NSW Court of Criminal Appeal', 'NSW Supreme Court']


def search(dictionary_file, postings_file, query_file, output_file, document_file):
    start = time.time()
    out_file = open(output_file, 'w')
    post_file = open(postings_file, 'r')
    dictionary = pickle.load(open(dictionary_file, 'rb'))
    doc_info = pickle.load(open(document_file, 'rb'))

    with open(query_file, 'r') as input, open(output_file, 'w') as output:
        results = []

        for query in input:
            query = query.rstrip()
            if not query:
                continue
            result = process_query(query, dictionary, post_file, doc_info)
            result.append(' '.join(map(str, result)))
        output.write("\n".join(results))

    end = time.time()
    print(end - start)

    out_file.close()
    post_file.close()


def load_posting_list(term, dictionary, post_file):
    offset = dictionary[term].offset
    post_file.seek(offset)
    data = post_file.readline()
    posting_list = map(lambda x: x.split(','), data.split(';'))
    return posting_list


def process_query(query, dictionary, post_file, doc_info):
    queries = map(lambda s: s.strip(), query.split('AND'))
    doc_list = []

    for q in queries:
        if q[0] == '"' and q[-1] == '"':
            q = q.replace('"', "")
            result = phrasal_query(q, dictionary, post_file)
            doc_list.append(result)
        else:
            query_weight = compute_query_weight(query, dictionary, len(doc_info))

            if len(query_weight) > 0:
                term_postings = {term: load_posting_list(term, dictionary, post_file) for term in query_weight}
                score = compute_score(query_weight, term_postings, doc_info)
                result = sorted(score, key=score.get, reverse=True)

                doc_list.append(result)

    if len(doc_list) == 1:
        doc_list = doc_list[0]
    else:
        # TODO: combine multiple lists
        pass

    return doc_list


# return a dictioary where key is doc_id,
# and value is cos similarity score for that doc
def compute_score(query_weight, term_postings, doc_info):
    score = Counter()

    for term in query_weight:
        posting = term_postings[term]
        for item in posting:
            doc_id = item[0]
            tf = float(item[1])

            score[doc_id] += query_weight[term] * tf / doc_info[doc_id].length

    max_score = max(score.values())
    min_score = min(score.values())
    diff_score = max_score - min_score
    weightage = 0.6

    for doc_id in score:
        court = doc_info[doc_id].court
        if court in court_list_1:
            court_score = 1
        elif court in court_list_2:
            court_score = 0.5
        else:
            court_score = 0

        # feature normalization
        cos_score = score[doc_id]
        cos_score = (cos_score - min_score) / diff_score
        score[doc_id] = weightage * cos_score + (1 - weightage) * court_score


    return score


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

    for term, freq in term_weight.items():
        df = dictionary[term][0]
        idf_wt = math.log10(float(num_doc) / df)
        tf_wt = 1 + math.log10(freq)
        wt = idf_wt * tf_wt

        term_weight[term] = wt

    return term_weight


def phrasal_query(query, dictionary, post_file):
    terms = map(process_term, query.split())

    posting1 = load_posting_list(terms.pop(0), dictionary, post_file)

    while len(terms) > 0:
        posting2 = load_posting_list(terms.pop(0), dictionary, post_file)
        posting_temp = []
        idx1 = idx2 = 0

        while idx1 < len(posting1) and idx2 < len(posting2):
            # if doc_id match 
            if posting1[idx1][0] == posting2[idx2][0]:

                item = [posting1[idx1][0], 0]

                # retrieve position
                pp1 = map(int, posting1[idx1][2:])
                pp2 = map(int, posting2[idx2][2:])

                pidx1 = pidx2 = 0

                while pidx1 < len(pp1):
                    while pidx2 < len(pp2):
                        if pp2[pidx2] - pp1[pidx1] == 1:
                            item[1] += 1  # update number of matches found
                            item.append(str(pp2[pidx2]))
                        elif pp2[pidx2] - pp1[pidx1] > 1:
                            break

                        pidx2 += 1

                    pidx1 += 1

                # phrase found
                if len(item) > 2:
                    posting_temp.append(item)

                idx1 += 1
                idx2 += 1

            elif posting1[idx1][0] < posting2[idx2][0]:
                idx1 += 1
            else:
                idx2 += 1

        posting1 = posting_temp

    return map(lambda x: x[0], posting1)


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
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    usage()
    sys.exit(2)

document_file = 'documents.pkl'
search(dictionary_file, postings_file, file_of_queries, file_of_output, document_file)
