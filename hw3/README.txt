This is the README file for A0121585H and A0156136H's submission
Email: a0121585@u.nus.edu
       a0156136@u.nus.edu

== Python Version ==

We're using Python Version 2.7 for this assignment.

== General Notes about this assignment ==

During index .....


During searching, we first tokenize the query, and perform stemming and case-folding on each
query term. Stop words are removed since they have low idf and do not have much effect on final 
ranking. For each query term, we then compute its tf and idf, and construct tf-idf vector for the 
entire query. We then extract posting list associated with each query term. The cos similarity score
for each document is computed using the described algorithm in the lecture note. Finally, we use python heapq to heapify the list of cos similarity score, extract the top 10 scores and their respective doc id. 


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