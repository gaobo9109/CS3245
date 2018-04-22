import nltk
import re
import numpy
import os
from nltk.corpus import stopwords

"""
This is a sanitizer designed for hw4
To use this, you just need to import the Sanitizer class and new a sanitizer
object and then you can do sanitizing. You could change the stop words in
'stop_words.txt'.
"""

DEFAULT_INVALID_CHARS = re.compile(r'[^a-z\s\-]+', re.I)
DEFAULT_JUDGEMENT_REGEX = re.compile(r'judge?ment:?\n', re.I)
DEFAULT_JUDGEMENT_KEY = 'judgment'
LINE_BREAK = re.compile(r'\n')
WHITE_SPACE = re.compile(r'\s+')

PATH_NOT_VALID_MESSAGE = 'Stop words path is not valid.'

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

class Sanitizer:

    def tokenize(self, text, remove_stop_words=True):
        """Tokenizes text by removing invalid characters, putting to lower case and stemming
        Return a list of sanitized tokens from the given text"""
        tokens = map(lambda t: re.sub(self.invalid_regex, '', t), nltk.word_tokenize(text.decode('utf-8')))
        tokens = map(lambda t: self.ps.stem(t.lower()), filter(None, tokens))
        if remove_stop_words:
            tokens = filter(lambda t: t not in self.stop_words, tokens)
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
                continue
            break_index = i
            break
        return '\n'.join(breaked[break_index:])

    def extract_judgement(self, content, judgement_regex=DEFAULT_JUDGEMENT_REGEX):
        """Extracts the judgement part accroding to the key word
        Returns a text block (string) of judgement text
        """
        temp = re.split(judgement_regex, content)
        if len(temp) > 2:
            result_content = self.__merge_content_after(temp, 1, DEFAULT_JUDGEMENT_KEY)
        elif len(temp) < 2:
            result_content = self.__extract_without_key(content)
        else:
            result_content = temp[1]
        return result_content

    def __init__(self, stop_word_path=DEFAULT_STOP_WORD_PATH, invalid_chars=DEFAULT_INVALID_CHARS):
        self.invalid_regex = re.compile(invalid_chars)
        self.ps = nltk.stem.PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
