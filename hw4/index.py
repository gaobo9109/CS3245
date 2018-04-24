#!/usr/bin/python
from __future__ import division, print_function
import re
import nltk
import sys
import getopt
import csv
import vbcode
from collections import Counter, namedtuple, defaultdict
from itertools import imap
from multiprocessing import Pool
from operator import attrgetter


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


def usage():
    print("usage: " + sys.argv[0] + " -i dataset-file -d dictionary-file -p postings-file [-m]")


def calculate_deltas(numbers):
    if not numbers:
        return numbers

    deltas = [numbers[0]]
    for i, n in enumerate(numbers[1:]):
        deltas.append(n - numbers[i])
    return deltas


def from_deltas(deltas):
    if not deltas:
        return deltas

    numbers = [deltas[0]]
    for i in deltas[1:]:
        numbers.append(i + numbers[-1])
    return numbers


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
    words = sanitizer.tokenize(sanitizer.sanitize(row.content))
    counter = Counter()
    for index, word in enumerate(filter(None, words)):
        counter[word] += 1
        positions[word].append(index)

    # Keeps track of the current sum of tf^2
    postings = {}
    length_sum = 0

    for word in counter.keys():
        weighted_tf = 1 + math.log10(counter[word])
        position_deltas = calculate_deltas(positions[word])
        postings[word] = Posting(id, position_deltas, weighted_tf)

        # Add weighted_tf^2 to lengthSum
        length_sum += weighted_tf ** 2

    # TODO: Optimize this using objects instead of strings
    document = Document(document_id=document_id,
                        title=row.title,
                        length=math.sqrt(length_sum),
                        court=row.court)

    return id, postings, document


def encode_posting(args):
    term, postings = args
    delta_id = calculate_deltas(map(attrgetter('id'), postings))
    encoded_entry = b''

    for posting, id in zip(postings, delta_id):
        decimal_tf = int(posting.weighted_tf * 10 ** 6) if posting.weighted_tf != 1.0 else 1
        encoded_entry += vbcode.encode([id, decimal_tf, len(posting.positions)])
        encoded_entry += vbcode.encode(posting.positions)

    return term, encoded_entry


def write_postings(output_file_postings, postings, pool=None):
    # List of corresponding posting lists and their starting bytes
    term_offsets = {}

    if pool:
        results = pool.map(encode_posting, postings.items())
    else:
        results = imap(encode_posting, postings.items())

    encoded_entries = dict(results)
    sorted_terms = sorted(postings)

    with open(output_file_postings, 'wb') as output_file:
        for term in sorted_terms:
            offset = output_file.tell()
            output_file.write(encoded_entries[term])
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
        posting_file.seek(entry.offset)

        postings = []
        document_id = 0
        while posting_file.tell() < end:
            packed_posting = vbcode.decode_stream(posting_file, 3)
            if not packed_posting:
                break

            delta_id, decimal_tf, positions_len = packed_posting
            tf = decimal_tf / 10**6 if decimal_tf != 1 else 1.0
            document_id += delta_id

            position_deltas = vbcode.decode_stream(posting_file, positions_len)
            positions = from_deltas(position_deltas)
            
            postings.append(Posting(document_id, positions, tf))
        return postings

    @staticmethod
    def write_from_freq_offsets(filename, document_freq, term_offsets):
        with open(filename, 'wb') as f:
            for term in document_freq:
                encoded_entry = vbcode.encode([len(term), document_freq[term], term_offsets[term]])
                f.write(encoded_entry + bytes(term))

    @staticmethod
    def read(filename):
        entries = {}

        with open(filename, 'rb') as f:
            decoded = vbcode.decode_stream(f, 3)
            while decoded:
                length, freq, offset = decoded
                term = f.read(length)
                entries[term] = Entry(frequency=freq, offset=offset)
                decoded = vbcode.decode_stream(f, 3)

        return Dictionary(entries)


if __name__ == '__main__':
    input_directory = output_file_dictionary = output_file_postings = pool = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:m')
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
        elif o == '-m': # Enable multiprocessing
            pool = Pool()
            print("Multiprocessing enabled")
        else:
            assert False, "unhandled option"

    if input_directory is None or output_file_postings is None or output_file_dictionary is None:
        usage()
        sys.exit(2)

    output_file_documents = "documents.pkl"

    document_freq, postings, documents = generate_dict_and_postings(input_directory, pool)
    term_offsets = write_postings(output_file_postings, postings)
    Dictionary.write_from_freq_offsets(output_file_dictionary, document_freq, term_offsets)

    with open(output_file_documents, 'wb') as f:
        pickle.dump(documents, f, protocol=2)
