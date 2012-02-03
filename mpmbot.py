""" A simple IRC bot using coleifer's IRCBot library. Returns ticket info from
Redmine and commit info from Github. """

import httplib
import httplib2
from pdb import set_trace ### REMOVE BEFORE COMITTING
import requests
import socket
try:
    import json
except ImportError:
    import simplejson as json

from irc import IRCBot, run_bot

from settings import (GITHUB_API_KEY, GITHUB_API_USER, GITHUB_URL, GITHUB_USER,
    REDMINE_FORMAT, REDMINE_API_KEY, REDMINE_URL)

DEBUG = False

class WebAPIError(Exception):
    """ Generic web service error to handle different API call failures """
    pass

if not DEBUG:
    def set_trace():
        """ If DEBUG is set to False, redefine set_trace so we don't have to
        spent time in pdb. """
        pass

def shorten(msg):
    """ Shorten to 50 characters, if too long """
    if len(msg) > 50:
        msg = msg[0:47] + '...'
    return msg

class MPMBot(IRCBot):
    """
    Subclasses IRCBot to construct a bot that responds to request for commit
    and ticket information. Queries Redmine instances and Github accounts based
    on settings.py
    """

    redmine_url = REDMINE_URL
    redmine_api_key = REDMINE_API_KEY
    redmine_format = REDMINE_FORMAT

    github_api_key = GITHUB_API_KEY
    github_api_user = GITHUB_API_USER
    github_url = GITHUB_URL
    github_user = GITHUB_USER
    github_repos = []
    github_credentials = ("%s/token" % GITHUB_API_USER, GITHUB_API_KEY)

    def _fetch_content(self, url, headers):
        """ Helper method to handle HTTP API calls """
        http = httplib2.Http(timeout=5)

        try:
            response, content = http.request(url, "GET", headers=headers)
        except (socket.error, httplib.error), ex:
            raise WebAPIError("error accessing web service: %s" % ex)

        if int(response.get('status', '404')) != 200:
            raise WebAPIError("Got %s while trying to access web service." % response.get('status', '404'))

        return content

    def _fetch_github_content(self, url):
        """ Github specific helper method to handle HTTP API calls """
        try:
            req = requests.get(url, auth=self.github_credentials)
            if req.status_code != 200:
                raise WebAPIError("Got %s while trying to access Github." % req.status_code)

            return req.text
        except Exception, ex:
            raise WebAPIError("error accessing Github: %s" % ex)


    def _populate_github_repos(self):
        """ Retrieve and populate the local cache of repos """
        url = "%s/api/v2/json/repos/show/%s" % (self.github_url,
            self.github_user)
        set_trace()
        content = self._fetch_github_content(url)

        doc = json.loads(content)
        repos = doc.get('repositories', None)

        for repo in repos:
            name = repo.get('name', None)
            # weird getting some repos multiple times, distinct it
            if name and name not in self.github_repos:
                self.github_repos.append(name)


    def _get_commit_info(self, commit):
        """ Loop through all repos to find commit, construct msg and return """
        set_trace()
        if not self.github_repos:
            self._populate_github_repos()

        for repo in self.github_repos:
            url = "%s/api/v2/json/commits/show/%s/%s/%s" % (self.github_url,
                self.github_user, repo, commit)
            try:
                set_trace()
                content = self._fetch_github_content(url)
                set_trace()
                doc = json.loads(content)
                commit_rec = doc.get('commit', None)
                if commit_rec:
                    login = commit_rec.get('committer', None).get('login', '')
                    date = commit_rec.get('committed_date', '')
                    commit_url = commit_rec.get('url', None)
                    if commit_url:
                        commit_url = "%s%s" % (self.github_url, commit_url)
                    msg = shorten(commit_rec.get('message', ''))
                return "Id: %s Committer: %s Date: %s Message: '%s' %s" % (commit[0:10], login, date, msg, commit_url)
            except Exception, ex:
                pass


    def _get_ticket_info(self, number):
        """ Construct ticket info message and return """
        url = '%s/issues/%s.%s' % (self.redmine_url, number,
            self.redmine_format)
        headers = {'X-Redmine-API-Key': self.redmine_api_key}
        content = self._fetch_content(url, headers)
        doc = json.loads(content)

        issue = doc.get('issue', None)

        if issue is None:
            raise WebAPIError(number)

        status = issue.get('status', None).get('name', '')
        priority = issue.get('priority', None).get('name', '')
        subject = shorten(issue.get('subject', ''))
        tracker = issue.get('tracker', None).get('name', '')
        ticket_url = '%s/issues/%s' % (self.redmine_url, number)

        return "%s: %s Priority: %s Status: %s Subj: '%s' %s" % (tracker,
            number, priority, status, subject, ticket_url)

    def commit_info(self, sender, message, channel, commit=None):
        """ Set reply to sender and handle errors """
        self.conn.logger.info('looking for commit %s' % commit)
        try:
            content = self._get_commit_info(commit)
            reply = "%s: %s" % (sender, content)
        except WebAPIError, ex:
            reply = "%s: could not find that commit (also: %s)" % (sender, ex)
        except Exception, ex:
            reply = "Unknown error: %s" % ex
        return reply

    def ticket_info(self, sender, message, channel, number=None):
        """ Set reply to sender and handle errors """
        self.conn.logger.info('looking for ticket %s' % number)
        try:
            content = self._get_ticket_info(number)
            reply = '%s: %s' % (sender, content)
        except WebAPIError, ex:
            reply = '%s: could not find ticket %s (also: %s)' % (sender,
                number, ex)
        except Exception, ex:
            reply = 'Unknown error: %s' % ex
        return reply

    def command_patterns(self):
        """ Define dispatch regexes """
        return(
            ('.*#(?P<commit>[0-9a-fA-F]{40})', self.commit_info),
            ('.*#commit (?P<commit>[0-9a-fA-F]{40})', self.commit_info),
            ('.*#ticket (?P<number>\d{3,})', self.ticket_info),
            ('.*#(?P<number>\d{3,})', self.ticket_info),
        )

HOST = 'irc.freenode.net'
PORT = 6667
NICK = 'mpmbot'
CHANNELS = ['#mpmbot',]

run_bot(MPMBot, HOST, PORT, NICK, CHANNELS)
