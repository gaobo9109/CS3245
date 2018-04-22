#!/usr/bin/python
import re
import nltk
import sys
import getopt
import csv
import io
from struct import Struct
from collections import Counter, namedtuple, defaultdict
from itertools import imap
from multiprocessing import Pool
from vendor.pyvbcode import vbcode

try:
    import cPickle as pickle
except ImportError:
    import pickle
import math

from sanitizer import Sanitizer

Document = namedtuple('Document', ('document_id', 'title', 'length', 'court'))
Entry = namedtuple('Entry', ('offset', 'frequency'))
Posting = namedtuple('Posting', ('id', 'positions', 'weighted_tf'))
DatasetRow = namedtuple('DatasetRow', ('document_id', 'title', 'content', 'date_posted', 'court'))

# CSV's default field limit is a bit too small for us
csv.field_size_limit(2**30)

# Create a sanitizer instance for us to use
sanitizer = Sanitizer()

# document_id, weighted_tf, len(positions)
posting_struct = Struct("HfH")


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
            results = pool.map(generate_posting, enumerate(reader))
        else:
            results = imap(generate_posting, enumerate(reader))

        for id, document_postings, document in results:
            documents[id] = document

            for term, posting_list in document_postings.items():
                postings[term].append(posting_list)
                doc_freq[term] += 1

    return doc_freq, postings, documents


def generate_posting(args):
    id, row = args
    document_id = int(row.document_id)
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
        postings[word] = Posting(id, positions[word], weighted_tf)

        # Add weighted_tf^2 to lengthSum
        length_sum += weighted_tf ** 2

    # TODO: Optimize this using objects instead of strings
    document = Document(document_id=document_id,
                        title=row.title,
                        length=math.sqrt(length_sum),
                        court=row.court)

    return id, postings, document


def write_postings(output_file_postings, postings):
    # List of corresponding posting lists and their starting bytes
    term_offsets = {}
    sorted_terms = sorted(postings)

    with open(output_file_postings, 'wb') as output_file:
        for term in sorted_terms:
            offset = output_file.tell()

            for posting in postings[term]:
                encoded_entry = posting_struct.pack(posting.id, posting.weighted_tf, len(posting.positions))
                encoded_entry += vbcode.encode(posting.positions)
                output_file.write(encoded_entry)

                if term == 'home':
                    print posting

            term_offsets[term] = offset

    return term_offsets


class Dictionary:
    def __init__(self, entries):
        self.terms = sorted(entries)
        self.entries = entries
        self.end = {}

        terms = sorted(entries)
        for index, term in enumerate(terms[:-1]):
            self.end[term] = entries[terms[index + 1]].offset

    def write(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.entries, f, protocol=2)

    def get_term(self, term):
        return self.entries[term], self.end.get(term, sys.maxsize)

    def read_posting(self, term, posting_file):
        if term not in self.entries:
            return []

        entry, end = self.get_term(term)
        print(entry, end)
        posting_file.seek(entry.offset)

        postings = []
        while posting_file.tell() < end:
            encoded_posting = posting_file.read(posting_struct.size)
            if not encoded_posting:
                break

            id, tf, positions_len = posting_struct.unpack(encoded_posting)
            positions = vbcode.decode_stream(posting_file, positions_len)
            postings.append(Posting(id, positions, tf))
        return postings

    @staticmethod
    def write_from_freq_offsets(filename, document_freq, term_offsets):
        entries = {}
        for term in document_freq:
            entries[term] = Entry(frequency=document_freq[term], offset=term_offsets[term])

        with open(filename, 'wb') as f:
            pickle.dump(entries, f, protocol=2)

    @staticmethod
    def read(filename):
        with open(filename, 'rb') as f:
            entries = pickle.load(f)
        return Dictionary(entries)


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
    Dictionary.write_from_freq_offsets(output_file_dictionary, document_freq, term_offsets)

    with open(output_file_documents, 'wb') as f:
        pickle.dump(documents, f, protocol=2)
