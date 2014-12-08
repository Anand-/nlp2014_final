#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from os import path

import nltk
import glob


def read_files_to_list(fdir, expression='*.json'):
    """
    Returns list of files in path matching expression
    """
    filelist = []
    for file in glob.glob(path.join(fdir, expression)):
        filelist.append(file)
    return filelist


sent_tokenizer = nltk.tokenize.PunktSentenceTokenizer()


def sents_from_path(fdir, expression="*.json"):
    """Reads files in path matching expression and returns set of sentences"""
    file_list = read_files_to_list(fdir, expression)

    sents = set()
    for filepath in file_list:
        with open(filepath, 'r') as f:
            j = json.load(f)
            if 'objects' in j.keys() and 'title' in j['objects'][0]:
                #read article and fix unicode
                article = j['objects'][0]['text'].\
                    replace(u"\u2018", "'").\
                    replace(u"\u2019", "'").\
                    replace(u"\u201c", '"').\
                    replace(u"\u201d", '"')
                sents.update(sent_tokenizer.tokenize(article))

    return sents
