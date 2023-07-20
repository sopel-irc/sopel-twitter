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

### Important note

The library this plugin uses for Twitter data access stores its login session
data in **the current working directory**. For Sopel, that is the directory
from which the `sopel` command is run.

A future library release promises to add support for specifying where to store
session data, at which point this plugin will be updated to use the `homedir`
of Sopel's configuration (`~/.sopel` by default). You will be able to locate
the old session files by running e.g. `find / -type f -name
'sopel-twitter*.json' 2>/dev/null`. (Running `find` on `/` tends to output
numerous "Permission denied" errors, so suppressing stderr is recommended.)

## Usage

Just send a link to a tweet or profile!

You can also retrieve a user's info with the `.twitinfo` command:

```irc
< Wiz> .twitinfo NASA
< Sopel> [Twitter] NASA (@NASA) ✔️ | Pale Blue Dot | http://www.nasa.gov/
         | 204 friends, 46,602,251 followers | 65,377 tweets, 13,040 ♥s
         | Joined: 2007-12-19 - 20:20:32UTC | There's space for everybody. ✨
```
