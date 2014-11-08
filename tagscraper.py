#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import json

import requests
import tweepy

from tokens import key, secret

auth = tweepy.AppAuthHandler(key, secret)
api = tweepy.API(auth)


def link_scraper(query, outdir="pages"):
    outdir = path.join(path.curdir, outdir)
    results = api.search(query)
    n = 0

    for r in results:
        urls = [u['expanded_url'] for u in r.entities['urls']]
        for u in urls:
            print u
            page = requests.get(u)
            outpath = path.join(outdir, str(n) + '.html')
            n += 1
            outfile = open(outpath, 'w')

            # handle unrecognized characters
            text = page.text.encode('utf8', 'ignore')

            outdict = {'url': u, 'text': text, 'tweet', r.text}

            outfile.write(json.dumps(outdict))
            outfile.close()


def main():
    query = "#Election2014 filter:links"
    link_scraper(query)

if __name__ == '__main__':
    main()
