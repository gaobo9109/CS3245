from nltk.corpus import stopwords

SANITIZE_CUTOFF = 0.3
SYNONYM_CUTOFF = 0.8
DOCUMENTS_FILENAME = 'documents.pkl'

STOPWORDS = set(stopwords.words('english'))

# We can squeeze a 8 byte double into 3 VBE bytes with some loss of precision by multiplying it
# by some large int and truncating the rest of the decimal points
#
# Three byte variable byte encoding gives us 21 bits = max value of 2097152
# Given our max tf is around ~5.0, we can use multiplier values of up to 2097152 / 5 = 419430
# 300000 is chosen as a safe upper limit with some safety
TF_MULTIPLIER = 300000
