Highfive
========

GitHub hooks to provide an encouraging atmosphere for new contributors

See this bot in action: [@rails-bot](https://github.com/rails-bot?tab=activity)

Install
=======

To install `highfive` you just need to execute the `setup.py` script or use
`pip` directly. Both commands have to be executed from the directory where the
`setup.py` script is located.

    $ pip install -r requirements.txt
    $ python setup.py install

or

    $ pip install -r requirements.txt
    $ pip install . # the dot is important ;)


Adding a Project
================

To make rails-highfive interact with a new repo, add a configuration file in
`highfive/configs`, with a filename of the form `reponame.json`.

It should look like:

```
{
    "groups":{
        "all": ["@username", "@otheruser"],
        "subteamname": ["@subteammember", "@username"]
    },
    "dirs":{
        "dirname":  ["subteamname", "@anotheruser"]
    },
    "contributing": "http://project.tld/contributing_guide.html",
    "expected_branch": "develop"
}
```

The `groups` section allows you to alias lists of usernames. You should
specify at least one user in the group "all"; others are optional.

The `dirs` section is where you map directories of the repo to users or
groups who're eligible to review PRs affecting it. This section can be left
blank.

`contributing` specifies the contribution guide link in the message which
welcomes new contributors to the repository. If `contributing` is not
present, the [Rails contributing guide][railscontrib] will be linked instead.

If PRs should be filed against a branch other than `master`, specify the
correct destination in the `expected_branch` field. If `expected_branch` is
left out, highfive will assume that PRs should be filed against `master`.
The bot posts a warning on any PR that targets an unexpected branch.

[railscontrib]: http://edgeguides.rubyonrails.org/contributing_to_ruby_on_rails.html

Deploying
=========

rails-highfive can be deployed on Heroku. You'll need to set up the following required environment variables:

* **GITHUB_USER**: the bot's GitHub user
* **GITHUB_TOKEN**: the bot's GitHub token
* **HOOK_SECRET**: a secret string that is shared with the GitHub webhook setup

To set up a webhook on GitHub for testing your bot, use the following settings on a repo or org:

* **Content type**: `application/json`
* **Secret**: the same string you used in the `HOOK_SECRET` env var for your bot
* **Events**:
  * Selet `Let me select individual events`
  * Selet `Issues`, `Pull request review comment`, `Issue comment`, `Pull request`
