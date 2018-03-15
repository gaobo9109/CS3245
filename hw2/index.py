#!/usr/bin/python
import re
import nltk
import sys
import getopt
import os
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import *
import string
try:
    import cPickle as pickle
except:
    import pickle
import math
from linked_list import LinkedList 

def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"

def generate_dict_and_postings(input_directory):
    dictionary = {}
    postings = []
    term_count = 0
    stemmer = PorterStemmer()


    #Get list of all files in the input directory
    files = os.listdir(input_directory)
    files = map (int,files)
    files.sort()

    with open("docID.txt",'w') as f:
        for docID in files:
            f.write(str(docID))
            f.write(" ")

    for i in files:
        #Concat file name to directory
        file = os.path.join(input_directory,str(i))
        with open(file, 'r') as f:
            #Tokenise and stem
            data = f.read()
            words = word_tokenize(data)
            words = [stemmer.stem(word.translate(None, string.punctuation)) for word in words]

            #Removes punctuation for words with puncuation as last character
            # for index, word in enumerate(words):
            #     if word [-1] in string.punctuation and len(word) > 1:
            #         words[index] = stemmer.stem(word[:-1].lower())
            #     else:
            #         words[index] = stemmer.stem(word.lower())

            #List(Set(words)) gets rid of duplicates
            for word in list(set(words)):
                if word not in string.punctuation:
                    if word not in dictionary:
                        #Add to dictionary, set doc freq to 1
                        #term_count is used as a reference to the corresponding index of the postings list
                        dictionary[word] = [1,term_count,0]
                        #Add doc ID to as first element in linked list
                        tempLinkedList = LinkedList()
                        tempLinkedList.add(i)
                        #Append linked list to postings list
                        postings.append(tempLinkedList)
                        term_count = term_count + 1
                    else:
                        #Incremet doc frequency
                        dictionary[word][0] = dictionary[word][0] + 1
                        #Append doc ID to posting list
                        postings[dictionary[word][1]].add(i)

    return dictionary, postings
        

def write_postings(output_file_postings, postings):
    #Used to track the starting byte of posting
    byte_tracker = 0
    #List of corresponding posting lists and their starting bytes
    byte_ref = []

    with open(output_file_postings,'w') as f:
        for posting in postings:
            length = posting.size
            #interval represents how many elements to skip
            interval = length / int(math.floor(math.sqrt(length)))

            counter = 0
            current = posting.getHead()

            #Loops through all nodes in linked list
            while True:
                #Criteria for node to have skip pointer
                if counter % interval == 0 and length > 2:
                    skip = current
                    #Iterates over "interval" number of nodes or till end of list is reached
                    for i in range(0,interval):
                        if skip.hasNext():
                            skip = skip.getNext()
                        else:
                            break
                    #If node is not itself, set skip pointer
                    if current.getData() != skip.getData():
                        current.setSkip(skip)

                counter = counter + 1

                if current.hasNext() == False:
                    break
                current = current.getNext()
            
            #Writes pickle generated string to file
            data_string = pickle.dumps(posting)
            f.write(data_string)
            #Keep track of starting byte and length of pickle in bytes 
            byte_ref.append([byte_tracker,f.tell()-byte_tracker])
            #Keeps track of starting byte of next linked list
            byte_tracker = int(f.tell())
            ll = pickle.loads(data_string)

    return byte_ref

def write_dictionary(byte_ref, output_file_dictionary, dictionary):
    #Updates starting byte and length of pickle
    for key in dictionary:
        dictionary[key][2] = byte_ref[dictionary[key][1]][1]
        dictionary[key][1] = byte_ref[dictionary[key][1]][0]

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

dictionary,postings = generate_dict_and_postings(input_directory)
byte_ref = write_postings(output_file_postings, postings)
write_dictionary(byte_ref, output_file_dictionary, dictionary)