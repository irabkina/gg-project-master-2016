import nltk
from nltk.corpus import stopwords
import re
import json
import os.path

from nltk.tokenize import wordpunct_tokenize
from collections import Counter

OFFICIAL_AWARDS = ['cecil b. demille award', 'best motion picture - drama', 'best performance by an actress in a motion picture - drama', 'best performance by an actor in a motion picture - drama', 'best motion picture - comedy or musical', 'best performance by an actress in a motion picture - comedy or musical', 'best performance by an actor in a motion picture - comedy or musical', 'best animated feature film', 'best foreign language film', 'best performance by an actress in a supporting role in a motion picture', 'best performance by an actor in a supporting role in a motion picture', 'best director - motion picture', 'best screenplay - motion picture', 'best original score - motion picture', 'best original song - motion picture', 'best television series - drama', 'best performance by an actress in a television series - drama', 'best performance by an actor in a television series - drama', 'best television series - comedy or musical', 'best performance by an actress in a television series - comedy or musical', 'best performance by an actor in a television series - comedy or musical', 'best mini-series or motion picture made for television', 'best performance by an actress in a mini-series or motion picture made for television', 'best performance by an actor in a mini-series or motion picture made for television', 'best performance by an actress in a supporting role in a series, mini-series or motion picture made for television', 'best performance by an actor in a supporting role in a series, mini-series or motion picture made for television']
path = ''

yearMap = {}
reader = None
docs = None
# all the nominees
all_nominees = {}
all_winners = {}
all_presenters = {}


#award names mapped to list of tweet indices about that award
tweetsSortedByAward = {}

# For finding presenters, when we find a tweet we think is related to an award, pick from the official award list which
# award the tweet relates to.  This way we can later search just the related tweets for "present" or "envelope" and a
# name.

# alternatively we can associate our determined award names (rather than the official ones) with the tweets for the
# same reason.

# If a tweet has to do with an award (matches the word "best" and one other word) then finds the most similar award name
# and puts the tweet index in a list attached to that award, in the dictionary tweetsSortedByAward.
def sortTweets(year):
    global tweetsSortedByAward
    tweetsSortedByAward = {}
    for award in OFFICIAL_AWARDS:
        tweetsSortedByAward[award] = []

    strings = yearMap[year]['strings']
    isAwardPattern = re.compile(r'best|award', re.IGNORECASE)
    # remove stoplisted words from the sets we will compare to the tweets, and then make a set out of these tokenized versions
    awardSets = [set(w for w in lst if w not in stopwords.words('english') and w is not "-") for lst in jsonTokenizer(OFFICIAL_AWARDS)]

    for j in range(len(strings)):
        tweet = strings[j]
        if re.search(isAwardPattern, tweet):
            tweetTokenized = [w.lower() for w in wordpunct_tokenize(tweet)]
            max = 1
            bestIndex = []
            tweetSet = set(tweetTokenized)
            for i in range(len(awardSets)):
                currLen = len(tweetSet & awardSets[i])
                if currLen > max:
                    max = currLen
                    bestIndex = [i]
                # elif currLen == max:
                #     bestIndex.append(i)
            if bestIndex:
                for index in bestIndex:
                    tweetsSortedByAward[OFFICIAL_AWARDS[index]].append(j)
    return

def get_hosts(year):
    '''Hosts is a list of one or more strings. Do NOT change the name
    of this function or what it returns.'''
    if year not in yearMap.keys():
        prep_year(year)

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

    hosts = host_mentions.most_common(2)

    if hosts[1][1] < hosts[0][1]*3/4:
        hosts = [hosts[0][0]]
    else:
        hosts = [host[0] for host in hosts]

    return hosts

def get_awards(year):
    '''Awards is a list of strings. Do NOT change the name
    of this function or what it returns.'''
    if year not in yearMap.keys():
        prep_year(year)
    # Your code here
    awards = []
    strings = yearMap[year]['strings']
    genAwardPattern = re.compile(r'(best .*)(drama|musical|film|picture|television)', re.IGNORECASE)
    award_mentions = Counter()

    for i in range(len(strings)):
        match = re.findall(genAwardPattern, strings[i])
        # matches = [m for m in match]
        match = (w[0].lower()+w[1].lower() for w in match)
        for m in match:

            award_mentions[m] += 1

    awards_tuples = award_mentions.most_common()

    reject = re.compile(r',|\"|\'|\(')
    awards_tuples_filter = []
    for a in awards_tuples:
        if not re.search(reject, a[0]):
            awards_tuples_filter.append(a)

    awards_tuples = awards_tuples_filter

    awards_tokenized = jsonTokenizer([a[0] for a in awards_tuples])

    awards_sets = [set(a) for a in awards_tokenized]

    awards = []

    for i in range(len(awards_sets)):
        include = True
        for j in range(len(awards_sets)):
            if awards_sets[i] < awards_sets[j] and awards_tuples[j][1] > 1:
                awards_tuples[j] = (awards_tuples[j][0], awards_tuples[i][1]+awards_tuples[j][1])
                include = False
                break
        if include:
            awards.append(awards_tuples[i])

    awards.sort(reverse=True, key=lambda x: x[1])

    awards = [award[0] for award in awards]
    awards = awards[:26]

    return awards

def get_all(year):
    global all_nominees
    global all_presenters
    global all_winners
    if len(list(all_nominees))>0:
        return

    if year not in yearMap.keys():
        prep_year(year)

    sortTweets(year)

    strings = yearMap[year]['strings']
    nom_patterns = []
    pres_patterns = []
    namePattern = re.compile(r'[A-Z]\w*( [^\.:&!\?,@#\(\)]*[A-Z]\w*)?') #add to no list? :;!?()
    personPattern = re.compile(r'[A-Z]\w* [A-Z]\w*')

    # patterns for finding nominees
    nom_patterns.append(re.compile(r'nom', re.IGNORECASE))
    nom_patterns.append(re.compile(r'should.*(w[io]n|get)', re.IGNORECASE))
    nom_patterns.append(re.compile(r'will (win|get)', re.IGNORECASE))
    nom_patterns.append(re.compile(r'gonna (win|get)', re.IGNORECASE))
    nom_patterns.append(re.compile(r'deserve', re.IGNORECASE))

    # patterns for finding presenters
    pres_patterns.append(re.compile(r'present',re.IGNORECASE))
    pres_patterns.append(re.compile(r'envelope',re.IGNORECASE))
    pres_patterns.append(re.compile(r'announc',re.IGNORECASE))

    stoplist = ['rt', 'yay', 'yes', 'congrats', 'globe','globes','golden','goldenglobes','best','movie','motion','picture','film','drama','comedy','musical','cecil','demille','award', 'awards','tv','performance', 'actress','actor','television','feature','foreign','language','supporting','role','director','original','series']
    nltk_stopwords = stopwords.words('english')

    potentialWinners = {}
    potentialNominees = {}
    preses = {}

    for award in tweetsSortedByAward.keys():
        potentialWinners[award] = Counter()
        potentialNominees[award] = Counter()
        preses[award] = Counter()
        tweets = tweetsSortedByAward[award]

        for index in tweets:
            # get winner candidates and nominees
            tweet = strings[index]
            match = re.search(namePattern, tweet)
            if match:
                match = match.group(0).lower()
                potentialWinners[award][match] += 1
                for pat in nom_patterns:
                    if re.search(pat, tweet):
                        potentialNominees[award][match] += 1
            #get presenters
            for pat in pres_patterns:
                if re.search(pat, tweet):
                    matches = re.findall(personPattern, tweet)
                    matches = (w.lower() for w in matches)
                    for match in matches:
                        preses[award][match]+=1


    # stoplists and finds the 5 most frequently mentioned "nominees" and up to 2 most mentioned "presenters"
    nominees = {}
    presenters = {}
    winners = {}
    for award in OFFICIAL_AWARDS:
        winnerList = []
        sortedWinners = potentialWinners[award].most_common()
        #if award == "best performance by an actress in a television series - comedy or musical":
            #for name in curr_noms:
               # print name[0]
        for n in sortedWinners:
            add = True
            tokens = wordpunct_tokenize(n[0])
            for token in tokens:
                if token in stoplist or token in nltk_stopwords:
                    add = False
                    break
            if add:
                winnerList.append(n)

        nomineeList = []
        sortedNominees = potentialNominees[award].most_common()
        for n in sortedNominees:
            add = True
            tokens = wordpunct_tokenize(n[0])
            for token in tokens:
                if token in stoplist or token in nltk_stopwords:
                    add = False
                    break
            if add:
                nomineeList.append(n)

        # winner is the most common n-gram, biased against unigrams by one half (a unigram must have double the frequency
        # of a bigram to be picked.).  Nominees are the 4 most common bigram+, but not the winner.
        award_winner = pick_top(1, winnerList, .5)
        winners[award] = award_winner[0]

        nomineeList = pick_top(5, nomineeList, 0)
        nomineeList = [nominee for nominee in nomineeList if award_winner[0] != nominee]
        if len(nomineeList) is 5:
            nomineeList = nomineeList[:4]
        if len(nomineeList) is 0:
            nominees[award] = [""]
        else:
            nominees[award]=nomineeList

        award_preses = []
        curr_preses = preses[award].most_common()
        for p in curr_preses:
            add = True
            tokens = wordpunct_tokenize(p[0])
            for token in tokens:
                if token in stoplist or token in nltk_stopwords:
                    add = False
                    break
            if add and p[0] != winners[award]:
                award_preses.append(p[0])


        if len(award_preses) is 0:
            presenters[award] = [""]
        elif len(award_preses) is 1 or preses[award][award_preses[1]] < preses[award][award_preses[0]]*0.75:
            presenters[award] = [award_preses[0]]
        else:
            presenters[award] = award_preses[0:2]
    
    all_nominees = nominees
    all_presenters = presenters
    all_winners = winners
    return

# Takes the top *number* unigrams or n-grams, depending on ratio
def pick_top(number, sortedLst, ratio):
    unigrams = []
    bigramsplus = []
    for element in sortedLst:
        tokens = wordpunct_tokenize(element[0])
        if len(tokens) is 1:
            unigrams.append(element)
        else:
            bigramsplus.append(element)

    #will be a list of the top *number* strings
    topList = []
    unigramIndex = 0
    bigramIndex = 0
    while len(topList) < number:
        if unigramIndex is len(unigrams):
            if bigramIndex is len(bigramsplus):
                break
            else:
                topList.append(bigramsplus[bigramIndex][0])
                bigramIndex += 1
        elif bigramIndex is len(bigramsplus):
            topList.append(unigrams[unigramIndex][0])
            unigramIndex += 1
        else:
            if unigrams[unigramIndex][1] * ratio < bigramsplus[bigramIndex][1]:
                topList.append(bigramsplus[bigramIndex][0])
                bigramIndex += 1
            else:
                topList.append(unigrams[unigramIndex][0])
                unigramIndex += 1

    return topList


def get_nominees(year):
    '''Nominees is a dictionary with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change
    the name of this function or what it returns.'''
    #Your code here
    global all_nominees
    if len(list(all_nominees)) == 0:
        get_all(year)

    nominees = {}
    for award in all_nominees.keys():
        nominees[award] = all_nominees[award]

    return nominees
    

def get_winner(year):
    '''Winners is a dictionary with the hard coded award
    names as keys, and each entry containing a single string.
    Do NOT change the name of this function or what it returns.'''
    global all_winners
    if len(list(all_winners)) == 0:
        get_all(year)

    winners = {}
    for award in all_winners.keys():
        winners[award] = all_winners[award]

    return winners
    


def get_presenters(year):
    '''Presenters is a dictionary with the hard coded award
    names as keys, and each entry a list of strings. Do NOT change the
    name of this function or what it returns.'''
    # Your code here
    global all_presenters
    if len(list(all_presenters)) == 0:
        get_all(year)
    
    return all_presenters

def best_dressed(year):
    if year not in yearMap.keys():
        prep_year(year)

    strings = yearMap[year]['strings']
    dressPattern = re.compile(r'dress', re.IGNORECASE)
    namePattern = re.compile(r'[A-Z]\w* [A-Z]\w*') #, re.IGNORECASE) # ?([A-Z]\w*)?
    stoplist = ['globes','golden','best','movie','motion','picture','film','drama','comedy','musical','cecil','demille','award','tv','performance', 'actress','actor','television','feature','foreign','language','supporting','role','director','original','series']

    dress_mentions = Counter()
    for tweet in strings:
        if re.search(dressPattern, tweet):
            matches = re.findall(namePattern, tweet)
            matches = (w.lower() for w in matches)
            for match in matches:
                match_words = wordpunct_tokenize(match)
                if match_words[0] not in stoplist and match_words[1] not in stoplist:
                    dress_mentions[match] += 1

    best_dress = dress_mentions.most_common(1)

    return best_dress[0][0]

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
    stoplist = [',', '(', ')', '.', '?', '/', '+', ':', ';']
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

    return

def main():
    '''This function calls your program. Typing "python gg_api.py"
    will run this function. Or, in the interpreter, import gg_api
    and then run gg_api.main(). This is the second thing the TA will
    run when grading. Do NOT change the name of this function or
    what it returns.'''
    # Your code here
    print "Welcome to the Golden Globes API"
    
    #pre_ceremony()

    #print "Ok, I'm ready."
    year = get_year()

    while True:
        print "We will be looking at " + year + ". \n What would you like to do?"
        print "1: Get award names"
        print "2: Get nominees"
        print "3: Get winners"
        print "4: Get host(s)"
        print "5: Get presenters"
        print "6: Get best dressed"
        print "7: Change year"
        print "8: Exit"

        choices = ["1","2","3","4","5","6", "7","8"]

        func = raw_input("Enter choice number: ")
        while func not in choices:
            func = raw_input("Please enter a number 1-8: ")

        result = 0
        if func == "1":
            print "\nGetting award names"
            result = get_awards(year)
        elif func == "2":
            print "\nGetting nominees"
            result = get_nominees(year)
        elif func == "3":
            print "\nGetting winners"
            print_winners(get_winner(year))
        elif func == "4":
            print "\nGetting hosts"
            result = get_hosts(year)
        elif func == "5":
            print "\nGetting presenters"
            result = get_presenters(year)
        elif func == "6":
            print "\nGetting best dressed"
            print best_dressed(year)
        elif func == "7":
            year = get_year()
        elif func == "8":
            break

        if result != 0:
            if isinstance(result, dict):
                print_dict(result)
            elif isinstance(result, list):
                print_list(result)

        print "\n"

    return

def print_dict(d):
    for key in d.keys():

        print key + ": \n" + ', '.join(d[key])+'\n'

def print_list(l):
    for x in l:
        thisString = ''.join((c for c in x if ord(c) < 128))
        print "\t"+ thisString
    return ""

def print_winners(winnersDict):
    for key in winnersDict.keys():
        print key + ": " + winnersDict[key]

def get_year():
    while True:
        year = raw_input("What year would you like me to look into?\n")
        if os.path.exists("./gg%s.json" %year):
            prep_year(year)
            return year
        else:
            print "Please make sure gg%s.json exists and is inside this folder" %year

    return year

def prep_year(year):
    global yearMap
    yearMap[year] = {}
    yearMap[year]['strings'] = jsonStrings('gg'+year+'.json')
    

if __name__ == '__main__':
    main()
