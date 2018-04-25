#!/usr/bin/python
import nltk
import sys
import getopt
import time
import string
import math
from nltk.stem import PorterStemmer
from collections import Counter

from index import Document, Entry, Posting, Dictionary
from config import *

try:
    import cPickle as pickle
except ImportError:
    import pickle

stemmer = PorterStemmer()

court_list_1 = ['SG Court of Appeal', 'SG Privy Council', 'UK House of Lords',
                'UK Supreme Court', 'High Court of Australia', 'CA Supreme Court']

court_list_2 = ['SG High Court', 'Singapore International Commercial Court', 'HK High Court',
                'HK Court of First Instance', 'UK Crown Court', 'UK Court of Appeal',
                'UK High Court', 'Federal Court of Australia', 'NSW Court of Appeal',
                'NSW Court of Criminal Appeal', 'NSW Supreme Court']


def search(dictionary_file, postings_file, query_file, output_file, document_file, model=None):
    dictionary = Dictionary.read(dictionary_file)

    with open(document_file, 'rb') as f:
        doc_info = pickle.load(f)

    start = time.time()
    with open(query_file, 'r') as input, open(output_file, 'w') as output, open(postings_file, 'rb') as post_file:
        results = []

        for query in input:
            query = query.strip()
            if not query:
                continue
            result = process_query(query, dictionary, post_file, doc_info, model)
            results.append(' '.join(map(str, result)))

        output.write("\n".join(results))

    end = time.time()
    print(end - start)


def expand_query(query_terms, model):
    expanded_terms = []

    for term in query_terms:
        try:
            similar = model.most_similar(term)
            if not similar:
                continue

            synonym, score = similar.pop(0)
            while similar and score >= SYNONYM_CUTOFF:
                expanded_terms.append(synonym)
                synonym, score = similar.pop(0)

        except KeyError:
            # Term not in vocabulary - just skip it
            pass

    return expanded_terms


def process_query(query, dictionary, post_file, doc_info, model):
    # check if the query is free text or boolean
    if '"' not in query and 'AND' not in query:
        query_terms = map(process_term, query.split())
        if model:
            query_terms.extend(expand_query(query_terms, model))
        doc_list = free_text_query(query_terms, dictionary, post_file, doc_info)
    else:
        doc_list = boolean_query(query, dictionary, post_file, doc_info)
    return doc_list

# return a list of doc_id
def free_text_query(query_terms, dictionary, post_file, doc_info):
    query_weight = compute_query_weight(query_terms, dictionary, len(doc_info))

    if query_weight:
        term_postings = {term: dictionary.read_posting(term, post_file) for term in query_weight}
        score = compute_score_free_text(query_weight, term_postings, doc_info)
        doc_list = rank_by_score(score, doc_info)
    else:
        doc_list = []

    return doc_list


def boolean_query(query, dictionary, post_file, doc_info):
    queries = query.split('AND')
    results = []

    for q in queries:
        q = q.replace('"', "").strip()
        result = phrasal_query(q, dictionary, post_file, doc_info)
        results.append(result)

    id_list1 = map(lambda x: x.id, results[0])
    index = 1

    while index < len(results):
        id_list2 = map(lambda x: x.id, results[index])
        id_list1 = boolean_AND(id_list1, id_list2)
        index += 1

    final_list = id_list1

    # filter the posting list for all query terms based on the final_list
    filtered_results = [filter(lambda x: x.id in final_list, result) for result in results]

    score = compute_score_boolean(final_list, filtered_results, doc_info)
    doc_list = rank_by_score(score, doc_info)

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


# return a dictionary where key is doc_id,
# and value is cos similarity score for that doc
def compute_score_free_text(query_weight, term_postings, doc_info):
    score = Counter()

    for term in query_weight:
        posting = term_postings[term]
        for item in posting:
            doc_id = item.id
            tf = item.weighted_tf

            score[doc_id] += query_weight[term] * tf / doc_info[doc_id].length

    score = combine_court_score(score, doc_info, 0.8)

    return score

def compute_score_boolean(id_list, filtered_results, doc_info):
    score = Counter()
    for i in range(len(id_list)):
        doc_id = id_list[i]
        for result in filtered_results:
            score[doc_id] += result[i].weighted_tf / doc_info[doc_id].length

    score = combine_court_score(score, doc_info, 0.8)
    return score

def rank_by_score(score, doc_info):
    result = sorted(score, key=score.get, reverse=True)
    doc_list = [doc_info[doc_id].document_id for doc_id in result]
    return doc_list


def combine_court_score(score, doc_info, weightage):
    if not score:
        return score
    
    max_score = max(score.values())
    min_score = min(score.values())
    diff_score = max_score - min_score

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
def compute_query_weight(query_terms, dictionary, num_doc):
    term_weight = {}

    for term in query_terms:
        if term in term_weight:
            term_weight[term] += 1
        elif term in dictionary.terms and term not in STOPWORDS:
            term_weight[term] = 1

    for term, freq in term_weight.items():
        entry, end = dictionary.get_term(term)
        df = entry.frequency
        idf_wt = math.log10(float(num_doc) / df)
        tf_wt = 1 + math.log10(freq)
        wt = idf_wt * tf_wt

        term_weight[term] = wt

    return term_weight

# return a list of Posting objects
def phrasal_query(query, dictionary, post_file, doc_info):
    terms = filter(lambda x: x not in STOPWORDS, map(process_term, query.split()))

    posting1 = dictionary.read_posting(terms.pop(0), post_file)

    while terms:
        posting2 = dictionary.read_posting(terms.pop(0), post_file)
        posting_temp = []
        i1 = i2 = 0

        while i1 < len(posting1) and i2 < len(posting2):
            # if doc_id match
            if posting1[i1].id == posting2[i2].id:
                # construct intermediate positions
                positions = []
                count = 0

                # retrieve position
                pp1 = posting1[i1].positions
                pp2 = posting2[i2].positions

                j1 = j2 = 0

                while j1 < len(pp1):
                    while j2 < len(pp2):
                        # record the position of second word of the phrase
                        if pp2[j2] - pp1[j1] == 1:
                            positions.append(pp2[j2])
                            count += 1
                        elif pp2[j2] - pp1[j1] > 1:
                            break

                        j2 += 1
                    j1 += 1

                # phrase found
                if positions:
                    weighted_tf = 1 + math.log10(count)
                    posting_temp.append(Posting(posting1[i1].id, positions, weighted_tf))

                i1 += 1
                i2 += 1

            elif posting1[i1].id < posting2[i2].id:
                i1 += 1
            else:
                i2 += 1

        posting1 = posting_temp

    return posting1


def process_term(term):
    word = stemmer.stem(term.lower().translate(None, string.punctuation))
    return word


def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file [-e word2vec model]"


dictionary_file = postings_file = file_of_queries = file_of_output = model = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:e:')
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
    elif o == '-e':
        try:
            from gensim.models.word2vec import Word2Vec

            model = Word2Vec.load(a)
        except Exception as e:
            print "Cannot load word2vec model"
            print e

    else:
        assert False, "unhandled option"

if dictionary_file is None or postings_file is None or file_of_queries is None or file_of_output is None:
    usage()
    sys.exit(2)

search(dictionary_file, postings_file, file_of_queries, file_of_output, DOCUMENTS_FILENAME, model)
