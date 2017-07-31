# coding=utf-8
from __future__ import unicode_literals, absolute_import, division, print_function

import json

import oauth2 as oauth

from sopel import module
from sopel.config.types import StaticSection, ValidatedAttribute, NO_DEFAULT
from sopel.logger import get_logger

import tweepy

logger = get_logger(__name__)


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


@module.url('https?://twitter.com/(?:[^/]*)(?:/status(?:es)?/(\d+)).*')
def get_url(bot, trigger, match):
    auth = tweepy.OAuthHandler(bot.config.twitter.consumer_key,
                               bot.config.twitter.consumer_secret)
    auth.set_access_token(bot.config.twitter.access_token,
                          bot.config.twitter.access_token_secret)
    api = tweepy.API(auth_handler=auth, wait_on_rate_limit=True)

    id_ = match.group(1)
    tweet = api.get_status(id_)

    message = ('[Twitter] {tweet.text} | {tweet.user.name} '
               '(@{tweet.user.screen_name}) | {tweet.retweet_count} RTs '
               '| {tweet.favorite_count} ♥s').format(tweet=tweet)
    all_urls = tweet.entities['urls']
    if tweet.is_quote_status:
        # add the quoted tweet
        message += (' | Quoting {tweet.quoted_status["user"]["name"]} '
                    '(@{tweet.quoted_status["user"]["screen_name"]}): '
                    '{tweet.quoted_status["text"]}').format(tweet=tweet)
        quote_id = tweet.quoted_status['id_str']
        # remove the link to the quoted tweet
        for url in tweet.entities.urls:
            expanded_url = url['expanded_url']
            if expanded_url.rsplit('/', 1)[1] == quote_id:
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
@module.url(r'https?://twitter.com/(?:#!/)?([A-Za-z0-9_]{1,15})(?!/status)\b')
def get_url(bot, trigger, match):
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
    if url is not None:
        message += (' | URL: ' + profile_url)

    bot.say(message)

