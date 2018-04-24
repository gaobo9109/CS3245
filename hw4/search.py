#!/usr/bin/python
import re
import nltk
import sys
import getopt
import time
from nltk.stem import *
from nltk.corpus import stopwords
from gensim.models import word2vec
import string
import math
from collections import Counter, namedtuple, defaultdict
from index import Document, Entry, Posting, Dictionary

try:
    import cPickle as pickle
except:
    import pickle

stop_words = set(stopwords.words('english'))
model = word2vec.Word2Vec.load('model/vectors.model')

court_list_1 = ['SG Court of Appeal', 'SG Privy Council', 'UK House of Lords',
                'UK Supreme Court', 'High Court of Australia', 'CA Supreme Court']

court_list_2 = ['SG High Court', 'Singapore International Commercial Court', 'HK High Court',
                'HK Court of First Instance', 'UK Crown Court', 'UK Court of Appeal',
                'UK High Court', 'Federal Court of Australia', 'NSW Court of Appeal',
                'NSW Court of Criminal Appeal', 'NSW Supreme Court']

def search(dictionary_file, postings_file, query_file, output_file, document_file, expansion=False):

    out_file = open(output_file, 'w')
    post_file = open(postings_file, 'r')
    dictionary = Dictionary.read(dictionary_file)
    doc_info = pickle.load(open(document_file, 'rb'))


    start = time.time()
    with open(query_file, 'r') as input, open(output_file, 'w') as output:
        results = []

        for query in input:
            query = query.rstrip()
            if not query:
                continue
            result = process_query(query, dictionary, post_file, doc_info, expansion)
            results.append(' '.join(map(str, result)))

        output.write("\n".join(results))

    end = time.time()
    print(end - start)

    out_file.close()
    post_file.close()

def expand_query(query):
    expanded = [model.most_similar(term)[0][0].encode('ascii', 'ignore') for term in query.split()]
    return ' '.join(expanded)

def process_query(query, dictionary, post_file, doc_info, expansion):
    # check if the query is free text or boolean
    if query.find('"') == -1 and query.find('AND') == -1:
        if expansion:
            query = expand_query(query)
        doc_list = free_text_query(query, dictionary, post_file, doc_info)
    else:
        doc_list = boolean_query(query, dictionary, post_file, doc_info, expansion)
    return doc_list


def free_text_query(query, dictionary, post_file, doc_info):
    query_weight = compute_query_weight(query, dictionary, len(doc_info))

    if len(query_weight) > 0:
        term_postings = {term: dictionary.read_posting(term, post_file) for term in query_weight}
        score = compute_score(query_weight, term_postings, doc_info)
        result = sorted(score, key=score.get, reverse=True)
        doc_list = [doc_info[doc_id].document_id for doc_id in result]
    else:
        doc_list = []

    return doc_list

def boolean_query(query, dictionary, post_file, doc_info, expansion):
    queries = map(lambda s: s.strip(), query.split('AND'))
    results = []

    for q in queries:
        if q[0] == '"' and q[-1] == '"':
            q = q.replace('"', "")
        if expansion:
            q = expand_query(q)
        result = phrasal_query(q, dictionary, post_file, doc_info)
        results.append(result)

    list1 = results.pop(0)

    while len(results) > 0:
        list2 = results.pop(0)
        list1 = boolean_AND(list1, list2)

    # rank based on court
    scores = map(lambda x: assign_court_score(doc_info[x].court), list1)
    doc_list = [doc_info[doc_id].document_id for score, doc_id in sorted(zip(scores, list1), reverse=True)]

    return doc_list


def boolean_AND(list1, list2):
    i1 = i2 = 0
    result = []

    while i1 < len(list1) and i2 < len(list2):
        if list1[i1] == list2[i2]:
            result.append(list1[i1])
            i1 += 1
            i2 += 1
        elif list1[i1] < list2[i2]:
            i1 += 1
        else:
            i2 += 1
    return result


# return a dictioary where key is doc_id,
# and value is cos similarity score for that doc
def compute_score(query_weight, term_postings, doc_info):
    score = Counter()

    for term in query_weight:
        posting = term_postings[term]
        for item in posting:
            doc_id = item.id
            tf = item.weighted_tf

            score[doc_id] += query_weight[term] * tf / doc_info[doc_id].length

    max_score = max(score.values())
    min_score = min(score.values())
    diff_score = max_score - min_score
    weightage = 0.5

    for doc_id in score:
        court = doc_info[doc_id].court
        court_score = assign_court_score(court)

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
        elif term in dictionary.terms and term not in stop_words:
            term_weight[term] = 1

    for term, freq in term_weight.items():
        entry, end = dictionary.get_term(term)
        df = entry.frequency
        idf_wt = math.log10(float(num_doc) / df)
        tf_wt = 1 + math.log10(freq)
        wt = idf_wt * tf_wt

        term_weight[term] = wt

    return term_weight


def phrasal_query(query, dictionary, post_file, doc_info):
    terms = map(process_term, query.split())

    posting1 = dictionary.read_posting(terms.pop(0), post_file)

    while len(terms) > 0:
        posting2 = dictionary.read_posting(terms.pop(0), post_file)
        posting_temp = []
        i1 = i2 = 0

        while i1 < len(posting1) and i2 < len(posting2):
            # if doc_id match
            if posting1[i1].id == posting2[i2].id:

                # construct intermediate posting
                item = Posting(posting1[i1].id, [], 0)

                # retrieve position
                pp1 = posting1[i1].positions
                pp2 = posting2[i2].positions

                j1 = j2 = 0

                while j1 < len(pp1):
                    while j2 < len(pp2):
                        # record the position of second word of the phrase
                        if pp2[j2] - pp1[j1] == 1:
                            item.positions.append(pp2[j2])
                        elif pp2[j2] - pp1[j1] > 1:
                            break

                        j2 += 1

                    j1 += 1

                # phrase found
                if len(item.positions) > 0:
                    posting_temp.append(item)

                i1 += 1
                i2 += 1

            elif posting1[i1].id < posting2[i2].id:
                i1 += 1
            else:
                i2 += 1

        posting1 = posting_temp

    return map(lambda x: x.id, posting1)


def process_term(term):
    stemmer = PorterStemmer()
    word = stemmer.stem(term.lower().translate(None, string.punctuation))
    return word

def assign_court_score(court):
    if court in court_list_1:
        court_score = 1
    elif court in court_list_2:
        court_score = 0.5
    else:
        court_score = 0
    return court_score


def analyse(doc_list, scores, doc_info):
    for id, score in zip(doc_list, scores):
        doc_id = doc_info[id].document_id
        court = doc_info[id].court
        print doc_id, score, court

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
search(dictionary_file, postings_file, file_of_queries, file_of_output, document_file, expansion=True)
