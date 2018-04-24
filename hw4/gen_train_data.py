import nltk
import csv
import pickle
from sanitizer import Sanitizer
from multiprocessing import Pool

csv.field_size_limit(2**30)
sanitizer = Sanitizer()
filename = 'dataset.csv'


def generate_training_data(row):
    document_id, title, content, date_posted, court = row
    judgement = sanitizer.extract_judgement(content)
    sentences = nltk.sent_tokenize(unicode(judgement, errors='ignore'))
    return map(sanitizer.tokenize, sentences)


if __name__ == "__main__":
    reader = csv.reader(open(filename, 'rb'))
    reader.next()
    
    pool = Pool()
    results = pool.map(generate_training_data, reader)
    sentences = []
    for sent in results:
        sentences.extend(sent)

    with open('sentences.txt', 'w') as f:
        for sentence in sentences:
            f.write(' '.join(sentence) + '\n')
