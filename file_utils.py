
# coding: utf-8

# In[1]:

import nltk, string
from nltk.corpus import stopwords, brown
from nltk.tokenize import RegexpTokenizer
from nltk.collocations import *
import codecs, os, json, glob
from bs4 import BeautifulSoup
from nltk.corpus import wordnet as wn
from pandas import DataFrame
import pandas as pd
from os import path


# In[2]:

def languageCheck(text):
    fd = nltk.FreqDist(nltk.word_tokenize(text))
    topwords = [key.lower() for key in fd.keys()[:15]]
    
    if "the" not in topwords:
#         print "BAD TOPWORDS: ", topwords
        return False
    else:
#         print "GOOD TOPWORDS: ", topwords
        return True


# In[5]:

def parseImportantNps():
    grammar = r"""
    N-N: {<DET|CD.*>?<J*|N.*>+<N.*>} # chunk DET/Cardinal w/optional ADJ or N with proper noun
           {<NNP.*>+<NNP.*>}             # chunk solo proper nouns only
    """
    cp = nltk.RegexpParser(grammar)
    return cp, 'N-N'


def chunk(tagged, func=parseImportantNps):
    "Chunks tagged sents using parser returned by func"
    chunks = []
    leaves = []
    cp, cn = func()
    for i in tagged:
        tree = cp.parse(i)
        for subtree in tree.subtrees():
            if subtree.node == cn:
                leaflist = [leaf[0] for leaf in subtree.leaves()]
                chunks.append(subtree.leaves())
                leaves.append(' '.join(leaflist))
    return leaves


# In[3]:

def read_files_to_list(fdir, expression='*[0-9].json'):
    """
    Returns list of files in path matching expression
    """
    filelist = []
    for file in glob.glob(path.join(fdir, expression)):
        filelist.append(file)
    return filelist


def clean_unicode(string):
    "Cleans some unicode from string"
    return string.        replace(u"\u2018", "'").        replace(u"\u2019", "'").        replace(u"\u201c", '"').        replace(u"\u201d", '"')

        
def dict_from_path(fdir, expression="*.json"):
    """Reads files in path matching expression and returns list of dicts containing
        title, url, and text"""
    file_list = read_files_to_list(fdir, expression)
    out=[]
    
    for filepath in file_list:
        #print filepath
        
        with open(filepath, 'r') as f:
            j = json.load(f)
            if 'objects' in j.keys() and 'title' in j['objects'][0]:
                #read article and fix unicode
                data=j['objects'][0]
                url=j['request']["pageUrl"]
            else:
                # skip if no objects or title
                continue
            
            article = clean_unicode(data['text'])
            if not languageCheck(article):
                continue
            
            row={
                "title":clean_unicode(data['title']),
                "url":url,
                "article":article
                }
            out.append(row)
                

    return out


# In[4]:

#look for important noun phrase patterns, either nouns preceded by Det+Adj or simply compound nouns
def parseImportantNps():
    grammar = r"""
    N-N: {<DET|CD.*>?<J*|N.*>+<N.*>} # chunk DET/Cardinal w/optional ADJ or N with proper noun
           {<NNP.*>+<NNP.*>}             # chunk solo proper nouns only
    """
    cp = nltk.RegexpParser(grammar)
    return cp, 'N-N'


#function to chunk 
def chunk(tagged, func=parseImportantNps):
    chunks = []
    leaves = []
    cp, cn = func()
    for i in tagged:
        tree = cp.parse(i)
        for subtree in tree.subtrees():
            if subtree.node == cn:
                leaflist = [leaf[0] for leaf in subtree.leaves()]
                chunks.append(subtree.leaves())
                leaves.append(' '.join(leaflist))
    return leaves

def listToTokens(sentenceList):
    tokenized_sents = [nltk.word_tokenize(sent.strip('(').strip(')')) for sent in sentenceList]
    return tokenized_sents

def tagTokens(tokenList):
    tagged_sents = [nltk.pos_tag(sent) for sent in tokenList]
    return tagged_sents


# In[44]:

def df_from_path(fdir, expression='*[0-9].json', V=False):
    """Reads files in path matching expression and returns data frame containing
        title, url, and text"""
    
    if V:
        print "getting data"
        
    data = dict_from_path(fdir, expression)
    
    if V:
        print "creating dataframe"
        
    df=pd.DataFrame.from_dict(data)
    df.drop_duplicates(subset='title', inplace=True)
    df.drop_duplicates(subset='article', inplace=True)
    
    if V:
        print "tokenizing"
    
    df['tokenized_article'] = df['article'].map(nltk.word_tokenize)
    df['tokenized_title'] = df['title'].map(nltk.word_tokenize)
    df['sent_tokenized'] = df['article'].map(nltk.sent_tokenize)
    
    if V:
        print "tagging"
    
    df['pos_tagged_word_tokenized']=df['sent_tokenized'].map(listToTokens).map(tagTokens)
    
    if V:
        print "chunking"
    
    df['article_chunks'] = df.pos_tagged_word_tokenized.apply(chunk)
    
    return df

