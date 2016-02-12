import nltk
from nltk.corpus import stopwords
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
# all the nominees
all_nominees = {}
all_presenters = {}

tweetsSortedByAward = {}

# For finding presenters, when we find a tweet we think is related to an award, pick from the official award list which
# award the tweet relates to.  This way we can later search just the related tweets for "present" or "envelope" and a
# name.

# alternatively we can associate our determined award names (rather than the official ones) with the tweets for the
# same reason.

def sortTweets(year):
    global tweetsSortedByAward
    strings = yearMap[year]['strings']
    isAwardPattern = re.compile(r'best|award', re.IGNORECASE)
    # remove stoplisted words from the sets we will compare to the tweets, and then make a set out of these tokenized versions
    awardSets = (set(w for w in lst if w not in nltk.stopwords) for lst in jsonTokenizer(OFFICIAL_AWARDS))


    for j in range(len(strings)):
        tweet = strings[j]
        if re.search(isAwardPattern, tweet):
            tweetTokenized = [w.lower() for w in wordpunct_tokenize(tweet)]
            max = 0
            bestIndex = -1
            tweetSet = set(tweetTokenized)
            for i in range(len(awardSets)):
                currLen = len(tweetSet & awardSets[i])
                if currLen > max:
                    max = currLen
                    bestIndex = i
            if bestIndex != -1:
                try:
                    tweetsSortedByAward[OFFICIAL_AWARDS[bestIndex]]
                except KeyError:
                    tweetsSortedByAward[OFFICIAL_AWARDS[bestIndex]] = []
                tweetsSortedByAward[OFFICIAL_AWARDS[bestIndex]].append(j)
    return



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

def get_all(year):
    if len(list(all_nominees))>0:
        return
    strings = yearMap[year]['strings']
    nom_patterns = []
    pres_patterns = []
    namePattern = re.compile(r'[A-Z]\w* [A-Z]\w*')

    # patterns for finding nominees
    nom_patterns.append(re.compile(r'nom', re.IGNORECASE))
    nom_patterns.append(re.compile(r'should.*w[io]n', re.IGNORECASE))
    nom_patterns.append(re.compile(r'will win', re.IGNORECASE))
    nom_patterns.append(re.compile(r'gonna win', re.IGNORECASE))

    # patterns for finding presenters
    pres_patterns.append(re.compile(r'present',re.IGNORECASE))
    pres_patterns.append(re.compile(r'envelope',re.IGNORECASE))
    pres_patterns.append(re.compile(r'announc',re.IGNORECASE))

    stoplist = ['globes','golden','best','movie','motion','picture','film','drama','comedy','musical','cecil','demille','award','tv','performance', 'actress','actor','television','feature','foreign','language','supporting','role','director','original','series']

    noms = {}
    preses = {}

    for award in awardTweets.keys():
        noms[award] = Counter()
        tweets = awardTweets[award]

        for tweet in tweets:
            # get nominees
            for pat in nom_patterns:
                if re.search(pat, tweet):
                    matches = re.findall(namePattern, tweet)
                    matches = (w.lower() for w in matches)
                    for match in matches:
                        noms[award][match]+=1

            #get presenters
            for pat in pres_patterns:
                if re.search(pat, tweet):
                    matches = re.findall(namePattern, tweet)
                    matches = (w.lower() for w in matches)
                    for match in matches:
                        preses[award][match]+=1


    nominees = {}
    presenters = {}
    for award in noms.keys():
        counter = 10
        award_noms = []
        while len(award_noms)<5:
            curr_noms = noms[award].most_common(counter)
            for n in curr_noms:
                add = True
                for w in stoplist:
                    if w in n:
                        add = False
                        break
                if add:
                    award_noms.append(n)
                counter+=10
        nominees[award]=award_noms

        award_preses = []
        while len(award_preses)<2:
            curr_preses = preses[award].most_common(counter)
            for p in curr_preses:
                add = True
                for w in stoplist:
                    if w in p:
                        add = False
                        break
                if add:
                    award_preses.append(n)
                counter+=10

        
        if preses[award][award_preses[1]] < preses[award][award_preses[0]]*0.75:
            presenters[award] = [award_preses[0]]
        else:
            presenters[award] = award_preses[0:2]
    
    all_nominees = nominees
    all_presenters = presenters
    return


def get_nominees(year):
    '''Nominees is a dictionary with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change
    the name of this function or what it returns.'''
    #Your code here
    if len(list(all_nominees))<0:
        get_all(year)

    nominees = {}
    for award in all_nominees.keys():
        nominees[award] = all_nominees[award][1:5]

    return nominees
    

def get_winners(year):
    '''Winners is a dictionary with the hard coded award
    names as keys, and each entry containing a single string.
    Do NOT change the name of this function or what it returns.'''
    if len(list(all_nominees))<0:
        get_all(year)

    nominees = {}
    for award in all_nominees.keys():
        nominees[award] = all_nominees[award][0]

    return nominees
    


def get_presenters(year):
    '''Presenters is a dictionary with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change the
    name of this function or what it returns.'''
    # Your code here
    if len(list(all_presenters))<0:
        get_all(year)
    
    return all_presenters



def jsonStrings (fileid):
    # using json libraries
    strings = []
    with open(fileid) as f:
        jsons = json.load(f)
    for item in jsons:
        text = item['text']
        strings.append(text)
    return strings

# Takes a list of tweet strings and returns a list of tokenized lists
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
    print "Welcome to the Golden Globes API. Please wait."
    
    pre_ceremony()

    print "Ok, I'm ready." 
    year = get_year()
    
    while True:
        print "We will be looking at " + year + ". \n What would you like to do?"
        print "1: Get award names"
        print "2: Get nominees"
        print "3: Get winners"
        print "4: Get host(s)"
        print "5: Get presenters"
        print "6: Change year"
        print "7: Exit"

        choices = ["1","2","3","4","5","6", "7"]

        func = raw_input("Enter choice number: ")
        while func not in choices:
            func = raw_input("Please enter a number 1-7: ")  

        result = 0
        if func == "1":
            result = award_names(int(year))
            continue
        elif func == "2":
            result = get_nominees(int(year))
            continue
        elif func == "3":
            result = get_winners(int(year))
        elif func == "4":
            result = get_hosts(int(year))
        elif func == "5":
            result = get_presenters(int(year))
        elif func == "6":
            year = get_year()
        elif func == "6":
            result = get_year()
        elif func == "7":
            break

        if result != 0:
            if isinstance(result, dict):
                print_dict(result)
            elif isinstance(result, list):
                print_list(result)

    return

def print_dict(d):
    for (k,v) in d:
        print k + ": \n" + print_list(v)

def print_list(l):
    for x in l:
        print "\t"+x+"\n"

def get_year():
    year = raw_input("What year would you like me to look into? \n")
    
    while year != "2013" and year != "2015":
         year = raw_input("Sorry, that year isn't valid. Please enter 2013 or 2015. What year would you like me to look into? \n")
    
    return year

if __name__ == '__main__':
    main()
