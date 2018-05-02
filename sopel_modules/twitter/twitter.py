# coding=utf-8
from __future__ import unicode_literals, absolute_import, division, print_function
from sopel import module
from sopel.config.types import StaticSection, ValidatedAttribute, NO_DEFAULT
from sopel.logger import get_logger
import json
import oauth2 as oauth
import tweepy, re


logger = get_logger(__name__)
url_tweet_id = re.compile(r'.*status(?:es)?/(\d+)$')

class TwitterSection(StaticSection):
    consumer_key = ValidatedAttribute('consumer_key', default=NO_DEFAULT)
    consumer_secret = ValidatedAttribute('consumer_secret', default=NO_DEFAULT)
    access_token = ValidatedAttribute('access_token', default=NO_DEFAULT)
    access_token_secret = ValidatedAttribute('access_token_secret', default=NO_DEFAULT)

def configure(config):
    config.define_section('twitter', TwitterSection, validate=False)
    config.twitter.configure_setting(
        'consumer_key', 'Enter your Twitter consumer key')
    config.twitter.configure_setting(
        'consumer_secret', 'Enter your Twitter consumer secret')
    config.twitter.configure_setting(
        'access_token', 'Enter your Twitter access token')
    config.twitter.configure_setting(
        'access_token_secret', 'Enter your Twitter access token secret')


def setup(bot):
    bot.config.define_section('twitter', TwitterSection)

# there are lots of exotic status url's. look for anything starting with
# twitter.com and then ending with /status(es)/number
#
# Possibilities twitter.com/i/...:
# streams live moments videos web stickers directory status cards discover
@module.url(r'https?:\/\/(?:mobile\.)?twitter\.com\/[#!A-Za-z0-9_\/]*\/(status(?:es)?|tweet)?\/(\d+)\b')
def get_tweet(bot, trigger, match):
    auth = tweepy.OAuthHandler(bot.config.twitter.consumer_key,
                               bot.config.twitter.consumer_secret)
    auth.set_access_token(bot.config.twitter.access_token,
                          bot.config.twitter.access_token_secret)
    api = tweepy.API(auth_handler=auth, wait_on_rate_limit=True)

    tweet_id = match.group(2)
    tweet = api.get_status(tweet_id, tweet_mode='extended')
    tweet.full_text = tweet.full_text.replace('\n', ' ')

    message = ('[Twitter] {tweet.full_text} | {tweet.user.name} '
            '(@{tweet.user.screen_name}) | {tweet.retweet_count:,} RTs '
               '| {tweet.favorite_count:,} ♥s').format(tweet=tweet)
    all_urls = tweet.entities['urls']
    if tweet.is_quote_status:
        # add the quoted tweet
        message += (' | Quoting {tweet.quoted_status[user][name]} '
                    '(@{tweet.quoted_status[user][screen_name]}): '
                    '{tweet.quoted_status[full_text]}').format(tweet=tweet)
        quote_id = tweet.quoted_status_id_str
        # remove the link to the quoted tweet
        for url in tweet.entities['urls']:
            expanded_url = url['expanded_url']
            match = url_tweet_id.match(expanded_url)
            if match is not None:
                if match.group(1) == quote_id or match.group(1) == tweet.id_str:
                    message = message.replace(url['url'], '')
                    break
        all_urls = all_urls + tweet.quoted_status['entities']['urls']
    all_urls = ((u['url'], u['expanded_url']) for u in all_urls)
    all_urls = sorted(all_urls, key=lambda pair: len(pair[1]))

    for url in all_urls:
        replaced = message.replace(url[0], url[1])
        if len(replaced) < 400:  # 400 is a guess to keep the privmsg < 510
            message = replaced
        else:
            break

    bot.say(message)

# avoid status urls
@module.url(r'https?:\/\/(?:mobile\.)?twitter\.com\/(?!#!\/|i)([A-Za-z0-9_]{1,15})(?!\/status)\b')
def get_profile(bot, trigger, match):
    auth = tweepy.OAuthHandler(bot.config.twitter.consumer_key,
                               bot.config.twitter.consumer_secret)
    auth.set_access_token(bot.config.twitter.access_token,
                          bot.config.twitter.access_token_secret)
    api = tweepy.API(auth_handler=auth, wait_on_rate_limit=True)

    sn = match.group(1)
    user = api.get_user(screen_name=sn)

    desc = user.description
    for url in user.entities['description']['urls']:
        desc = desc.replace(url['url'], url['display_url'])

    profile_url = None
    if hasattr(user, 'url') and user.url is not None:
        profile_url = user.url
        for url in user.entities['url']['urls']:
            profile_url = profile_url.replace(url['url'], url['display_url'])

    message = ('[Twitter] @{user.screen_name}: {user.name}'
           ' | Description: {desc}'
           ' | Location: {user.location}'
           ' | Tweets: {user.statuses_count}'
           ' | Following: {user.friends_count}'
           ' | Followers: {user.followers_count}').format(user=user, desc=desc)
    if profile_url is not None:
        message += (' | URL: ' + profile_url)

    bot.say(message)
