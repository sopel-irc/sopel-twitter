# coding=utf-8
"""sopel-twitter

A Twitter plugin for Sopel
"""
from __future__ import unicode_literals, absolute_import, division, print_function

from datetime import datetime
import json
import re

from tweety.bot import Twitter
from tweety import exceptions_ as tweety_errors

from sopel import plugin, tools
from sopel.config.types import (
    BooleanAttribute,
    ListAttribute,
    StaticSection,
)

logger = tools.get_logger('twitter')

DOMAIN_REGEX = r"https?://(?:m(?:obile)?\.)?twitter\.com/"
STATUS_REGEX = r"(?:\w+|i/web)/status/(?P<status>\d+)"
USER_REGEX = r"(?P<user>\w+)/?(?:\?.*)?$"
NEWLINE_RUN_REGEX = re.compile(r"\s*\n[\n\s]*")


class TwitterSection(StaticSection):
    show_quoted_tweets = BooleanAttribute('show_quoted_tweets', default=True)
    alternate_domains = ListAttribute(
        "alternate_domains",
        default=["vxtwitter.com", "nitter.net"],
    )


def configure(config):
    config.define_section('twitter', TwitterSection, validate=False)
    config.twitter.configure_setting(
        'show_quoted_tweets', 'When a tweet quotes another status, '
        'show the quoted tweet on a second IRC line?')


def setup(bot):
    bot.config.define_section('twitter', TwitterSection)
    bot.memory['tweety_app'] = Twitter()


def get_preferred_media_item_link(item):
    """
    Guess the most useful link for a given piece of embedded media.

    :param item: a single Media object from Tweety
    :return: the best-guess link to output for optimum IRC user utility
    :rtype: str

    Twitter puts just a thumbnail for the media link if it's animated/video.
    Ideally we'd like clients that support it to show inline video, not a
    thumbnail, so we need to apply a little guesswork to figure out if we can
    output a video clip instead of a static image.
    """
    variants = item.get('streams', [])

    if not variants:
        # static image, or unknown other rich media item; return static image
        return item['media_url_https']

    # if we've reached this point, it's probably "real" rich media
    if len(variants) > 1:
        # ugh, Twitter returns unsorted data
        variants.sort(key=lambda k: k.get('bitrate', 0))

    return variants[-1]['url']


def format_tweet(tweet):
    """
    Format a tweet object for display.

    :param tweet: the tweet object, as decoded JSON
    :return: the formatted tweet
    :rtype: tuple
    """
    text = NEWLINE_RUN_REGEX.sub("\n", tweet.text)
    text = text.replace("\n", " \u23CE ")  # Unicode symbol to indicate line-break
    urls = tweet.urls
    media = tweet.media

    # Remove link to quoted status itself, if it's present
    if tweet.is_quoted:
        for url in urls:
            if url['expanded_url'].rsplit('/', 1)[1] == tweet.quoted_tweet.id:
                # this regex matches zero-or-more whitespace behind the link, but
                # whitespace after the link only matches if it's trailing (that is,
                # not followed by more non-whitespace characters).
                text = re.sub(r'\s*%s(\s+(?!\S))?' % re.escape(url['url']), '', text)
                break  # there should only be one

    # Expand media links so clients with image previews can show them
    for item in media:
        url = get_preferred_media_item_link(item)
        replaced = text.replace(item.url, url)
        if replaced == text:
            # Twitter only puts the first media item's URL in the tweet body
            # We have to append the others ourselves
            text += ' ' + url
        else:
            text = replaced

    # Expand other links to full URLs
    for url in urls:
        text = text.replace(url['url'], url['expanded_url'])

    # Done! At least, until Twitter adds more entity types...
    u = tweet.author
    return u.name + ' (@' + u.username + '): ' + tools.web.decode(text)


def format_time(bot, trigger, stamp):
    """
    Format a Twitter-provided timestamp based on user/channel settings.

    :param bot: the Sopel instance from the triggering event
    :param trigger: the trigger itself
    :param datetime stamp: the timezone-aware timestamp
    :return: the formatted publish timestamp of the ``tweet``
    :rtype: str
    """
    tz = tools.time.get_timezone(
        bot.db, bot.config, None, trigger.nick, trigger.sender)
    return tools.time.format_time(
        bot.db, bot.config, tz, trigger.nick, trigger.sender, stamp)


def _twitter_alt_domains(path_regex):
    """Build a url_lazy loader for the specified callback type.

    :param str path_regex: The path to be appended to each domain regex
    :return: A loader to be called by url_lazy()
    :rtype: Callable[[Config], List[re.Pattern]]
    """
    def loader(settings):
        """Lazy loader for configured alt domains

        :param settings: bot.config
        :type settings: :class:`~sopel.config.Config`
        :return: A list of compiled regexes
        :rtype: List[re.Pattern]
        """
        return [
            re.compile(r"https?://{}/{}".format(domain, path_regex))
            for domain in settings.twitter.alternate_domains
        ]

    return loader


@plugin.url_lazy(_twitter_alt_domains(STATUS_REGEX))
@plugin.url(DOMAIN_REGEX + STATUS_REGEX)
def url_status(bot, trigger):
    output_status(bot, trigger, trigger.group("status"))


@plugin.url_lazy(_twitter_alt_domains(USER_REGEX))
@plugin.url(DOMAIN_REGEX + USER_REGEX)
def url_user(bot, trigger):
    output_user(bot, trigger, trigger.group("user"))


@plugin.commands('twitinfo')
@plugin.example('.twitinfo SopelIRC')
def user_command(bot, trigger):
    if not trigger.group(3):
        bot.reply("What user do you want me to look up?")
        return plugin.NOLIMIT

    output_user(bot, trigger, trigger.group(3))


def output_status(bot, trigger, id_):
    try:
        tweet = bot.memory['tweety_app'].tweet_detail(id_)
    except tweety_errors.InvalidTweetIdentifier:
        bot.say("Couldn't fetch that tweet. Most likely, it's either private or deleted.")
        return
    except (
        tweety_errors.GuestTokenNotFound,
        tweety_errors.ProxyParseError,
        tweety_errors.UnknownError,
    ):
        bot.say("Can't access Twitter data. Please try again later.")
        return

    template = "[Twitter] {tweet} | {RTs} RTs | {hearts} ♥s | Posted: {posted}"

    bot.say(template.format(tweet=format_tweet(tweet),
                            RTs=tweet.retweet_counts,
                            hearts=tweet.likes,
                            posted=format_time(bot, trigger, tweet.created_on)))

    if (
        bot.config.twitter.show_quoted_tweets
        and tweet.is_quoted
        and tweet.quoted_tweet is not None
    ):
        tweet = tweet.quoted_tweet
        bot.say(template.format(tweet='Quoting: ' + format_tweet(tweet),
                                RTs=tweet.retweet_counts,
                                hearts=tweet.likes,
                                posted=format_time(bot, trigger, tweet.created_on)))


def output_user(bot, trigger, sn):
    try:
        user = Twitter(sn).get_user_info()
    except tweety_errors.UserNotFound:
        bot.say("User not found.")
        return
    except tweety_errors.UserProtected:
        bot.say("User profile is protected.")
        return
    except (
        tweety_errors.GuestTokenNotFound,
        tweety_errors.ProxyParseError,
        tweety_errors.UnknownError,
    ):
        bot.say("Can't access Twitter data. Please try again later.")
        return

    url = None
    try:
        url = user.entities['url']['urls'][0]['expanded_url']
    except (KeyError, IndexError):
        pass

    bio = user.get('description', None)
    if bio:
        for link in user['entities']['description']['urls']:  # bloody t.co everywhere
            bio = bio.replace(link['url'], link['expanded_url'])
        bio = tools.web.decode(bio)

    message = ('[Twitter] {user[name]} (@{user[screen_name]}){verified}{protected}{location}{url}'
               ' | {user[friends_count]:,} friends, {user[followers_count]:,} followers'
               ' | {user[statuses_count]:,} tweets, {user[favourites_count]:,} ♥s'
               ' | Joined: {joined}{bio}').format(
               user=user,
               verified=(' ✔️' if user['verified'] else ''),
               protected=(' 🔒' if user['protected'] else ''),
               location=(' | ' + user['location'] if user.get('location', None) else ''),
               url=(' | ' + url if url else ''),
               joined=format_time(bot, trigger, user['created_at']),
               bio=(' | ' + bio if bio else ''))

    bot.say(message, truncation=' […]')
