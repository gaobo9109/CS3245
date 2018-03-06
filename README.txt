This is the README file for A0121585H and A0156136H's submission

== Python Version ==

We're using Python Version 2.7 for this assignment.

== General Notes about this assignment ==


During indexing, we first read a document and tokenize it into words. For each word,
we perform porter stemming and store it as a key in the dictionary. We accounted for
2 corner cases:

1. Where the word ends with a puncuation, the punctuation is removed and the word is 
put through the stemmer again
2. Where there is a / between two words, the words a treated as two separate terms

The value of the dictionary is a three element list. The first element is 
the document frequency of the word. The second element is the byte location in 
postings.txt for this word's posting list. The last element is the number of 
bytes to read to retrieve the entire posting list for the word. The dictionary is 
stored as a pickle in Dictionary.txt. 

Each posting list is stored in a LinkedList, where skip pointers are assigned based
on the square root of the length of the list. Every LinkedList is written as a pickle
to postings.txt, and the corresponding byte location and length is stored in the second
and third element of the dictionary values.

During searching, we first tokenize the query and use shunting yard algorithm to convert
the query into postfix notation, which is easier to process. To perform the boolean 
operation, we will load the linked list of docIDs for each query word from the posting
file, and merge the list based on the type of boolean operation. Since skip pointers
are already assigned to specific nodes at indexing time, linked list can be loaded from
file fully populated. As a small optimization, we try to detect AND NOT, which is a single
boolean operation, instead of performing NOT followed by AND operation. To perform NOT operation efficiently, we store a complete list of docID, which can be compared against a 
term's posting list to produce the NOT list. 


== Files included with this submission ==


index.py: to index the NLTK corpus
search.py: query the index using boolean expression
linked_list.py: implementation of linked list
dictionary.txt: contain the dictionary for the index
postings.txt: contain the posting list for all words that appear in the corpus
docID.txt: a list of all document ID in the corpus 
queries.txt: contain boolean queries separated by lines
output.txt: contain lists of docID for each boolean query in queries.txt


== Statement of individual work ==


We, A0121585H, and A0156136H certify that we have followed the CS 3245 
Information Retrieval class guidelines for homework assignments. In particular, 
we expressly vow that we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  


== References ==

http://www.nltk.org/

To check on NLTK API

https://brilliant.org/wiki/shunting-yard-algorithm/

To understand the shunting yard algorithm for parsing boolean expression

https://pymotw.com/2/pickle/

To understand how to use pickle