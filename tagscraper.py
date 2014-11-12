#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os import path
import re
import json

import requests
import tweepy

from tokens import key, secret

auth = tweepy.AppAuthHandler(key, secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

Cursor = tweepy.Cursor

tweepy.parsers.ModelParser


def page_download(url, outpath):
    """Copies the file at url to outpath"""
    page = requests.get(url)
    # check if url is text
    if not page.headers['content-type'].startswith("text"):
        raise Exception("Page not text")

    # check that page returned properly
    if not page.status_code == 200:
        raise Exception("Invalid status code")

    text = page.text.encode('utf8', 'ignore')
    outfile = open(outpath, 'w')
    outfile.write(text)
    return True


def yield_tweets(query):
    """Searchs for tweets with query and returns info about first n"""
    for tweet in Cursor(api.search, q=query).items():
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
        yield info


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
    n = 0
    for tweet in tweet_list:
        print "{} urls scraped".format(n)
        for i, url in enumerate(tweet['full_urls']):
            outpath = path.join(
                outdir, str(tweet['id']) + "_" + str(i) + ".html"
            )
            print "Scraping {} to {}".format(url, outpath)
            
            try:
                page_download(url, outpath)
                n += 1
            except Exception as e:
                print "error scraping"
                print str(e)


def scraper(outdir, query, n=100):

    if not path.exists(outdir):
        #check if path exists and make otherwise
        os.makedirs(outdir)

    tweets = yield_tweets(query)
    tweet_list = []
    urls = set()

    count = 0

    for tweet in tweets:

        if len(tweet['full_urls']) > 0:
            n_urls = 0
            scraped = False
            for u in tweet['full_urls']:
                if re.findall(r"youtu\.be|youture\.com|soundcloud.com", u):
                    #check if page is likely to have non text media
                    continue

                if not u in urls:
                    outpath = path.join(outdir, str(tweet['id'])+str(n_urls)+".html")
                    try:
                        page_download(u, outpath)
                        count += 1
                        n_urls += 1
                        scraped = True
                        urls.add(u)
                        print "{} scraped".format(u)
                        print "{} urls scraped".format(count)
                    except Exception as e:
                        print "error scraping"
                        print str(e)

            if scraped:
                tweet_list.append(tweet)

        if count >= n:
            break

    # create manifest file of tweets
    manifest = open(path.join(outdir, "manifest.json"), 'w')
    manifest.write(json.dumps(tweet_list))
    manifest.close()
    print "Tweet manifest written"


def scrape_hashtag(hashtag, outdir, n=100, since=None, until=None):
    """Scrapes n links from hashtag on twitter and places files in outdir"""
    query = "#{} filter:links lang:en".format(hashtag)
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
