from __future__ import division
import nltk
import re
import pickle
from config import *

"""
This is a sanitizer designed for hw4
To use this, you just need to import the Sanitizer class and new a sanitizer
object and then you can do sanitizing. You could change the stop words in
'stop_words.txt'.
"""

# Remove all non-ASCII, whitespace and - (dash) characters
DEFAULT_INVALID_CHARS = re.compile(r'[^a-z\s\-]+', re.I)

# Regex used to split off judgement from the metadata at the start of the document
JUDGEMENT_DELIMITERS = [
    # Try to match the word JUDGEMENT as it appears in the various forms. Take note of
    #  - Whitespace in front and behind
    #  - American vs. British spelling (extra 'e' after 'g')
    #  - Colon afterwards
    #  - Space B E T W E E N each character
    #  - Match when it is the only word on the line (anchor to start and end line breaks)
    re.compile(r'(^|\n)\s*j\s*u\s*d\s*g\s*e*\s*m\s*e\s*n\s*t\s*:?\s*\n', re.I),

    re.compile(r'EX TEMPORE JUDGMENT\s', re.I),
    re.compile(r'\sTHE COURT (DECLARES|ORDERS) THAT:?\s', re.I),
    re.compile(r'\sJudge?ment\s+Reserved.?\s', re.I),

    re.compile(r'\n\s*Cur\s+Adv\s+Vult\s*\n', re.I),

    re.compile(r'\n\s*REASONS\s+FOR\s+JUDGE?MENT\s*\n'),

    re.compile(r'^\s*REMARKS\s+ON\s+SENTENCE\b', re.I),
]

# For removing boilerplate text at the end of content
DOCUMENT_END_PREFIX = [
    'DISCLAIMER - Every effort has been made to comply',
    'I certify that the preceding',
]

RESTRICTED_TEXT_REGEX = re.compile(r'The text of decision for[^\n]*has been restricted', re.I)

# For removing other junk in the documents
PAGE_NUMBER_REGEX = re.compile(r'\[Page \d+\]', re.I)
CSS_SUFFIX = '!important;}'

LINE_BREAK = re.compile(r'\n+')
WHITE_SPACE = re.compile(r'\s+')


def remove_until(text, pattern):
    match = re.search(pattern, text)
    if not match:
        return text

    return text[match.end():]


def remove_from(text, pattern):
    match = text.rfind(pattern)
    if match == -1:
        return text

    return text[:match]


class Sanitizer:
    def sanitize(self, text):
        # Remove page number embedded inside text
        text = self.remove_page_numbers(text)

        # Remove JS junk from the text
        text = self.remove_cdata(text)

        # Remove disclaimer text and other boilerplate at the end of the text
        for prefix in DOCUMENT_END_PREFIX:
            text = remove_from(text, prefix)

        # Try to extract the judgement from the text
        text = self.extract_judgement(text)

        return text

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
        if self.us_to_uk:
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
        from k + 1 are from content"""
        lines = filter(str.strip, re.split(LINE_BREAK, content))
        line_lengths = map(lambda line: len(self.__remove_whitespace(line)), lines)

        if len(lines) < 2:
            return content

        if line_lengths[0] > 500:
            return content

        total_length = sum(line_lengths)
        current_length = line_lengths[0]

        i = 1
        for i in range(1, len(lines)):
            line_len = line_lengths[i]
            if line_len < (current_length / i) * 2 and current_length < total_length * SANITIZE_CUTOFF:
                current_length += line_len
            else:
                break

        return '\n'.join(lines[i-1:])

    def __remove_whitespace(self, line):
        return re.sub(WHITE_SPACE, '', line)

    def extract_judgement(self, content):
        """Extracts the judgement part according to the key word
        Returns a text block (string) of judgement text"""
        for regex in JUDGEMENT_DELIMITERS:
            match = re.search(regex, content)

            if match and (match.end() < 1000 or match.end() / len(content) < SANITIZE_CUTOFF):
                return content[match.end():]

        return self.__extract_without_key(content)

    def remove_page_numbers(self, content):
        return re.sub(PAGE_NUMBER_REGEX, ' ', content)

    def remove_cdata(self, content):
        start = content.find('//<![CDATA')
        while start != -1:
            end = content.find('//]]>', start)
            if end == -1:
                break

            content = content[:start] + content[end + len('//]]>'):]
            start = content.find('//<![CDATA')

        return content

    def is_restricted_document(self, content):
        return 'The text of this decision has been restricted' in content \
               or re.search(RESTRICTED_TEXT_REGEX, content)

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
