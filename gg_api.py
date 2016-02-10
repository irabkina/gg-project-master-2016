import nltk
import re
import json

from nltk.tokenize import wordpunct_tokenize
from collections import Counter

OFFICIAL_AWARDS = ['cecil b. demille award', 'best motion picture - drama', 'best performance by an actress in a motion picture - drama', 'best performance by an actor in a motion picture - drama', 'best motion picture - comedy or musical', 'best performance by an actress in a motion picture - comedy or musical', 'best performance by an actor in a motion picture - comedy or musical', 'best animated feature film', 'best foreign language film', 'best performance by an actress in a supporting role in a motion picture', 'best performance by an actor in a supporting role in a motion picture', 'best director - motion picture', 'best screenplay - motion picture', 'best original score - motion picture', 'best original song - motion picture', 'best television series - drama', 'best performance by an actress in a television series - drama', 'best performance by an actor in a television series - drama', 'best television series - comedy or musical', 'best performance by an actress in a television series - comedy or musical', 'best performance by an actor in a television series - comedy or musical', 'best mini-series or motion picture made for television', 'best performance by an actress in a mini-series or motion picture made for television', 'best performance by an actor in a mini-series or motion picture made for television', 'best performance by an actress in a supporting role in a series, mini-series or motion picture made for television', 'best performance by an actor in a supporting role in a series, mini-series or motion picture made for television']
path = 'tweets'

yearMap = {}
reader = None
docs = None



def get_hosts(year):
    '''Hosts is a list of one or more strings. Do NOT change the name
    of this function or what it returns.'''
    strings = yearMap[year]['strings']
    hostPattern = re.compile(r'hosts?', re.IGNORECASE)
    namePattern = re.compile(r'[A-Z]\w* [A-Z]\w*', re.IGNORECASE) # ?([A-Z]\w*)?

    host_mentions = Counter()
    for tweet in strings:
        if re.search(hostPattern, tweet):
            matches = re.findall(namePattern, tweet)
            matches = (w.lower() for w in matches)
            for match in matches:
                host_mentions[match] += 1

    hosts = host_mentions.most_common(10)
    return hosts

def get_awards(year):
    '''Awards is a list of strings. Do NOT change the name
    of this function or what it returns.'''
    # Your code here
    awards = []
    return awards

def get_nominees(year):
    '''Nominees is a list of dictionaries with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change
    the name of this function or what it returns.'''
    # Your code here
    nominees = []
    return nominees

def get_winners(year):
    '''Winners is a list of dictionaries with the hard coded award
    names as keys, and each entry a list containing a single string.
    Do NOT change the name of this function or what it returns.'''
    # Your code here
    winners = []
    return winners

def get_presenters(year):
    '''Presenters is a list of dictionaries with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change the
    name of this function or what it returns.'''
    # Your code here
    presenters = []
    return presenters

def strings(reader, fileids=None):
        # """
        # Returns only the text content of Tweets in the file(s)
        #
        # :return: the given file(s) as a list of Tweets.
        # :rtype: list(str)
        # """
        #
        #
        #
        #
        # NOTE: adapted from TwitterCorpusReader.strings
        global docs
        if docs is None:
            docs = reader.docs(fileids)
        print len(docs)
        tweets = []
        for jsono in docs:
            #print jsono
            if isinstance(jsono, list):
                jsono = jsono[0]
            try:
                text = jsono['text']
                if isinstance(text, bytes):
                    text = text.decode(reader.encoding)
                tweets.append(text)
            except KeyError:
                pass
        return tweets


def jsonStrings (fileid):
    # using json libraries
    strings = []
    with open(fileid) as f:
        jsons = json.load(f)
    for item in jsons:
        text = item['text']
        strings.append(text)
    return strings

def jsonTokenizer(tweets):
    tokens = []
    for tweet in tweets:
        tokens.append(wordpunct_tokenize(tweet))
    return tokens

def tokenized(reader, strings):
    # NOTE: adapted from TwitterCorpusReader.strings
        """
        :return: the given file(s) as a list of the text content of Tweets as
        as a list of words, screenanames, hashtags, URLs and punctuation symbols.

        :rtype: list(list(str))
        """
        tweets = strings
        tokenizer = reader._word_tokenizer
        return [tokenizer.tokenize(t) for t in tweets]

def pre_ceremony():
    '''This function loads/fetches/processes any data your program
    will use, and stores that data in your DB or in a json, csv, or
    plain text file. It is the first thing the TA will run when grading.
    Do NOT change the name of this function or what it returns.'''
    # Your code here
    # global reader
    # reader = nltk.corpus.reader.twitter.TwitterCorpusReader(root=path, fileids = ['gg2013.json', 'gg2015.json'])
    global yearMap
    print "finished creating reader"
    yearMap[2013] = {}
    yearMap[2015] = {}
    yearMap[2013]['strings'] = 'testing'
    print yearMap[2013]['strings']
    yearMap[2013]['strings'] = jsonStrings('tweets/gg2013.json')
    print "finished creating 2013 strings"
    # yearMap[2015]['strings'] = jsonStrings('tweets/gg2015.json')
    # print "finished creating 2015 strings"
    yearMap[2013]['tokens'] = jsonTokenizer(yearMap[2013]['strings'])
    print "finished creating 2013 tokens"
    # yearMap[2015]['tokens'] = jsonTokenizer(yearMap[2015]['strings'])
    # print "Pre-ceremony processing complete."
    return

def main():
    '''This function calls your program. Typing "python gg_api.py"
    will run this function. Or, in the interpreter, import gg_api
    and then run gg_api.main(). This is the second thing the TA will
    run when grading. Do NOT change the name of this function or
    what it returns.'''
    # Your code here
    pre_ceremony()
    print get_hosts(2013)
    print yearMap[2013]['tokens'][0]
    return

if __name__ == '__main__':
    main()
