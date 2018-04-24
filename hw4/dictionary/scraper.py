from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
import pickle
import requests
import re

url = 'http://www.tysto.com/uk-us-spelling-list.html'
stemmer = PorterStemmer()


def get_words(tag):
    return map(lambda w: stemmer.stem(w), re.split('\s*\n\s*', tag.get_text().strip()))


page = requests.get(url)
html = BeautifulSoup(page.content, "html.parser")

table = html.select_one('tr.Body')
uk, us = table.select('td')

dictionary = {}
for uk_word, us_word in zip(get_words(us), get_words(uk)):
    if uk_word and us_word and uk_word != us_word:
        dictionary[us_word] = uk_word


pickle.dump(dictionary, open('../us-uk.pkl', 'wb'))
