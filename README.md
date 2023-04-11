# sopel-twitter

A Twitter plugin for [Sopel](https://sopel.chat/).

## Installation

Releases are hosted on PyPI, so after installing Sopel, all you need is `pip`:

```bash
$ pip install sopel-twitter
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
show_quoted_tweets = True
# Optional: For quote-tweets, send a second message showing the quoted tweet?
# Default: True

alternate_domains =
    fxtwitter.com
    vxtwitter.com
    nitter.net
# Optional: What other domains should we treat like twitter domains?
# Default: vxtwitter.com, nitter.net
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
