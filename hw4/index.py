#!/usr/bin/python
import re
import nltk
import sys
import getopt
import csv
from collections import Counter, namedtuple, defaultdict
from itertools import imap
from multiprocessing import Pool

try:
    import cPickle as pickle
except ImportError:
    import pickle
import math

from sanitizer import Sanitizer

Document = namedtuple('Document', ('title', 'length', 'court'))
Entry = namedtuple('Entry', ('offset', 'frequency'))
Posting = namedtuple('Posting', ('document_id', 'positions', 'weighted_tf'))
DatasetRow = namedtuple('DatasetRow', ('document_id', 'title', 'content', 'date_posted', 'court'))

# CSV's default field limit is a bit too small for us
csv.field_size_limit(2**30)

# Create a sanitizer instance for us to use
sanitizer = Sanitizer()


def usage():
    print "usage: " + sys.argv[0] + " -i dataset-file -d dictionary-file -p postings-file"


# Returns dictionary, postings, lengths and courts list based on dataset
def generate_dict_and_postings(data_file, pool=None):
    doc_freq = Counter()
    postings = defaultdict(list)
    documents = {}

    with open(data_file, 'rb') as f:
        reader = imap(lambda row: DatasetRow(*row), csv.reader(f))
        reader.next()  # Drop the header row

        if pool:
            results = pool.map(generate_posting, reader)
        else:
            results = imap(generate_posting, reader)

        for document_id, document_postings, document in results:
            documents[document_id] = document

            for term, posting_list in document_postings.items():
                postings[term].append(posting_list)
                doc_freq[term] += 1

    return doc_freq, postings, documents


def generate_posting(row):
    document_id = row.document_id
    positions = defaultdict(list)
    print(document_id)

    # Counter stores the count of every word
    words = sanitizer.tokenize(row.content)
    counter = Counter()
    for index, word in enumerate(filter(None, words)):
        counter[word] += 1
        positions[word].append(index)

    # Keeps track of the current sum of tf^2
    postings = {}
    length_sum = 0

    for word in counter.keys():
        weighted_tf = 1 + math.log10(counter[word])
        postings[word] = Posting(document_id, positions[word], weighted_tf)

        # Add weighted_tf^2 to lengthSum
        length_sum += weighted_tf ** 2

    # TODO: Optimize this using objects instead of strings
    document = Document(title=row.title, length=math.sqrt(length_sum), court=row.court)
    return document_id, postings, document


def format_posting(posting):
    return "%s,%s,%s" % (posting.document_id, posting.weighted_tf, ",".join(map(str, posting.positions)))


def write_postings(output_file_postings, postings):
    # List of corresponding posting lists and their starting bytes
    term_offsets = {}
    sorted_terms = sorted(postings)

    with open(output_file_postings, 'w') as f:
        for term in sorted_terms:
            term_offsets[term] = int(f.tell())
            # Format: doc_id,tf,position1,position2,position3,...;doc_id,tf,position1,position2,...
            formatted_postings = map(format_posting, postings[term])
            f.write(";".join(formatted_postings) + "\n")

    return term_offsets


def write_dictionary(dictionary_file, document_freq, term_offsets):
    dictionary = {}
    for term in document_freq:
        dictionary[term] = Entry(frequency=document_freq[term], offset=term_offsets[term])

    with open(dictionary_file, 'wb') as f:
        pickle.dump(dictionary, f, protocol=2)


if __name__ == '__main__':
    input_directory = output_file_dictionary = output_file_postings = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
    except getopt.GetoptError, err:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-i':  # input directory
            input_directory = a
        elif o == '-d':  # dictionary file
            output_file_dictionary = a
        elif o == '-p':  # postings file
            output_file_postings = a
        else:
            assert False, "unhandled option"

    if input_directory is None or output_file_postings is None or output_file_dictionary is None:
        usage()
        sys.exit(2)

    output_file_documents = "documents.pkl"
    pool = None # = Pool()
    document_freq, postings, documents = generate_dict_and_postings(input_directory, pool)
    term_offsets = write_postings(output_file_postings, postings)
    write_dictionary(output_file_dictionary, document_freq, term_offsets)

    with open(output_file_documents, 'wb') as f:
        pickle.dump(documents, f, protocol=2)
