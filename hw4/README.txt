This is the README file for AXXXXXXXX, AXXXXXXXX, A0121585H and A0156136H's submission
Email:	XXXXXXXX@u.nus.edu
		XXXXXXXX@u.nus.edu
		a0121585@u.nus.edu
		e0032273@u.nus.edu

== Python Version ==

We're using Python Version 2.7 for this assignment.

== General Notes about this assignment ==

= Indexing =

index.py deploys multithreading to iterate through all the documents, then sanitizes and tokenizes the document into words.
The posting, a namedtuple of: (weighted tf, positional index and document id), is then generated for each word and added to
the posting list. The document, a named tuple of: (id, title, length (sum of the squares of weighted tfs), court) is generated 
and added to the document index.

= Sanitization & Tokenization =

For a given document, we remove any meta data that occurs at the start of a document, including page numbers, and consider only
the "Judgement" portion of the report. Then we tokenise words that are not stop words (according to nltk.corpus stopwords), 
converting them to lower case, removing all invalid characters, then performing porter stemming. We return the terms back to 
index.py.

= Writing & Encoding =

The finished postings list and dictionary is then written to postings.txt and dictionary.txt respectively. Variable byte 
encoding is used to compress the postings list.
The Dictionary is written as ???
The Documents list is written as a pickled object to documents.pkl

= Searching =

There are two cases for searching : Free text queries and boolean queries. A boolean query is identified by the existence of 
an "AND" in the query and has the possibility of including phrasal queries. 

For free text queries:
For each query term, the tf-idf is calculated and the tf-idf vector is constructed for the entire query. We then extract the
posting list associated with each query term. The cos similarity score for each document is computed, and the results are 
returned in order of relevance

For boolean queries:
???

= Query Expansion =
???

== Files included with this submission ==

index.py: to index the dataset
search.py: query the index
sanitizer.py: sanitises the content
dictionary.txt: contain the dictionary for the index
postings.txt: contain the posting list for all words that appear in the corpus


== Statement of individual work ==


We, AXXXXXXXX, AXXXXXXXX, A0121585H, and A0156136H certify that we have followed the CS 3245 
Information Retrieval class guidelines for homework assignments. In particular, 
we expressly vow that we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  


== References ==

