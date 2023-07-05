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

**Twitter cookies are required to use this plugin** as of 1 July 2023. You may
want to minimize the risk of adverse action by using a throwaway login instead
of your real profile; however, note that doing so will affect the rate limit
available to this plugin.

The easiest way to configure `sopel-twitter` is via Sopel's configuration
wizard – simply run `sopel-plugins configure twitter` and enter the cookie
values for which it prompts you.

Otherwise, you can edit your bot's configuration file:

```ini
[twitter]
cookies =
    auth_token=df4c7364f4fac2b3843904ecc566b0e1accdf98b;
    ct0=23f96509cba936b732cd39e171dce0fa5da9ecd1d7f3551258fe3e1a21da79a797e80496e8190613ba8a8ebc07ef6d8004b17518e84f9b6f8100738c5243a3da3139c87a5a55e46d70ed99cf0f068a23
# Required: Cookies from Twitter
# Newlines are not required, but the semicolon (;) very much is!
# You will have to pull this from your own logged-in account; rate limits will
# vary depending on the account's verification/Blue status.

show_quoted_tweets = True
# Optional: For quote-tweets, send a second message showing the quoted tweet?
# Default: True

alternate_domains =
    fxtwitter.com
    vxtwitter.com
    nitter.net
# Optional: What other domains should we treat like twitter domains?
# Default: fxtwitter.com, vxtwitter.com, nitter.net
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
