
# coding: utf-8

# In[ ]:

import nltk, string
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.collocations import *
import codecs, os, json, glob
from bs4 import BeautifulSoup
from nltk.corpus import wordnet as wn
from pandas import DataFrame
import pandas as pd
import get_sents

import file_utils
from os import path


# In[ ]:

def getPhraseLengths(chunkfd):
    "break chunks into groups by length"
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
    return len1, len2, len3, lenMore

def mergeTerms(list1):
    "merge ngrams into same length other ngrams"
    results = []
    list2 = set([i.lower() for i in list1])
    
    for i in list2: 
        flag = True
        for j in list2:
            if i in j and i != j:
                results.append(j)
                flag = False
                
        if flag == True and i not in results: 
            results.append(i)
    
    return set(results)


def mergeTerms2Lists(shortlenlist, longerlenlist):
    "merge shorter length terms into longer length terms"
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

def get_best_chunks(df):
    corpus_chunks = []
    for chunk in df['article_chunks']:
        corpus_chunks.extend(chunk)

    chunk_fd = nltk.FreqDist(corpus_chunks)
    freqchunks = chunk_fd.keys()[:100]

    #produce chunk groups by length
    len1, len2, len3, lenMore = getPhraseLengths(freqchunks)

    #condense all terms of same length into new lists
    new_len2 = mergeTerms(len2)
    new_len3 = mergeTerms(len3)
    new_lenMore = mergeTerms(lenMore)

    #resulting list 
    merged2_3 = mergeTerms2Lists(new_len2, new_len3)

    #resulting list if we decide to merge into larger chunks
    improved_freqchunks = mergeTerms2Lists(merged2_3.keys(), new_lenMore)
    return improved_freqchunks


# In[ ]:

def chunk_mapper(df, n_chunks=100):
    corpus_chunks = []
    for chunk in df['article_chunks']:
        corpus_chunks.extend(chunk)
    
    chunk_fd = nltk.FreqDist(corpus_chunks)
    freqchunks = chunk_fd.keys()[:n_chunks]
    
    chunk_map={}
    
    for c in freqchunks:
        for k,v in chunk_map.items():
            if c.lower() in k.lower() or k.lower() in c.lower():
                chunk_map[c]=v
                break
        
        if c not in chunk_map:
                chunk_map[c]=c
    
    return chunk_map


# In[ ]:

def apply_map(row, chunk_map):
    return set(chunk_map[c] for c in row if c in chunk_map.keys())


# In[ ]:

def create_best_chunk_df(df, chunk_col='article_chunks'):
    "extracts the best chunks from dataframe df using column chunk_col"
    
    chunks = set(get_best_chunks(df))
    return df[chunk_col].map(lambda r: chunks & set(r))


# In[ ]:

def df_chunks_from_path(fdir, expression='*[0-9].json', V=False):
    "reads files from path matching expression and returns df with chunk columns"
    

        
    df = file_utils.df_from_path(fdir, expression, V)
    
    if V:
        print "Getting best chunks"
        
    df['common_chunks']=create_best_chunk_df(df)
    
    return df

