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
import math
import pprint
from linked_list import LinkedList 

def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"

def utf8len(s):
    return len(s.encode('utf-8'))

def generate_dict_and_postings():
    dictionary = {}
    postings = []
    term_count = 0
    stemmer = PorterStemmer()

    #Get list of all files in the input directory
    files = listdir(input_directory)
    files = map (int,files)
    files.sort()

    with open("docID.txt",'w') as f:
        for docID in files:
            f.write(str(docID))
            f.write(" ")

    #for i in files:
    for i in range(0,10):
        #Concat file name to directory
        #file = input_directory + str(i)
        file = input_directory + str(files[i])
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
                        dictionary[word] = [1,term_count,0]
                        #Add doc ID to as first element in posting list
                        #postings.append([i])
                        tempLinkedList = LinkedList()
                        tempLinkedList.add(files[i])
                        postings.append(tempLinkedList)
                        term_count = term_count + 1
                    else:
                        #Incremet doc frequency
                        dictionary[word][0] = dictionary[word][0] + 1
                        #Append doc ID to posting list
                        #postings[dictionary[word][1]].append([i])
                        postings[dictionary[word][1]].add(files[i])

    return dictionary, postings

def write_postings():
    #Used to track the starting byte of posting
    byte_tracker = 0
    #List of corresponding posting lists and their starting bytes
    byte_ref = []

    #print(postings)

    with open(output_file_postings,'w') as f:
        for posting in postings:
            length = posting.size
            interval = length / int(math.floor(math.sqrt(length)))
            counter = 0
            #Write docID with space
            current = posting.getHead()
            while True:
                if counter % interval == 0 and length > 2:
                    skip = current
                    for i in range(0,interval):
                        if skip.hasNext():
                            skip = skip.getNext()
                        else:
                            break
                    if current.getData() != skip.getData():
                        current.setSkip(skip)

                counter = counter + 1
                if current.hasNext() == False:
                    break
                current = current.getNext()
            
            data_string = pickle.dumps(posting)
            string_length = len(data_string) + data_string.count('\n')
            #byte_tracker = byte_tracker + string_length
            #f.write(str(string_length) + " ")
            f.write(data_string)
            byte_ref.append([byte_tracker,len(data_string)])
            byte_tracker = int(f.tell())
            #print(string_length)

            #GET PICKLE WRITE TO FILE

    return byte_ref

def write_dictionary(byte_ref):
    #Update pointer to correct byte reference
    for key in dictionary:
        dictionary[key][2] = byte_ref[dictionary[key][1]][1]
        dictionary[key][1] = byte_ref[dictionary[key][1]][0]

    print(dictionary)
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