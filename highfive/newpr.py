#!/usr/bin/python

import base64
import urllib, urllib2
import web
import json
import random
import sys
from StringIO import StringIO
import gzip
import re
import time
import socket
import os
import hmac
import hashlib

# Maximum per page is 100. Sorted by number of commits, so most of the time the
# contributor will happen early,
contributors_url = "https://api.github.com/repos/%s/%s/contributors?per_page=100"
post_comment_url = "https://api.github.com/repos/%s/%s/issues/%s/comments"
collabo_url = "https://api.github.com/repos/%s/%s/collaborators?per_page=100"
issue_url = "https://api.github.com/repos/%s/%s/issues/%s"

welcome_with_reviewer = '@%s (or someone else)'
welcome_without_reviewer = "@rafaelfranca (NB. this repo may be misconfigured)"
raw_welcome = """Thanks for the pull request, and welcome! The Rails team is excited to review your changes, and you should hear from %s soon.

If any changes to this PR are deemed necessary, please add them as extra commits. This ensures that the reviewer can see what has changed since they last reviewed the code. Due to the way GitHub handles out-of-date commits, this should also make it reasonably obvious what issues have or haven't been addressed. Large or tricky changes may require several passes of review and changes.

Please see [the contribution instructions](%s) for more information.
"""


def welcome_msg(reviewer, config):
    if reviewer is None:
        text = welcome_without_reviewer
    else:
        text = welcome_with_reviewer % reviewer
    # Default to the Rails contribution guide if "contributing" wasn't set
    link = config.get('contributing')
    if not link:
        link = "http://edgeguides.rubyonrails.org/contributing_to_ruby_on_rails.html"
    return raw_welcome % (text, link)

warning_summary = '<img src="http://www.joshmatthews.net/warning.svg" alt="warning" height=20> **Warning** <img src="http://www.joshmatthews.net/warning.svg" alt="warning" height=20>\n\n%s'
surprise_branch_warning = "Pull requests are usually filed against the %s branch for this repo, but this one is against %s. Please double check that you specified the right target!"

review_with_reviewer = 'r? @%s\n\n(@rails-bot has picked a reviewer for you, use r? to override)'
review_without_reviewer = '@%s: no appropriate reviewer found, use r? to override'

def review_msg(reviewer, submitter):
    if reviewer is None:
        text = review_without_reviewer % submitter
    else:
        text = review_with_reviewer % reviewer
    return text

reviewer_re = re.compile("\\b[rR]\?[:\- ]*@([a-zA-Z0-9\-]+)")

def _load_json_file(name):
    configs_dir = os.path.join(os.path.dirname(__file__), 'configs')

    with open(os.path.join(configs_dir, name)) as config:
        return json.loads(config.read())

def api_req(method, url, data=None, username=None, token=None, media_type=None):
    data = None if not data else json.dumps(data)
    headers = {} if not data else {'Content-Type': 'application/json'}
    req = urllib2.Request(url, data, headers)
    req.get_method = lambda: method
    if token:
        base64string = base64.standard_b64encode('%s:x-oauth-basic' % (token)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)

    if media_type:
        req.add_header("Accept", media_type)
    f = urllib2.urlopen(req)
    header = f.info()
    if header.get('Content-Encoding') == 'gzip':
        buf = StringIO(f.read())
        f = gzip.GzipFile(fileobj=buf)
    body = f.read()
    return { "header": header, "body": body }

def post_comment(body, owner, repo, issue, user, token):
    global post_comment_url
    try:
        result = api_req("POST", post_comment_url % (owner, repo, issue), {"body": body}, user, token)['body']
    except urllib2.HTTPError, e:
        if e.code == 201:
            pass
        else:
            raise e

def set_assignee(assignee, owner, repo, issue, user, token, author):
    global issue_url
    try:
        print "Assigning %s to %s" % (issue, assignee)
        result = api_req("PATCH", issue_url % (owner, repo, issue), {"assignee": assignee}, user, token)['body']
    except urllib2.HTTPError, e:
        if e.code == 201:
            pass
        else:
            raise e

def get_collaborators(owner, repo, user, token):
    try:
        result = api_req("GET", collabo_url % (owner, repo), None, user, token)['body']
    except urllib2.HTTPError, e:
        if e.code == 201:
            pass
        else:
            raise e
    return [c['login'] for c in json.loads(result)]

# This function is adapted from https://github.com/kennethreitz/requests/blob/209a871b638f85e2c61966f82e547377ed4260d9/requests/utils.py#L562
# Licensed under Apache 2.0: http://www.apache.org/licenses/LICENSE-2.0
def parse_header_links(value):
    if not value:
        return None

    links = {}
    replace_chars = " '\""
    for val in value.split(","):
        try:
            url, params = val.split(";", 1)
        except ValueError:
            url, params = val, ''

        url = url.strip("<> '\"")

        for param in params.split(";"):
            try:
                key, value = param.split("=")
            except ValueError:
                break
            key = key.strip(replace_chars)
            if key == 'rel':
                links[value.strip(replace_chars)] = url

    return links

def is_new_contributor(username, owner, repo, user, token, config):
    if 'contributors' in config and username in config['contributors']:
        return False

    # iterate through the pages to try and find the contributor
    url = contributors_url % (owner, repo)
    while True:
        stats_raw = api_req("GET", url, None, user, token)
        stats = json.loads(stats_raw['body'])
        links = parse_header_links(stats_raw['header'].get('Link'))

        for contributor in stats:
            if contributor['login'] == username:
                return False

        if not links or 'next' not in links:
            return True
        url = links['next']

# If the user specified a reviewer, return the username, otherwise returns None.
def find_reviewer(commit_msg):
    print "Finding reviewer in: %s" % commit_msg
    match = reviewer_re.search(commit_msg)
    if not match:
        return None
    return match.group(1)

# Choose a reviewer for the PR
def choose_reviewer(repo, owner, diff, exclude, config):
    if not (owner == 'rails'):
        return 'test_user_selection_ignore_this'

    # Get JSON data on reviewers.
    dirs = config.get('dirs', {})
    groups = config['groups']

    # fill in the default groups, ensuring that overwriting is an
    # error.
    global_ = _load_json_file('_global.json')
    for name, people in global_['groups'].iteritems():
        assert name not in groups, "group %s overlaps with _global.json" % name
        groups[name] = people


    most_changed = None
    # If there's directories with specially assigned groups/users
    # inspect the diff to find the directory (under src) with the most
    # additions
    if dirs:
        counts = {}
        cur_dir = None
        for line in diff.split('\n'):
            if line.startswith("diff --git "):
                # update cur_dir
                cur_dir = None
                start = line.find(" b/src/") + len(" b/src/")
                if start == -1:
                    continue
                end = line.find("/", start)
                if end == -1:
                    continue

                cur_dir = line[start:end]

                # A few heuristics to get better reviewers
                if cur_dir.startswith('librustc'):
                    cur_dir = 'librustc'
                if cur_dir == 'test':
                    cur_dir = None
                if cur_dir and cur_dir not in counts:
                    counts[cur_dir] = 0
                continue

            if cur_dir and (not line.startswith('+++')) and line.startswith('+'):
                counts[cur_dir] += 1

        # Find the largest count.
        most_changes = 0
        for dir, changes in counts.iteritems():
            if changes > most_changes:
                most_changes = changes
                most_changed = dir

    # lookup that directory in the json file to find the potential reviewers
    potential = groups['all']
    if most_changed and most_changed in dirs:
        potential.extend(dirs[most_changed])


    # expand the reviewers list by group
    reviewers = []
    seen = {"all"}
    while potential:
        p = potential.pop()
        if p.startswith('@'):
            # remove the '@' prefix from each username
            reviewers.append(p[1:])
        elif p in groups:
            # avoid infinite loops
            assert p not in seen, "group %s refers to itself" % p
            seen.add(p)
            # we allow groups in groups, so they need to be queued to be resolved
            potential.extend(groups[p])

    if exclude in reviewers:
        reviewers.remove(exclude)

    if reviewers:
        random.seed()
        return random.choice(reviewers)
    else:
        # no eligible reviewer found
        return None

def unexpected_branch(payload, config):
    """ returns (expected_branch, actual_branch) if they differ, else None
    """

    # If unspecified, assume master.
    expected_target = None
    if "expected_branch" in config:
        expected_target = config["expected_branch"]
    if not expected_target:
        expected_target = "master"

    # ie we want "stable" in this: "base": { "label": "rust-lang:stable"...
    actual_target = payload['pull_request']['base']['label'].split(':')[1]

    if expected_target != actual_target:
        return (expected_target, actual_target)
    return False

def new_pr(payload, user, token):
    owner = payload['pull_request']['base']['repo']['owner']['login']
    repo = payload['pull_request']['base']['repo']['name']

    author = payload["pull_request"]['user']['login']
    issue = str(payload["number"])
    diff = api_req("GET", payload["pull_request"]["diff_url"])['body']

    msg = payload["pull_request"]['body']
    reviewer = find_reviewer(msg)
    post_msg = False

    config = _load_json_file(repo + '.json')

    if not reviewer and author not in get_collaborators(owner, repo, user, token):
        post_msg = True
        diff = api_req("GET", payload["pull_request"]["diff_url"])['body']
        reviewer = choose_reviewer(repo, owner, diff, author, config)

    if reviewer:
        set_assignee(reviewer, owner, repo, issue, user, token, author)

    if is_new_contributor(author, owner, repo, user, token, config):
        post_comment(welcome_msg(reviewer, config), owner, repo, issue, user, token)
    elif post_msg:
        post_comment(review_msg(reviewer, author), owner, repo, issue, user, token)

    warnings = []

    surprise = unexpected_branch(payload, config)
    if surprise:
        warnings.append(surprise_branch_warning % surprise)

    if warnings:
        post_comment(warning_summary % '\n'.join(map(lambda x: '* ' + x, warnings)), owner, repo, issue, user, token)


def new_comment(payload, user, token):
    # Check the issue is a PR and is open.
    if 'issue' not in payload or payload['issue']['state'] != 'open' or 'pull_request' not in payload['issue']:
        return

    commenter = payload['comment']['user']['login']
    # Ignore our own comments.
    if commenter == user:
        return

    owner = payload['repository']['owner']['login']
    repo = payload['repository']['name']

    # Check the commenter is the submitter of the PR or the previous assignee.
    author = payload["issue"]['user']['login']
    if not (author == commenter or (payload['issue']['assignee'] and commenter == payload['issue']['assignee']['login'])):
        # Get collaborators for this repo and check if the commenter is one of them
        if commenter not in get_collaborators(owner, repo, user, token):
            print "%s is not a repository collaborator" % commenter
            return

    # Check for r? and set the assignee.
    msg = payload["comment"]['body']
    reviewer = find_reviewer(msg)
    if reviewer:
        issue = str(payload['issue']['number'])
        set_assignee(reviewer, owner, repo, issue, user, token, author)

user = os.environ.get('GITHUB_USER')
token = os.environ.get('GITHUB_TOKEN')

if not user or not token:
    print 'User is not configured'
    exit(1)


urls = (
    '/', 'index'
)

class index:
    def GET(self):
        return 'PONG'

    def POST(self):
        post = web.data()

        digest = hmac.new(os.environ.get('HOOK_SECRET'), post, hashlib.sha1).hexdigest()
        request_signature = web.ctx.env.get('HTTP_X_HUB_SIGNATURE').split('=')[1]

        if hmac.compare_digest(digest, request_signature):
            payload = json.loads(post)
            if "action" in payload:
                if payload["action"] == "opened":
                    new_pr(payload, user, token)
                elif payload["action"] == "created":
                    new_comment(payload, user, token)
        else:
            print 'Unautorized request'

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

