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


@module.url('https?://twitter.com/([^/]*)(?:/status/(\d+)).*')
def get_url(bot, trigger, match):
    consumer_key = bot.config.twitter.consumer_key
    consumer_secret = bot.config.twitter.consumer_secret

    consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
    client = oauth.Client(consumer)
    id_ = match.group(2)
    response, content = client.request(
        'https://api.twitter.com/1.1/statuses/show/{}.json'.format(id_))
    if response['status'] != '200':
        logger.error('%s error reaching the twitter API for %s',
                     response['status'], match.group(0))

    content = json.loads(content.decode('utf-8'))
    message = ('[Twitter] {content[text]} | {content[user][name]} '
               '(@{content[user][screen_name]}) | {content[retweet_count]} RTs '
               '| {content[favorite_count]} ♥s').format(content=content)
    all_urls = content['entities']['urls']
    if content['is_quote_status']:
        message += ('| Quoting {content[quoted_status][user][name]} '
                    '(@{content[quoted_status][user][screen_name]}): '
                    '{content[quoted_status][text]}').format(content=content)
        quote_id = content['quoted_status']['id_str']
        for url in content['entities']['urls']:
            expanded_url = url['expanded_url']
            if expanded_url.rsplit('/', 1)[1] == quote_id:
                message = message.replace(url['url'], '')
                break
        all_urls = all_urls + content['quoted_status']['entities']['urls']
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
@module.url('(?=.*https?://twitter.com/(?:#!/)?[A-Za-z0-9_]{1,15}(?!/status))https?://twitter.com/(?:#!/)?([A-Za-z0-9_]{1,15}).*')
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

    url = None
    if hasattr(user, 'url') and user.url is not None:
        url = user.url
        for url in user.entities['url']['urls']:
            url = desc.replace(url['url'], url['display_url'])

    message = ('[Twitter] @{user.screen_name}: {user.name} | '
           '| Description: {desc} '
           '| Location: {user.location} '
           '| Tweets: {user.statuses_count} '
           '| Following: {user.friends_count} '
           '| Followers: {user.followers_count}').format(user=user, desc=desc)
    if url is not None:
        message += (' | URL: ' + url)

    bot.say(message)

