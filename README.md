# sopel-twitter

A Twitter plugin for Sopel.

## Getting your API credentials

[See here](https://developer.twitter.com/en/docs/basics/getting-started) for
Twitter's account registration process. Unfortunately, it has become a Process
with a capital P, involving manual verification & sometimes lengthy wait
times. Twitter's v2 API added even more steps and restrictions. We hobbyists
just have to live with them; they're designed for much bigger fish than us.

Once you have a Twitter developer account, you can [create an
app](https://developer.twitter.com/en/apps/create) for your instance of
sopel-twitter. Only the "(required)" fields are, well, required. No need to set
a callback URL, turn on "Sign in with Twitter", or any of that. You can use
`https://github.com/sopel-irc/sopel-twitter` for your app's "Website URL".

After your App is set up, you must associate it with a Project. Then you can
visit the "Keys and tokens" tab of its settings to generate a Bearer Token,
and finally put your App's Bearer Token into Sopel's settings file using one
of these methods:

* Paste it into the file manually:
  ```ini
  [twitter]
  bearer_token = ABCDEFGHIJKLMNOPQRSTUVWXYZ_and_so_on
  ```
* `sopel-plugins configure twitter` in your favorite terminal/shell
* `sopel-config set twitter.bearer_token ABCDEFGHIJKLMNOPQRSTUVWXYZ_and_so_on`
  in your favorite terminal/shell (requires Sopel 7.1+)
