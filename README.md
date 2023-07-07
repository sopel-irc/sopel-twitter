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

# How to find Your Twitter Authentication Token

Follow these steps to locate your authentication token on Twitter. This token is often needed for using third-party applications with your Twitter account.

**Step 1: Log into Twitter**

Start by opening your preferred web browser on your computer. Navigate to Twitter's website and log into your account.

\```markdown
1. Open a web browser on your computer.
2. Go to https://www.twitter.com.
3. Log in to your Twitter account.
\```

**Step 2: Open Developer Tools**

Next, open the developer tools in your web browser. You can do this by either right-clicking anywhere on the page and selecting "Inspect", or by using the keyboard shortcut `CTRL + SHIFT + I`.

\```markdown
1. Right-click anywhere on the page.
2. Click on "Inspect" from the context menu (or press `CTRL + SHIFT + I`).
\```

**Step 3: Navigate to the "Application" Tab**

Once the developer tools panel is open, click on the "Application" tab.

\```markdown
1. In the developer tools panel, click on the "Application" tab.
\```

**Step 4: Expand the "Cookies" Section**

In the sidebar of the "Application" tab, you'll find a section titled "Storage". Click on the arrow next to "Cookies" to expand it. Then, select `https://twitter.com`.

\```markdown
1. On the sidebar, locate the "Storage" section.
2. Click the arrow next to "Cookies" to expand it.
3. Click on `https://twitter.com`.
\```

**Step 5: Locate and Copy the "auth_token" Value**

Finally, in the expanded list under `https://twitter.com`, find the name "auth_token". The value associated with "auth_token" is what you need. Right-click it and select "Copy".

\```markdown
1. In the expanded list under `https://twitter.com`, find the name "auth_token".
2. Right-click on the value of "auth_token" and select "Copy".
\```

## Usage

Just send a link to a tweet or profile!

You can also retrieve a user's info with the `.twitinfo` command:

```irc
< Wiz> .twitinfo NASA
< Sopel> [Twitter] NASA (@NASA) ✔️ | Pale Blue Dot | http://www.nasa.gov/
         | 204 friends, 46,602,251 followers | 65,377 tweets, 13,040 ♥s
         | Joined: 2007-12-19 - 20:20:32UTC | There's space for everybody. ✨
```
