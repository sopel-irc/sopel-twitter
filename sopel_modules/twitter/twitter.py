# coding=utf-8
from __future__ import unicode_literals, absolute_import, division, print_function

from datetime import datetime
import json
import re

import oauth2 as oauth

from sopel import module
from sopel.config.types import StaticSection, ValidatedAttribute, NO_DEFAULT
from sopel.logger import get_logger
from sopel.tools import time

logger = get_logger(__name__)


class TwitterSection(StaticSection):
    consumer_key = ValidatedAttribute('consumer_key', default=NO_DEFAULT)
    consumer_secret = ValidatedAttribute('consumer_secret', default=NO_DEFAULT)
    show_quoted_tweets = ValidatedAttribute('show_quoted_tweets', bool, default=True)


def configure(config):
    config.define_section('twitter', TwitterSection, validate=False)
    config.twitter.configure_setting(
        'consumer_key', 'Enter your Twitter consumer key')
    config.twitter.configure_setting(
        'consumer_secret', 'Enter your Twitter consumer secret')
    config.twitter.configure_setting(
        'show_quoted_tweets', 'When a tweet quotes another status, '
        'show the quoted tweet on a second IRC line?')


def setup(bot):
    bot.config.define_section('twitter', TwitterSection)


def get_client(bot):
    """Utility to get an OAuth client. Reduces boilerplate."""
    return oauth.Client(
        oauth.Consumer(
            key=bot.config.twitter.consumer_key,
            secret=bot.config.twitter.consumer_secret))


def get_extended_media(tweet):
    """
    Twitter annoyingly only returns extended_entities if certain entities exist.
    """
    # Get either the extended entities or an empty dict
    maybe_entities = tweet.get('extended_entities', {})
    # Safely return either the media key or an empty list
    return maybe_entities.get('media', [])


def format_tweet(tweet):
    """
    Format a tweet object for display.

    :param tweet: the tweet object, as decoded JSON
    :return: the formatted tweet, and formatted quoted tweet if it exists
    :rtype: tuple
    """
    try:
        text = tweet['full_text']
    except KeyError:
        text = tweet['text']
    text = text.replace("\n", " \u23CE ")  # Unicode symbol to indicate line-break
    urls = tweet['entities']['urls']
    media = get_extended_media(tweet)

    # Remove link to quoted status itself, if it's present
    if tweet['is_quote_status']:
        for url in urls:
            if url['expanded_url'].rsplit('/', 1)[1] == tweet['quoted_status_id_str']:
                text = re.sub('\\s*{url}\\s*'.format(url=re.escape(url['url'])), '', text)
                break  # there should only be one

    # Expand media links so clients with image previews can show them
    for item in media:
        replaced = text.replace(item['url'], item['media_url_https'])
        if replaced == text:
            # Twitter only puts the first media item's URL in the tweet body
            # We have to append the others ourselves
            text += item['media_url_https']
        else:
            text = replaced

    # Expand other links to full URLs
    for url in urls:
        text = text.replace(url['url'], url['expanded_url'])

    # Done! At least, until Twitter adds more entity types...
    u = tweet['user']
    return u['name'] + ' (@' + u['screen_name'] + '): ' + text


@module.url(r'https?://twitter.com/([^/]*)(?:/status/(\d+))?.*')
def get_url(bot, trigger, match):
    sn = match.group(1)
    id_ = match.group(2)

    if id_:
        output_status(bot, id_)
    else:
        output_user(bot, trigger, sn)


def output_status(bot, id_):
    client = get_client(bot)
    response, content = client.request(
        'https://api.twitter.com/1.1/statuses/show/{}.json?tweet_mode=extended'.format(id_))
    if response['status'] != '200':
        logger.error('%s error reaching the twitter API for status ID %s',
                     response['status'], id_)

    tweet = json.loads(content.decode('utf-8'))
    if tweet.get('errors', []):
        msg = "Twitter returned an error"
        try:
            error = tweet['errors'][0]
        except IndexError:
            error = {}
        try:
            msg = msg + ': ' + error['message']
            if msg[-1] != '.':
                msg = msg + '.'  # some texts end with a period, but not all -___-
        except KeyError:
            msg = msg + '. :( Maybe the tweet was deleted?'
        bot.say(msg)
        logger.debug('Tweet ID {id} returned error code {code}: "{message}"'
            .format(id=id_, code=error.get('code', '-1'),
                message=error.get('message', '(unknown description)')))
        return

    template = "[Twitter] {tweet} | {RTs} RTs | {hearts} ♥s"

    bot.say(template.format(tweet=format_tweet(tweet),
                            RTs=tweet['retweet_count'],
                            hearts=tweet['favorite_count']))

    if tweet['is_quote_status'] and bot.config.twitter.show_quoted_tweets:
        tweet = tweet['quoted_status']
        bot.say(template.format(tweet='Quoting: ' + format_tweet(tweet),
                                RTs=tweet['retweet_count'],
                                hearts=tweet['favorite_count']))


def output_user(bot, trigger, sn):
    client = get_client(bot)
    response, content = client.request(
        'https://api.twitter.com/1.1/users/show.json?screen_name={}'.format(sn))
    if response['status'] != '200':
        logger.error('%s error reaching the twitter API for screen name %s',
                     response['status'], sn)

    user = json.loads(content.decode('utf-8'))
    if user.get('errors', []):
        msg = "Twitter returned an error"
        try:
            error = user['errors'][0]
        except IndexError:
            error = {}
        try:
            msg = msg + ': ' + error['message']
            if msg[-1] != '.':
                msg = msg + '.'  # some texts end with a period, but not all... thanks, Twitter
        except KeyError:
            msg = msg + '. :( Maybe that user doesn\'t exist?'
        bot.say(msg)
        logger.debug('Screen name {sn} returned error code {code}: "{message}"'
            .format(sn=sn, code=error.get('code', '-1'),
                message=error.get('message', '(unknown description)')))
        return

    if user.get('url', None):
        url = user['entities']['url']['urls'][0]['expanded_url']  # Twitter c'mon, this is absurd
    else:
        url = ''

    joined = datetime.strptime(user['created_at'], '%a %b %d %H:%M:%S %z %Y')
    tz = time.get_timezone(
        bot.db, bot.config, None, trigger.nick, trigger.sender)
    joined_localized = time.format_time(
        bot.db, bot.config, tz, trigger.nick, trigger.sender, joined)

    message = ('[Twitter] {user[name]} (@{user[screen_name]}){verified}{protected}{location}{url}'
               ' | {user[friends_count]:,} friends, {user[followers_count]:,} followers'
               ' | {user[statuses_count]:,} tweets, {user[favourites_count]:,} ♥s'
               ' | Joined: {abstime}').format(
               user=user,
               verified=(' ✔️' if user['verified'] else ''),
               protected=(' 🔒' if user['protected'] else ''),
               location=(' | ' + user['location'] if user.get('location', None) else ''),
               url=(' | ' + url if url else ''),
               abstime=joined_localized)

    bot.say(message)
