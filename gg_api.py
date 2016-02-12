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
#award names mapped to list of tweet indices about that award
awardTweets = {}

# For finding presenters, when we find a tweet we think is related to an award, pick from the official award list which
# award the tweet relates to.  This way we can later search just the related tweets for "present" or "envelope" and a
# name.

# alternatively we can associate our determined award names (rather than the official ones) with the tweets for the
# same reason.


def get_hosts(year):
    '''Hosts is a list of one or more strings. Do NOT change the name
    of this function or what it returns.'''
    strings = yearMap[year]['strings']
    hostPattern = re.compile(r'hosts?', re.IGNORECASE)
    namePattern = re.compile(r'[A-Z]\w* [A-Z]\w*') #, re.IGNORECASE) # ?([A-Z]\w*)?

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
    global awardTweets
    strings = yearMap[year]['strings']
    genAwardPattern = re.compile(r'(best .*)(drama|musical|film|picture|television)', re.IGNORECASE)
    award_mentions = Counter()

    for i in range(len(strings)):
        match = re.findall(genAwardPattern, strings[i])
        # matches = [m for m in match]
        match = (w[0].lower()+w[1].lower() for w in match)
        for m in match:
            try:
                awardTweets[m]
            except KeyError:
                awardTweets[m] = []
            awardTweets[m].append(i)
            award_mentions[m] += 1

    awards_tuples = award_mentions.most_common()

    comma = re.compile(r',|\"|\'')
    awards_tuples_filter = []
    for a in awards_tuples:
        if not re.search(comma, a[0]):
            awards_tuples_filter.append(a)
        else:
            del awardTweets[a[0]]

    awards_tuples = awards_tuples_filter

    awards_tokenized = jsonTokenizer([a[0] for a in awards_tuples])

    awards_sets = [set(a) for a in awards_tokenized]

    awards = []

    for i in range(len(awards_sets)):
        include = True
        for j in range(len(awards_sets)):
            if awards_sets[i] < awards_sets[j] and awards_tuples[j][1] > 1:
                awards_tuples[j] = (awards_tuples[j][0], awards_tuples[i][1]+awards_tuples[j][1])
                awardTweets[awards_tuples[j][0]] += awardTweets[awards_tuples[i][0]]
                include = False
                break
        if include:
            awards.append(awards_tuples[i])

    awards.sort(reverse=True, key=lambda x: x[1])

    awards = awards

    return awards

def get_nominees(year):
    '''Nominees is a dictionary with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change
    the name of this function or what it returns.'''
    # Your code here
    strings = yearMap[year]['strings']
    nom_patterns = []
    award_patterns = {}
    namePattern = re.compile(r'[A-Z]\w* [A-Z]\w*')

    # patterns for finding nominees
    nom_patterns.append(re.compile(r'nom', re.IGNORECASE))
    nom_patterns.append(re.compile(r'should.*w[io]n', re.IGNORECASE))
    nom_patterns.append(re.compile(r'will win', re.IGNORECASE))
    nom_patterns.append(re.compile(r'gonna win', re.IGNORECASE))

    # patterns for awards
    award_patterns['cecil b. demille award'] = re.compile(r'((cecil)|(demille)).*award', re.IGNORECASE)
    award_patterns['best motion picture - drama'] = re.compile(r'best ((film)|(movie)|(motion picture)).*drama', re.IGNORECASE)
    award_patterns['best performance by an actress in a motion picture - drama'] = re.compile(r'best actress.*((film)|(movie)|(motion picture)).*drama', re.IGNORECASE)
    award_patterns['best performance by an actor in a motion picture - drama'] = re.compile(r'best actor.*((film)|(movie)|(motion picture)).*drama', re.IGNORECASE)
    award_patterns['best motion picture - comedy or musical'] = re.compile(r'best ((film)|(movie)|(motion picture)).*((comedy)|(musical))', re.IGNORECASE)
    award_patterns['best performance by an actress in a motion picture - comedy or musical'] = re.compile(r'best actress.*((film)|(movie)|(motion picture)).*((comedy)|(musical))', re.IGNORECASE)
    award_patterns['best performance by an actor in a motion picture - comedy or musical'] = re.compile(r'best actor.*((film)|(movie)|(motion picture)).*((comedy)|(musical))', re.IGNORECASE)
    award_patterns['best animated feature film'] = re.compile(r'best animated ((film)|(movie)|(motion picture))', re.IGNORECASE)
    award_patterns['best foreign language film'] = re.compile(r'best foreign (language )?((film)|(movie)|(motion picture))', re.IGNORECASE)
    award_patterns['best performance by an actress in a supporting role in a motion picture'] = re.compile(r'best supporting actress.*((film)|(movie)|(motion picture))', re.IGNORECASE)
    award_patterns['best performance by an actor in a supporting role in a motion picture'] = re.compile(r'best supporting actor.*((film)|(movie)|(motion picture))', re.IGNORECASE)
    award_patterns['best director - motion picture'] = re.compile(r'best director.*((film)|(movie)|(motion picture))', re.IGNORECASE)
    award_patterns['best screenplay - motion picture'] = re.compile(r'best screenplay.*((film)|(movie)|(motion picture))', re.IGNORECASE)
    award_patterns['best original score - motion picture'] = re.compile(r'best (original )?score.*((film)|(movie)|(motion picture))', re.IGNORECASE)
    award_patterns['best original song - motion picture'] = re.compile(r'best (original )?song.*((film)|(movie)|(motion picture))', re.IGNORECASE)
    award_patterns['best television series - drama'] = re.compile(r'best ((television )|(tv ))series.*drama', re.IGNORECASE)
    award_patterns['best performance by an actress in a television series - drama'] = re.compile(r'best actress.*((television)|(tv)).*series.*drama', re.IGNORECASE)
    award_patterns['best performance by an actor in a television series - drama'] = re.compile(r'best actor.*((television)|(tv)).*series.*drama', re.IGNORECASE)
    award_patterns['best television series - comedy or musical'] = re.compile(r'best ((television )|(tv ))series.*((comedy)|(musical))', re.IGNORECASE)
    award_patterns['best performance by an actress in a television series - comedy or musical'] = re.compile(r'best actress.*((television)|(tv)).*series.*((comedy)|(musical))', re.IGNORECASE)
    award_patterns['best performance by an actor in a television series - comedy or musical'] = re.compile(r'best actor.*((television)|(tv)).*series.*((comedy)|(musical))', re.IGNORECASE)
    award_patterns['best mini-series or motion picture made for television'] = re.compile(r'best.*((mini-series)|(made for))', re.IGNORECASE)
    award_patterns['best performance by an actor in a mini-series or motion picture made for television'] = re.compile(r'best actor.*((mini-series)|(made for))', re.IGNORECASE)
    award_patterns['best performance by an actress in a mini-series or motion picture made for television'] = re.compile(r'best actress.*((mini-series)|(made for))', re.IGNORECASE)
    award_patterns['best performance by an actress in a supporting role in a series, mini-series or motion picture made for television'] = re.compile(r'best supporting actress.*((mini-series)|(made for))', re.IGNORECASE)
    award_patterns['best performance by an actor in a supporting role in a series, mini-series or motion picture made for television'] = re.compile(r'best supporting actor.*((mini-series)|(made for))', re.IGNORECASE)

    noms = {}
    for tweet in strings:
        for award in award_patterns.keys():
            if award not in noms.keys():
                noms[award] = Counter()
            pat = award_patterns[award]
            if re.search(pat, tweet):
                matches = re.findall(namePattern, tweet)
                matches = (w.lower() for w in matches)
                for match in matches:
                    noms[award][match]+=1

    nominees = {}
    for award in noms.keys():
        nominees[award]=noms[award].most_common(5)
    
    return nominees

def get_winners(year):
    '''Winners is a dictionary with the hard coded award
    names as keys, and each entry containing a single string.
    Do NOT change the name of this function or what it returns.'''
    strings = yearMap[year]['strings']
    nominees = get_nominees(year)

    patterns = {}
    for lst in nominees.values():
        for nom in lst:
            pats = []
            pats.append(re.compile(r'best.*actor.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'best.*actress.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'best.*movie.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'best.*film.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'best.*show.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'best.*director.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'best.*screenplay.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'best original.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'best.*series.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'cecil.*'+nom, re.IGNORECASE))
            pats.append(re.compile(r'demille.*'+nom, re.IGNORECASE))
            pats.append(re.compile(nom+r'.*w[io]n[s].*', re.IGNORECASE))
            pats.append(re.compile(r'congrat.*'+nom, re.IGNORECASE))
            patterns[nom] = pats

    noms_mentions = Counter()
    for tweet in strings:
        for nom in patterns.keys():
            for pat in patterns[nom]:
                if re.search(pat, tweet):
                    noms_mentions[nom]+=1

    winner_dict = {}
    for award in nominees.keys():
        bestCount = 0
        winner = ""
        for n in nominees[award]:
            if noms_mentions[n] > bestCount:
                winner = n
                bestCount = noms_mentions[n]
        winner_dict[award] = winner

    return winner_dict

def get_presenters(year):
    '''Presenters is a dictionary with the hard coded award
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

def tokenizeNoPunctuation(tweets):
    tokens = []
    stoplist = [',', '(', ')', '.', '?', '/', '-', '+', ':', ';']
    for tweet in tweets:
        tokenized = wordpunct_tokenize(tweet)
        tokens.append([token for token in tokenized if token not in stoplist])
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
    #yearMap[2015]['strings'] = jsonStrings('tweets/gg2015.json')
    #print "finished creating 2015 strings"
    #yearMap[2013]['tokens'] = jsonTokenizer(yearMap[2013]['strings'])
    #print "finished creating 2013 tokens"
    #yearMap[2015]['tokens'] = jsonTokenizer(yearMap[2015]['strings'])
    print "Pre-ceremony processing complete."
    return

def main():
    '''This function calls your program. Typing "python gg_api.py"
    will run this function. Or, in the interpreter, import gg_api
    and then run gg_api.main(). This is the second thing the TA will
    run when grading. Do NOT change the name of this function or
    what it returns.'''
    # Your code here
    pre_ceremony()
    #print get_hosts(2013)
    #print yearMap[2013]['tokens'][0]
    #print get_winners(2013)
    get_awards(2013)
    global awardTweets
    print awardTweets.keys()[:10]
    return

if __name__ == '__main__':
    main()
