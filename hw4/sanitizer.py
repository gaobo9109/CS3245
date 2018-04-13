import nltk
import re
import os

"""
This is a sanitizer designed for hw4
To use this, you just need to import the Sanitizer class and new a sanitizer
object and then you can do sanitizing. You could change the stop words in
'stop_words.txt'.
"""

DEFAUIT_INVALID_CHARS = r'[^\w\d\s\-]+'
DEFAULT_JUDGMENT_KEY = 'Judgment:'

PATH_NOT_VALID_MESSAGE = 'Stop words path is not valid.'

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STOP_WORD_PATH = os.path.join(SCRIPT_PATH, './stop_words.txt')

class Sanitizer:

    def tokenize(self, text, remove_stop_words=True):
        """Tokenizes text by removing invalid characters, putting to lower case and stemming
        Return a list of sanitized tokens from the given text"""
        tokens = map(lambda t: re.sub(self.invalid_regex, '', t), nltk.word_tokenize(text))
        tokens = map(lambda t: self.ps.stem(t.lower()), filter(None, tokens))
        if remove_stop_words:
            tokens = filter(lambda t: t not in self.stop_words, tokens)
        return tokens

    def extract_judgment(self, content, judgment_key=DEFAULT_JUDGMENT_KEY):
        """Extracts the judgement part accroding to the key word
        Returns a text block (string) of judgement text
        """
        return content.split(judgment_key)[1]

    def __read_stop_words(self, path):
        """Reads the stop words from a give path.
        Returns a set of stop words
        """
        stop_words = set()
        path_valid = os.path.exists(path)
        assert path_valid, PATH_NOT_VALID_MESSAGE
        with open(path) as stop_word_file:
            for word in stop_word_file:
                stop_words.add(self.tokenize(word.strip(), False)[0])
        return stop_words

    def __init__(self, stop_word_path=DEFAULT_STOP_WORD_PATH, invalid_chars=DEFAUIT_INVALID_CHARS):
        self.invalid_regex = re.compile(invalid_chars)
        self.ps = nltk.stem.PorterStemmer()
        self.stop_words = self.__read_stop_words(stop_word_path)
