This is the README file for A0121585H and A0156136H's submission
Email: a0121585@u.nus.edu
       e0032273@u.nus.edu

== Python Version ==

We're using Python Version 2.7 for this assignment.

== General Notes about this assignment ==

During index we iterate through

During indexing, iterate through all the documents and tokenize the document into words.
For each word, we convert it to lower case, remove all punctuation, then perform porter 
stemming. This will be used as the key in the dictionary. 
The value of the dictionary is a three element list. The first element is 
the document frequency of the word. The second element is the byte location in 
postings.txt for this word's posting list. The last element is the number of 
bytes to read to retrieve the entire posting list for the word. The dictionary is 
stored as a pickle in Dictionary.txt. 
Each posting list is stored in a list where each element is a pair of docID and the 
log weighted term frequency for the corresponding docID. Every posting list is stored
as a pickle in postings.txt, and the corresponding byte location and length is stored
in the second and third element of the dictionary values
The document lengths for normalisation are calculated and stored in a dictionary with the
docID as the key. The dictionary is stored as a pickle in lengths.txt


During searching, we first tokenize the query, and perform stemming and case-folding on each
query term. Stop words are removed since they have low idf and do not have much effect on final 
ranking. For each query term, we then compute its tf and idf, and construct tf-idf vector for the 
entire query. We then extract posting list associated with each query term. The cos similarity score
for each document is computed using the described algorithm in the lecture note. Finally, we use python
heapq to heapify the list of cos similarity score, extract the top 10 scores and their respective doc id. 


== Files included with this submission ==

index.py: to index the NLTK corpus
search.py: query the index
dictionary.txt: contain the dictionary for the index
postings.txt: contain the posting list for all words that appear in the corpus
doc_norm.txt: normalization term for each document  
queries.txt: contain queries separated by lines
output.txt: contain lists of docID for each query in queries.txt


== Statement of individual work ==


We, A0121585H, and A0156136H certify that we have followed the CS 3245 
Information Retrieval class guidelines for homework assignments. In particular, 
we expressly vow that we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  


== References ==

http://www.nltk.org/

To check on NLTK API

https://pymotw.com/2/pickle/

To understand how to use pickle