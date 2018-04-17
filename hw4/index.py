#!/usr/bin/python
import ast
import re
import nltk
import sys
import getopt
import os
from collections import Counter
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import *
import string
try:
	import cPickle as pickle
except:
	import pickle
import math
from sanitizer import Sanitizer

def usage():
	print "usage: " + sys.argv[0] + " -i dataset-file -d dictionary-file -p postings-file"

#Returns dictionary, postings, lengths and courts list based on dataset
def generate_dict_and_postings(input_directory):
	dictionary = {}
	postings = []
	lengths = {}
	courts = {}
	term_count = 0

	with open(input_directory,'r') as f:
		raw_text = ""
		delimiter_count = 0
		#Read file line by line to avoid 
		for line in f:
			#Counts number of time delimiter occurs. It should occur 4 times but delimiter may appear in content
			delimiter_count = delimiter_count + line.count("\",\"")
			#Checks if the end of the entry is reached given by these conditions
			if line.endswith("\"\n") and delimiter_count >= 4 and "\",\"" in line:
				raw_text = raw_text + line
				#Process based on raw data
				term_count = process_dict_and_postings(raw_text, dictionary, postings, courts, lengths, term_count)
				#Reset raw_text and delimiter count
				raw_text = ""
				delimiter_count = 0
				continue
			#Else, add the line to the raw text
			raw_text = raw_text + line

	return dictionary, postings, lengths, courts

#Adds entries to dictionary, postings, lengths and courts list based on raw text
def process_dict_and_postings(raw_text, dictionary, postings,courts,lengths,term_count):
	#Split based on delimiter
	fields = raw_text.split("\",\"")	
	if fields[0][1:].strip()=='document_id':
		return 0
	#Document id is always first element and first character is a ", so it is stripped away
	document_id = int(fields[0][1:].strip())
	print(document_id)
	#Name of court is always last item. Last character is a ", so it is stripped away
	court = fields[-1].strip()[:-1]
	#Add court to courts dictionary
	courts[document_id] = court

	content = ""
	#Joins the strings together for case when delimiter exists within content
	if len(fields) > 5:
		content = ''.join(fields[2:-2])
	else:
		content = fields[2]

	sanitizer = Sanitizer()

	#words = sanitizer.tokenize(sanitizer.extract_judgement(content))
	#Use above when extract_judgement is fixed
	#Generates word list
	words = sanitizer.tokenize(content)


	#Start adding to postings and dictionary

	#Counter stores the count of every word
	counter = Counter(words)

	#Keeps track of the current sum of tf^2
	lengthSum = 0

	#Set(words) gets rid of duplicates
	for word in set(words):
		if word != "":
			weighted_tf = 1 + math.log(counter[word],10)
			if word not in dictionary:
				#Add to dictionary, set doc freq to 1
				#term_count is used as a reference to the corresponding index of the postings list
				dictionary[word] = [1,term_count,0]
				#Append pair of docID and weighted tf to postings list
				postings.append([[document_id,weighted_tf]])
				term_count = term_count + 1
			else:
				#Incremet doc frequency
				dictionary[word][0] = dictionary[word][0] + 1
				#Append pair of docID and weighted tf to postings list
				postings[dictionary[word][1]].append([document_id,weighted_tf])

			#Add weighted_tf^2 to lengthSum
			lengthSum = lengthSum + (weighted_tf*weighted_tf)

	#After all words have been added to dictionary, calculate document length for normalisation
	lengths[document_id] = math.sqrt(lengthSum)

	#returns term_count to keep track of index
	return term_count
		

def write_postings(output_file_postings, postings, dictionary):
	#Used to track the starting byte of posting
	byte_tracker = 0
	#List of corresponding posting lists and their starting bytes
	byte_ref = []

	with open(output_file_postings,'w') as f:
		for posting in postings:            
			#Writes pickle generated string to file
			data_string = pickle.dumps(posting)
			f.write(data_string)
			#Keep track of starting byte and length of pickle in bytes 
			byte_ref.append([byte_tracker,f.tell()-byte_tracker])
			#Keeps track of starting byte of next linked list
			byte_tracker = int(f.tell())

	#Updates starting byte and length of pickle into dictionary
	for key in dictionary:
		dictionary[key][2] = byte_ref[dictionary[key][1]][1]
		dictionary[key][1] = byte_ref[dictionary[key][1]][0]

	return byte_ref

def write_to_file(output_file_directory, to_write):
	#Write dictionary as pickle
	with open(output_file_directory,'w') as f:
		data_string = pickle.dumps(to_write)
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
lengths = {}
courts = {}

output_file_lengths = "lengths.txt"
output_file_courts = "courts.txt"

dictionary,postings,lengths,courts = generate_dict_and_postings(input_directory)
byte_ref = write_postings(output_file_postings, postings, dictionary)
write_to_file(output_file_dictionary, dictionary)
write_to_file(output_file_lengths, lengths)
write_to_file(output_file_courts, courts)