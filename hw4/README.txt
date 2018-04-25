This is the README file for A0135817B, AXXXXXXXX, A0121585H and A0156136H's submission
Email:	e0011848@u.nus.edu
		XXXXXXXX@u.nus.edu
		a0121585@u.nus.edu
		e0032273@u.nus.edu

== Python Version ==

We're using Python Version 2.7 for this assignment.

== General Notes about this assignment ==

Additional parameter flags added

- index.py: -m to enable multithreading. This increases memory usage but makes indexing significantly faster
- search.py: -e path/to/vector.model to enable query expansion using the given word2vec model

= Indexing =

We use three index files to keep track of all data

- postings.txt maps each term to their positions and tf in each document
- dictionary.txt maps each
- document.pkl maps the internal ID used to the real document ID, title, length, court and other metadata

index.py deploys multithreading to iterate through all the documents, then sanitizes and tokenizes the document into words.
Each term has a list of postings, and each posting consist of a namedtuple of (weighted tf, positional indices, id).
The document, a namedtuple of: (document_id, title, length (sum of the squares of weighted tfs), court) is
generated and added to the document index.


= Sanitization & Tokenization =

The documents provided are very noisy and contains a large amount of extraneous information as well as junk left by the
scraping/OCR process such as page numbers, bits of JavaScript embedded in the page and legal disclaimers. The sanitizer
is designed to strip all of these out from the data to improve index speed and quality. A number of documents
are also entirely empty because their content is restricted - these are also excluded from the index.

Zones and fields other than document's court are not used because the documents come from many different sources and
do not follow standard formats that make them easy to identify. If the original HTML was provided instead, it may be
possible to extract this information, but the plain text has too few reliable textual markers to allow zones to be
extracted.

For a given document, we remove any metadata that occurs at the start of a document, disclaimers and junk and consider
only the "Judgement" portion of the report. Then we tokenise words that are not stop words (according to nltk.corpus
stopwords); converting them to lowercase, removing all non letter, whitespace and hyphen characters; then performing
porter stemming. We also use an American to UK English translation table to standardize the spelling of English words
since the corpus contains documents from both sides of the Atlantic.

= Writing & Encoding =

Posting and Dictionary are binary files encoded using variable byte encoding. Documents is a Pickle file.

Index compression is employed heavily to ensure the index fits the required file size. Variable byte encoding is used to reduce
the size of all integers. tf is stored as a fixed point decimal, trading precision for size, and we remap all document
IDs to an internal ID of consecutive integers, which are smaller than the real document IDs. Incrementing integers
such as IDs and positional index are encoded as deltas, from which their original values are recalculated when the posting
is read. Each posting is encoded as id, tf, length of the positional index, followed by the positional index. This reduced
the posting file size by over 50% compared to the plain text format used in the previous homework.

The dictionary file also used variable byte encoding. Each dictionary entry is encoded as term length, document frequency,
byte offset followed by the term itself. This reduced the dictionary file from 10MB to just 2MB, at the cost of increased
read time.

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

config.py: contains tweakables
index.py: to index the dataset
search.py: query the index
sanitizer.py: sanitises the content
vbcode.py: contains the variable byte encoding implementation

dictionary.txt: contain the dictionary for the index
postings.txt: contain the posting list for all words that appear in the corpus
documents.pkl: contains metadata on all documents in the corpus

models/* : contains the word2vec models used for query expansion
train.py: the script used to train the word2vec model
gen_train_data.py: uses the sanitizer and tokenizer to generate training data for the model from the dataset

us-uk.pkl: US-UK English translation table
dictionary/scraper.py: The script used to scrape the above data


== Statement of individual work ==


We, A0135817B, AXXXXXXXX, A0121585H, and A0156136H certify that we have followed the CS 3245
Information Retrieval class guidelines for homework assignments. In particular, 
we expressly vow that we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  


== References ==

- Variable byte encoding code partly taken from https://github.com/utahta/pyvbcode/blob/master/vbcode.py
  which is just an implementation of the algorithm from the textbook, with our own modifications