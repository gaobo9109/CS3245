#!/usr/bin/python
import re
import nltk
import sys
import getopt
from os import listdir
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import *
import string
try:
    import cPickle as pickle
except:
    import pickle

def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"

def generate_dict_and_postings():
    dictionary = {}
    postings = []
    term_count = 0
    stemmer = PorterStemmer()

    #Get list of all files in the input directory
    files = listdir(input_directory)
    files = map (int,files)
    files.sort()

    for i in files:
        #Concat file name to directory
        file = input_directory + str(i)
        with open(file, 'r') as f:
            #Tokenise and stem
            data = f.read()
            words = word_tokenize(data)
            words = [stemmer.stem(word) for word in words]

            #List(Set(words)) gets rid of duplicates
            for word in list(set(words)):

                if word not in string.punctuation:
                    if word not in dictionary:
                        #Add to dictionary, set doc freq to 1
                        #term_count is used as a reference to the corresponding index of the postings list
                        dictionary[word] = [1,term_count]
                        #Add doc ID to as first element in posting list
                        postings.append([i])
                        term_count = term_count + 1
                    else:
                        #Incremet doc frequency
                        dictionary[word][0] = dictionary[word][0] + 1
                        #Append doc ID to posting list
                        postings[dictionary[word][1]].append(i)

    return dictionary, postings

def write_postings():
    #Used to track the starting byte of posting
    byte_tracker = 0
    #List of corresponding posting lists and their starting bytes
    byte_ref = []

    with open(output_file_postings,'w') as f:
        for posting in postings:
            byte_ref.append(byte_tracker)
            #Write docID with space
            for docID in posting:
                f.write(str(docID))
                f.write(" ")
                #Increase byte_tracker accordingly
                byte_tracker = byte_tracker + 1 + len(str(docID))
            # "$" is used as the end of line character
            f.write("$\n")
            byte_tracker = byte_tracker + 3

    return byte_ref

def write_dictionary(byte_ref):
    #Update pointer to correct byte reference
    for key in dictionary:
        dictionary[key][1] = byte_ref[dictionary[key][1]]

    #Write dictionary as pickle
    with open(output_file_dictionary,'w') as f:
        data_string = pickle.dumps(dictionary)
        f.write(data_string)

input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
    
for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"
        
if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

dictionary = {}
postings = []

dictionary,postings = generate_dict_and_postings()
byte_ref = write_postings()
write_dictionary(byte_ref)


with open(output_file_postings,'r') as f:
    pos = 2475
    f.seek(pos)
    string = ""
    data = f.read(1)
    while data != "$":
        #print(f.read(1))
        string = string + data
        pos = pos + 1
        f.seek(pos)
        data = f.read(1)
    print(string)

