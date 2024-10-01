# coding=utf-8
"""sopel-twitter

A Twitter plugin for Sopel
"""
from __future__ import unicode_literals, absolute_import, division, print_function

from datetime import datetime
import json
import os.path
import re

from tweety import Twitter, exceptions_ as tweety_errors

from sopel import plugin, tools
from sopel.config.types import (
    BooleanAttribute,
    ListAttribute,
    NO_DEFAULT,
    SecretAttribute,
    StaticSection,
    ValidatedAttribute,
)

logger = tools.get_logger('twitter')

DOMAIN_REGEX = r"https?://(?:m(?:obile)?\.)?(?:twitter|x)\.com/"
STATUS_REGEX = r"(?:\w+|i/web)/status/(?P<status>\d+)"
USER_REGEX = r"(?P<user>\w+)/?(?:\?.*)?$"
NEWLINE_RUN_REGEX = re.compile(r"\s*\n[\n\s]*")


class TwitterSection(StaticSection):
    username = ValidatedAttribute('username', default=NO_DEFAULT)
    password = SecretAttribute('password', default=NO_DEFAULT)
    show_quoted_tweets = BooleanAttribute('show_quoted_tweets', default=True)
    alternate_domains = ListAttribute(
        "alternate_domains",
        default=["vxtwitter.com", "fixvx.com", "nitter.net"],
    )


def configure(config):
    config.define_section('twitter', TwitterSection, validate=False)
    config.twitter.configure_setting(
        'username',
        "Username for your bot's Twitter account:")
    config.twitter.configure_setting(
        'password',
        "Password for your bot's Twitter account:")
    config.twitter.configure_setting(
        'show_quoted_tweets', 'When a tweet quotes another status, '
        'show the quoted tweet on a second IRC line?')


def setup(bot):
    bot.config.define_section('twitter', TwitterSection)

    # rename old session .json to new .tw_session format
    # but only if there isn't already a .tw_session file
    session_base = _get_tweety_session_name(bot)
    session_json = session_base + '.json'
    session_tw = session_base + '.tw_session'

    if (
        os.path.isfile(session_json)
        and not os.path.isfile(session_tw)
    ):
        os.rename(session_json, session_tw)


def _get_tweety_session_name(bot):
    """Return a session name for this plugin + bot config."""
    return os.path.join(
        _get_tweety_session_path(bot),
        "{}.sopel-twitter".format(bot.settings.basename)
    )


def _get_tweety_session_path(bot):
    """Return the path to where this plugin's sessions should live."""
    return os.path.expanduser(bot.settings.homedir)


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
    :rtype: str
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
            re.compile(r"https?://{}/{}".format(re.escape(domain), path_regex))
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
        app = Twitter(_get_tweety_session_name(bot))
        # sign_in() checks for an existing session, and tries to use it if
        # present. It will sign in with username & password if the session
        # doesn't exist or is expired/invalid.
        app.sign_in(bot.settings.twitter.username, bot.settings.twitter.password)

        tweet = app.tweet_detail(id_)
    except tweety_errors.DeniedLogin:
        bot.say("Twitter wouldn't let me log in. Please try again later. If this issue persists, contact my owner.")
        return
    except tweety_errors.ActionRequired:
        bot.say("Twitter's being (unusually) difficult. I can't sign in.")
        return
    except tweety_errors.InvalidCredentials:
        bot.say("Can't authenticate with Twitter. Please ask my owner to check my credentials.")
        return
    except tweety_errors.AuthenticationRequired:
        bot.say("That content requires authentication; sorry!")
        return
    except tweety_errors.UserProtected:
        bot.say("User profile is protected.")
        return
    except tweety_errors.ProtectedTweet:
        bot.say("Tweet is protected.")
        return
    except tweety_errors.RateLimitReached:
        bot.say("Rate limit reached. Please try again later.")
        return
    except tweety_errors.InvalidTweetIdentifier:
        bot.say("Couldn't fetch that tweet. It's probably private, 18+ flagged, or deleted.")
        return
    except (
        tweety_errors.GuestTokenNotFound,
        tweety_errors.ProxyParseError,
        tweety_errors.UnknownError,
    ):
        bot.say("Can't access Twitter data. Please try again later.")
        return

    preface = "[Twitter] {quoting}{tweet}"
    postface = " | {RTs} RTs | {hearts} ♥s | Posted: {posted}"

    bot.say(
        preface.format(quoting='', tweet=format_tweet(tweet)),
        truncation=' […]',
        trailing=postface.format(
            RTs=tweet.retweet_counts,
            hearts=tweet.likes,
            posted=format_time(bot, trigger, tweet.created_on),
        ),
    )

    if (
        bot.config.twitter.show_quoted_tweets
        and tweet.is_quoted
        and tweet.quoted_tweet is not None
    ):
        tweet = tweet.quoted_tweet
        bot.say(
            preface.format(quoting='Quoting ', tweet=format_tweet(tweet)),
            truncation=' […]',
            trailing=postface.format(
                RTs=tweet.retweet_counts,
                hearts=tweet.likes,
                posted=format_time(bot, trigger, tweet.created_on),
            ),
        )


def output_user(bot, trigger, sn):
    try:
        app = Twitter(_get_tweety_session_name(bot))
        # sign_in() checks for an existing session, and tries to use it if
        # present. It will sign in with username & password if the session
        # doesn't exist or is expired/invalid.
        app.sign_in(bot.settings.twitter.username, bot.settings.twitter.password)

        user = app.get_user_info(sn)
    except tweety_errors.DeniedLogin:
        bot.say("Twitter wouldn't let me log in. Please try again later. If this issue persists, contact my owner.")
        return
    except tweety_errors.ActionRequired:
        bot.say("Twitter's being (unusually) difficult. I can't sign in.")
        return
    except tweety_errors.InvalidCredentials:
        bot.say("Can't authenticate with Twitter. Please ask my owner to check my credentials.")
        return
    except tweety_errors.UserNotFound:
        bot.say("User not found.")
        return
    except tweety_errors.UserProtected:
        bot.say("User profile is protected.")
        return
    except tweety_errors.AuthenticationRequired:
        bot.say("That content requires authentication; sorry!")
        return
    except tweety_errors.RateLimitReached:
        bot.say("Rate limit reached. Please try again later.")
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

    bio = getattr(user, 'description', None)
    if bio:
        for link in user.entities['description']['urls']:  # bloody t.co everywhere
            bio = bio.replace(link['url'], link['expanded_url'])
        bio = tools.web.decode(bio)

    # fixup undocumentedly nullable int fields
    # upstream issue suggesting improvement: https://github.com/mahrtayyab/tweety/issues/87
    for field in ('friends_count', 'followers_count', 'statuses_count', 'favourites_count'):
        if getattr(user, field, None) is None:
            setattr(user, field, 0)

    message = ('[Twitter] {user.name} (@{user.screen_name}){verified}{protected}{location}{url}'
               ' | {user.friends_count:,} friends, {user.followers_count:,} followers'
               ' | {user.statuses_count:,} tweets, {user.favourites_count:,} ♥s'
               ' | Joined: {joined}{bio}').format(
               user=user,
               verified=(' ✔️' if user.verified else ''),
               protected=(' 🔒' if user.protected else ''),
               location=(' | ' + user.location if getattr(user, 'location', None) else ''),
               url=(' | ' + url if url else ''),
               joined=format_time(bot, trigger, user.created_at),
               bio=(' | ' + bio if bio else ''))

    bot.say(message, truncation=' […]')
