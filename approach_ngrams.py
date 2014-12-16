
# coding: utf-8

# In[ ]:

from os import path
import cPickle as pickle

import nltk, string
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.collocations import *
import codecs, os, json, glob
from bs4 import BeautifulSoup
from nltk.corpus import wordnet as wn
from pandas import DataFrame
import pandas as pd

import chunking_util
import grouping_util


# In[ ]:

def RegTokenizeWords(wordlist):
    pattern = r"([A-Z]\.)+|\w+([-']\w+)*|\$?\d+(\.\d+)?%?|\.\.\.|[][.,;\"'?():-_`]"
    return [word for word in nltk.regexp_tokenize(wordlist,pattern)]


# In[ ]:

def CreateNgramsOnTitle(articles_df):
    title_words = []
    for art in articles_df['tokenized_title2']:
        title_words.extend([word.replace(u"\u2018", "").replace(u"\u2019", "").replace(u"\u201c",'').replace(u"\u201d", '') for word in  art])

    title_words_noStop_noPunct = [word for word in title_words if word.lower() not in stopwords.words('english') and word not in string.punctuation] 

    freqD3 = nltk.FreqDist(nltk.bigrams(title_words_noStop_noPunct))
    top_bigrams = freqD3.keys()[:50]

    freqD4 = nltk.FreqDist(nltk.trigrams(title_words_noStop_noPunct))
    top_trigrams = freqD4.keys()[:50]

    freqD5 = nltk.FreqDist(nltk.ngrams(title_words_noStop_noPunct,4))
    top_ngrams = freqD5.keys()[:50]
    
    title_df = DataFrame({"top_bigrams":top_bigrams, "top_trigrams":top_trigrams, "top_ngrams":top_ngrams})
    
    return title_df

def getTrisAndNgramsForBiGrams(top_bigrams,top_trigrams,top_ngrams):
    finallist ={}
    for b1,b2 in top_bigrams[:15]:
        finallist[(b1,b2)] = []
        for t1,t2,t3 in top_trigrams[:30]:
            added=False
            
            if b1.lower() in [t1.lower(),t2.lower(),t3.lower()] and b2.lower() in [t1.lower(),t2.lower(),t3.lower()]:
                
                for ngram in top_ngrams[:30]:
                    ngramstring = " ".join(ngram)
                    if t1.lower() in ngramstring.lower() and t2.lower() in ngramstring.lower() and t3.lower() in ngramstring.lower():
                        finallist[(b1,b2)].append(ngram)
                        added = True
                if added == False:        
                    finallist[(b1,b2)].append((t1,t2,t3))
    return finallist


# In[ ]:

def GetSentencesBasedOnTerms(articles_df,keywords):
    
    finalsents ={}
    #list of keywords
    for key in keywords.keys():
        finalsents[key] =[]
        #article
        for art in articles_df["sent_tokenized"]:
            #sentences
            for sent in art:
                #handling len == 0
                if len(keywords[key])== 0:
                    if key[0].lower() in sent.lower() and key[1].lower() in sent.lower():
                        finalsents[key].append(RegTokenizeWords(sent))
                else:
                    #terms for each keyword
                    for term in keywords[key]:
                        if len(term) == 3:
                            if term[0].lower() in sent.lower() and term[1].lower() in sent.lower() and term[2].lower() in sent.lower():
                                finalsents[key].append(RegTokenizeWords(sent))
                                break
                        if len(term) == 4:
                            if term[0].lower() in sent.lower() and term[1].lower() in sent.lower() and term[2].lower() in sent.lower() and term[3].lower() in sent.lower():
                                finalsents[key].append(RegTokenizeWords(sent))
                                break
            #Trying to handle cases where the tri/n grams cannot be found in sentences
            if len(finalsents[key]) == 0:
                for art in articles_df["sent_tokenized"]:
                    for sent in art:
                        if key[0].lower() in sent.lower() and key[1].lower() in sent.lower():
                            finalsents[key].append(RegTokenizeWords(sent))
    return finalsents


# In[ ]:

# finalsents = GetSentencesBasedOnTerms(articles_df)
    
def GetFinalListOfChunks(finalsents):
    fc =[]
    chunksByBigram =  GetChunksForEachTopic(finalsents,parseImportantNps)
    for key in chunksByBigram.keys():
        fd = nltk.FreqDist(chunksByBigram[key])
        fc.extend([key for key,val in fd.items()[:10]])
    _2n3, _3n4 = getPhraseLengths(fc)
    return mergeTerms2Lists(_2n3.keys(),_3n4.keys()).keys()


# In[ ]:

#break chunks into groups by length
def getPhraseLengths(chunkfd):
    lenMore = []
    len3 = []
    len2 = []
    len1 = []
    combined = {}
    
    for c in chunkfd:
        if len(c.split()) > 3:
            lenMore.append(c)
        if len(c.split()) == 3:
            len3.append(c)
        if len(c.split()) == 2:
            len2.append(c)
        if len(c.split()) == 1:
            len1.append(c)
            
    len1 = mergeTerms(len1)
    len2 = mergeTerms(len2)
    len3 = mergeTerms(len3)
    lenMore = mergeTerms(lenMore)
    
    return mergeTerms2Lists(len2, len3), mergeTerms2Lists(len3, lenMore)
 
    
#merge ngrams into same length other ngrams
def mergeTerms(list1):
    
    results = []
    list2 = set(list1)
    
    for i in list2: 
        flag = True
        for j in list2:
            if i.lower() in j.lower() and i != j:
                results.append(j)
                flag = False
                
        if flag == True and i not in results: 
            results.append(i)
    
    return set(results)


#merge shorter length terms into longer length terms
def mergeTerms2Lists(shortlenlist, longerlenlist):
    termMapping = {}
    
    for j in longerlenlist:
        termMapping[j] = []
    for i in shortlenlist: 
        flag = True
        for j in longerlenlist:
            if i.lower() in j.lower():
                termMapping[j].append(i)
                flag = False
        if flag == True:
            termMapping[i] = []
    
    return termMapping


# In[ ]:

#Noun phrase chunker
#Gets you the noun phrases
def SlightlyModifiedChuangChunker(sent):
    grammar = "NP: {<CD>*(((<JJ>|<N.*>)+(<N.*>|<CD>))|<N.*>)}"
    cp = nltk.RegexpParser(grammar)
    result = cp.parse(sent)
    return result

def parseImportantNps(sent):
    grammar = r"""
    N-N: {<DET|CD.*>?<J*|N.*>+<N.*>} # chunk DET/Cardinal w/optional ADJ or N with proper noun
           {<NNP.*>+<NNP.*>}             # chunk solo proper nouns only
    """
    cp = nltk.RegexpParser(grammar)
    return cp.parse(sent)

#Run the chunker against a Chunker with a specific grammar
def ChunkASection(sents,Chunker):
    chunkedlist = []
    for sent in sents:
        chunks =  Chunker(sent)
        for chunk in chunks:
            if(type(chunk)==type(chunks)):
                temp =''
                for leaf in chunk.leaves():
                    temp += leaf[0]+' '
                chunkedlist.append(temp.strip())
    return chunkedlist

def GetChunksForEachTopic(diction, chunker):
    finalChunksByKey = {}
    for key in diction.keys():
        finalChunksByKey[key] = []
        tagged_sents = []
        for sent in diction[key]:
            tagged_sents.append(nltk.pos_tag(sent))
        finalChunksByKey[key].extend(ChunkASection(tagged_sents,chunker))
    return finalChunksByKey


# In[ ]:

def ngram_approach(data_path, min_matches=3):
    p = open(data_path, 'r')
    df=pickle.load(p)
    df['tokenized_title2'] = df['title'].map(RegTokenizeWords)
    df_title = CreateNgramsOnTitle(df)
    keyterms = getTrisAndNgramsForBiGrams(df_title["top_bigrams"],df_title["top_trigrams"],df_title["top_ngrams"])
    sentences = GetSentencesBasedOnTerms(df,keyterms)
    keyphrases = GetFinalListOfChunks(sentences)
    keyphrase_map = {k.lower():k.lower() for k in keyphrases}
    df_overlap=grouping_util.get_overlaps(keyphrase_map, df)
    df['common_chunks']=grouping_util.get_keyphrase_columns(keyphrase_map, df, make_keyphrase_cols=False)
    groups=grouping_util.get_groups(df_overlap, doc_percents=False,set_filters=df.common_chunks, min_matches=min_matches)
    
    out={
            'group_df':grouping_util.get_grouped_df(df_overlap,groups),
            'keyphrases':keyphrase_map
        }
    
    group_data=[]
    for g in groups:
        g_dict={}
        g_set=set(g)
        g_dict['keyphrases']=g_set
        url_list = []
        for url in df[df.common_chunks.apply(lambda r: r>=g_set)].url:
            url_list.append(url)
        
        g_dict['urls']=url_list
        
        group_data.append(g_dict)
    
    out['groups']=group_data
    
    return out

