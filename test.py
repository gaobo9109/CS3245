from nltk.tokenize import sent_tokenize, word_tokenize
import os

file_name = os.path.join("reuters","training","5")

with open(file_name, 'r') as file:
  data = file.read()
  sentences = sent_tokenize(data)
  for sentence in sentences:
    words = word_tokenize(sentence) 
