# sopel-twitter

A Twitter plugin for [Sopel](https://sopel.chat/).

## Installation

Releases are hosted on PyPI, so after installing Sopel, all you need is `pip`:

```bash
$ pip install sopel-twitter
```

If you want to use the development version, simply clone the repository and use
`pip install path/to/sopel-twitter`

### Newer library versions

`sopel-twitter` relies on [a third-party library][tweety-source] to access data,
which does not always publish its latest code to PyPI. If you run into problems
with this plugin, [install the latest library code][tweety-source-updates] and
see if that solves your issue.

Please also feel free to submit pull requests updating this plugin's version
constraints if you have tested a newer library release than what is currently
allowed. Thanks for your help!

[tweety-source]: https://github.com/mahrtayyab/tweety
[tweety-source-updates]: https://github.com/mahrtayyab/tweety#keep-synced-with-latest-fixes

## Configuring

**Twitter account required to use this plugin** as of 1 July 2023. You probably
want to minimize the potential impact of adverse action by using a throwaway
login instead of your real profile. New accounts can (as of 19 July 2023) be
verified using only an email address.

The easiest way to configure `sopel-twitter` is via Sopel's configuration
wizard – simply run `sopel-plugins configure twitter` and enter the values
for which it prompts you.

Otherwise, you can edit your bot's configuration file:

```ini
[twitter]
username = mybotaccount
password = s3cretb0tp@ss
# Both Required

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

### Important housekeeping notes

The library this plugin uses for Twitter data access previously stored its
login session data in **the current working directory**. For Sopel, that was
the directory from which the `sopel` command was run.

As of sopel-twitter 1.3.1, a newer library version became available with
support for storing session data in Sopel's `homedir` instead. You can clean
up the old session files left behind by sopel-twitter 1.3.0 by running e.g.
`find / -type f -name 'sopel-twitter*.json' 2>/dev/null`. (Running `find` on
`/` tends to output numerous "Permission denied" errors, so suppressing stderr
is recommended.)

Prior to the release of sopel-twitter 1.3.2, the session data filename changed
upstream from `.json` to `.tw_session`. This plugin will attempt to rename the
old session file if it exists, but if that fails you might want to clean up the
leftover `config_name.sopel-twitter.json` file.

## Usage

Just send a link to a tweet or profile!

You can also retrieve a user's info with the `.twitinfo` command:

```irc
< Wiz> .twitinfo NASA
< Sopel> [Twitter] NASA (@NASA) ✔️ | Pale Blue Dot | http://www.nasa.gov/
         | 204 friends, 46,602,251 followers | 65,377 tweets, 13,040 ♥s
         | Joined: 2007-12-19 - 20:20:32UTC | There's space for everybody. ✨
```
