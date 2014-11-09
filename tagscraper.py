#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os import path
import json

import requests
import tweepy

from tokens import key, secret

auth = tweepy.AppAuthHandler(key, secret)
api = tweepy.API(auth)

Cursor = tweepy.Cursor


def page_download(url, outpath):
    """Copies the file at url to outpath"""
    outfile = open(outpath, 'w')
    page = requests.get(url)
    text = page.text.encode('utf8', 'ignore')
    outfile.write(text)

    return True


def get_tweets(query, n=100):
    """Searchs for tweets with query and returns info about first n"""
    out = []
    for tweet in Cursor(api.search, q=query).items(n):
        # get details for each tweet
        info = {
            "text": tweet.text,
            "full_urls": [u['expanded_url'] for u in tweet.entities['urls']],
            "short_urls": [u['url'] for u in tweet.entities['urls']],
            "retweet_count": tweet.retweet_count,
            "created_at": tweet.created_at.isoformat(),
            "possibly_sensitive": tweet.possibly_sensitive,
            "id": tweet.id
        }

        out.append(info)

    return out


def tweet_scraper(tweet_list, outdir):
    """Scrapes urls from a list of tweets"""
    for tweet in tweet_list:
        for i, url in enumerate(tweet['full_urls']):
            outpath = path.join(
                outdir, str(tweet['id']) + "_" + str(i) + ".html"
            )
            print "Scraping {} to {}".format(url, outpath)
            
            try:
                page_download(url, outpath)
            except Exception as e:
                print "error scraping"
                print str(e)


def scraper(outdir, query, n=100):

    if not path.exists(outdir):
        #check if path exists and make otherwise
        os.makedirs(outdir)

    tweets = get_tweets(query, n)

    # create manifest file of tweets
    manifest = open(path.join(outdir, "manifest.json"), 'w')
    manifest.write(json.dumps(tweets))
    manifest.close()

    #scrape tweets
    tweet_scraper(tweets, outdir)


def scrape_hashtag(hashtag, outdir, n=100, since=None, until=None):
    """Scrapes n links from hashtag on twitter and places files in outdir"""
    query = "#{} filter:links".format(hashtag)
    if since:
        query += " since:{}".format(since)
    if until:
        query += " until:{}".format(until)

    print 'Scraping tweets from query "{}"'.format(query)
    scraper(outdir, query, n)


def main():
    outdir = path.join(path.curdir, "data", "Election2014")
    scrape_hashtag("Election2014", outdir, since="2014-11-3", until="2014-11-7")

if __name__ == '__main__':
    main()
