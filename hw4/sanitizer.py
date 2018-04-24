import nltk
import re
import numpy
import pickle
from config import *

"""
This is a sanitizer designed for hw4
To use this, you just need to import the Sanitizer class and new a sanitizer
object and then you can do sanitizing. You could change the stop words in
'stop_words.txt'.
"""

DEFAULT_INVALID_CHARS = re.compile(r'[^a-z\s\-]+', re.I)
DEFAULT_JUDGEMENT_REGEX = re.compile(r'^\s*judge?ment\s*:?\s*\n', re.I)

PAGE_NUMBER_REGEX = re.compile(r'\[Page \d+\]', re.I)
DISCLAIMER_PREFIX = 'DISCLAIMER - Every effort has been made to comply'
CDATA_SUFFIX = '//]]>'

LINE_BREAK = re.compile(r'\n+')
WHITE_SPACE = re.compile(r'\s+')


def remove_until(text, pattern):
    match = re.search(pattern, text)
    if not match:
        return text

    return text[match.end():]


def remove_from(text, pattern):
    match = re.search(pattern, text)
    if not match:
        return text

    return text[:match.start()]


class Sanitizer:
    def sanitize(self, text):
        # Remove JS junk from top of text
        text = remove_until(text, CDATA_SUFFIX)
        text = remove_from(text, DISCLAIMER_PREFIX)

        text = self.remove_page_numbers(text)
        return self.extract_judgement(text)

    def tokenize(self, text):
        """Tokenizes text by removing invalid characters, putting to lower case and stemming
        Return a list of sanitized tokens from the given text"""
        # Remove invalid characters, make lowercase
        text = re.sub(self.invalid_regex, ' ', text.decode('utf-8').lower())

        # Tokenize and remove stop words
        tokens = filter(lambda t: t not in STOPWORDS, nltk.word_tokenize(text))

        # Stem all tokens
        tokens = map(self.ps.stem, filter(None, tokens))

        # US to UK translation
        tokens = map(lambda t: self.us_to_uk.get(t, t), tokens)

        return tokens

    def __merge_content_after(self, array, index, key):
        """Merges the array after certain index with a key"""
        merged = key.join(array[index:])
        return merged

    def __extract_without_key(self, content):
        """In order to deal with those documents that do not have 'judgment' key.
        The basic idea is that break the document to paragraphs (according to new line)
        Keep an average value of the first k paragraphs. When the k + 1 element is
        greater than double of the size of the average, regard the paragraphs
        from k + 1 are from content
        """
        breaked = re.split(LINE_BREAK, content)
        white_removed = [re.sub(WHITE_SPACE, '', line) for line in breaked]
        sample = white_removed[:2]
        average_length = numpy.mean([len(x) for x in sample])

        break_index = 0
        for i in range(2, len(white_removed)):
            if len(white_removed[i]) < average_length * 2:
                average_length = numpy.mean([average_length, len(white_removed[i])])
            else:
                break_index = i
                break
        return '\n'.join(breaked[break_index:])

    def extract_judgement(self, content, judgement_regex=DEFAULT_JUDGEMENT_REGEX):
        """Extracts the judgement part according to the key word
        Returns a text block (string) of judgement text
        """
        match = re.search(judgement_regex, content)
        if match:
            return content[match.end():]
        else:
            return self.__extract_without_key(content)

    def remove_page_numbers(self, content):
        return re.sub(PAGE_NUMBER_REGEX, ' ', content)

    def __init__(self, invalid_chars=DEFAULT_INVALID_CHARS):
        self.invalid_regex = re.compile(invalid_chars)
        self.ps = nltk.stem.PorterStemmer()

        try:
            with open('us-uk.pkl', 'rb') as f:
                self.us_to_uk = pickle.load(f)
        except IOError as e:
            print 'Cannot load US-UK translation table'
            print e

            self.us_to_uk = {}

