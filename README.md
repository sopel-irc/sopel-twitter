# sopel-twitter

A Twitter plugin for [Sopel](https://sopel.chat/).

## Getting your API credentials

Twitter's [developer application
process](https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api)
has become rather tedious and annoying, involving a game of 20 questions with
manual verification and sometimes long wait times. Unfortunately you'll need
to go through it in order to use this plugin, since the API is needed to
retrieve account data and rich link previews.

Once you have a Twitter developer account, you can [create an
app](https://developer.twitter.com/en/portal/apps/new) for your instance of
sopel-twitter. You'll need the API Key (`consumer_key`) and Secret
(`consumer_secret`) for your bot configuration.

## Installation

Releases are hosted on PyPI, so after installing Sopel, all you need is `pip`:

```bash
$ pip install sopel-modules.twitter
```

If you want to use the development version, simply clone the repository and use
`pip install path/to/sopel-twitter`

## Configuring

The easiest way to configure `sopel-twitter` is using Sopel's configuration
wizard – simply run `sopel-plugins configure twitter` and enter the
credentials for the Twitter application you created.

Otherwise, you can edit your bot's configuration file:

```ini
[twitter]
consumer_key = YOUR_API_KEY_HERE
consumer_secret = YOUR_API_SECRET_HERE
# Optional: For quote-tweets, send a second message showing the quoted tweet?
# Default: True
show_quoted_tweets = True
```

## Usage

Just send a link to a tweet or profile!

You can also retrieve a user's info with the `.twitinfo` command:

```irc
< Wiz> .twitinfo NASA
< Sopel> [Twitter] NASA (@NASA) ✔️ | Pale Blue Dot | http://www.nasa.gov/
         | 204 friends, 46,602,251 followers | 65,377 tweets, 13,040 ♥s
         | Joined: 2007-12-19 - 20:20:32UTC | There's space for everybody. ✨
```
