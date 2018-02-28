#!/usr/bin/python
import re
import nltk
import sys
import getopt

precedence_map = {'(':4, 'NOT':3, 'AND':2, 'OR':1}

def search(dictionary_file, postings_file, query_file, output_file):
    out_file = open(out_file, 'w')
    post_file = open(postings_file, 'rb')
    dictionary = load_dictionary(dictionary_file)

    with open(query_file, 'r') as file:
        for query in file:
            result = process_query(query, dictionary, post_file)
            docID = ''
            for term in result:
                docId += result + ' '
            docID = docID[0:-1] + '\n'
            out_file.write(docID)

    out_file.close()
    post_file.close()
    query_file.close()

def load_dictionary(dictionary_file):
    pass

def load_posting_list(term, dictionary, post_file):
    pass

def process_query(query, dictionary, post_file):
    op_list = ['AND', 'OR', 'NOT']
    query.replace('(', '( ')
    query.replace(')', ') ')
    query = query.split()

    output_queue = shunting_yard(query)
    result_stack = []

    while output_queue
        term = output_queue.pop(0)
        result = []

        if term not in op_list:
            result = load_posting_list(term, dictionary, post_file)
        elif term == 'AND':
            op1 = result_stack.pop()
            op2 = result_stack.pop()
            result = boolean_AND(op1, op2)
        elif term == 'OR':
            op1 = result_stack.pop()
            op2 = result_stack.pop()
            result = boolean_OR(op1, op2)
        elif term == 'NOT':
            # try to detect AND NOT, there are two cases
            # if a AND NOT b, postfix notation a b NOT AND
            # if NOT a AND b, postfix notation a NOT b AND
            if (len(output_queue) > 0 and output_queue[0] == 'AND'):
                output_queue.pop(0)
                op1 = result_stack.pop()
                op2 = result_stack.pop()
                result = boolean_ANDNOT(op1, op2) 
            elif (len(output_queue) > 1 and output_queue[0] not in op_list 
                    and output_queue[1] == 'AND'):
                op1 = result_stack.pop(0)
                op2 = load_posting_list(output_queue.pop(), dictionary, post_list)
                output_queue.pop(0)
                result = boolean_ANDNOT(op1, op2)            
            else:
                op = result_stack.pop()
                result = boolean_NOT(op)
        
        result_stack.append(result)

    assert len(result_stack) == 1, 'result stack should only have one list at this point'
    return result_stack.pop()

def shunting_yard(query):
    op_stack = []
    output_queue = []

    for term in query:
        if term not in precedence_map:
            output_queue.append(term.lower())
        else:
            if term == '(':
                op_stack.append(term)
            elif term == ')':
                while op_stack and op_stack[-1] != '(':
                    output_queue.append(op_stack.pop())
                op_stack.pop()
            else:
                while op_stack and precedence_map(op_stack[-1]) >= precedence_map(term):
                    output_queue.append(op_stack.pop())
                op_stack.append(term)
    while op_stack:
        output_queue.append(op_stack.pop())
    return output_queue


def boolean_AND(op1, op2):
    pass

def boolean_OR(op1, op2):
    pass

def boolean_NOT(op):
    pass

def boolean_ANDNOT(op1, op2):
    pass


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
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

