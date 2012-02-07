""" A simple IRC bot using coleifer's IRCBot library. Returns ticket info from
Redmine and commit info from Github. """

try:
    import json
except ImportError:
    import simplejson as json

from irc import IRCBot, IRCConnection

from settings import *
from util import fetch_content, truncate, WebAPIError

class IRCBotMixin(object):
    """ Base class for IRCBot mixins """
    pass

class GithubMixin(IRCBotMixin):
    """ IRCBot mixin that provides Github services, currently uses Github v2
    API, should be upgraded to use v3 """

    github_url = GITHUB_URL
    github_user = GITHUB_USER
    github_repos = []
    github_credentials = ("%s/token" % GITHUB_API_USER, GITHUB_API_KEY)

    commit_msg = "Id: %s Committer: %s Date: %s Message: '%s' %s"
    commits = {}

    def github_command_patterns(self):
        """ Define command patterns for this mixin """
        return (
            ('.*#pull (?P<repo>\w+) (?P<pull>\d+)', self.pull_request_info),
            ('.*#(?P<sha>[0-9a-fA-F]{40})', self.commit_info),
            ('.*#commit (?P<sha>[0-9a-fA-F]{40})', self.commit_info),
        )

    def _populate_github_repos(self):
        """ Retrieve and populate the local cache of repos """
        url = "%s/api/v2/json/repos/show/%s" % (self.github_url,
            self.github_user)
        content = fetch_content(url, credentials=self.github_credentials)

        doc = json.loads(content)
        repos = doc.get('repositories', None)

        for repo in repos:
            name = repo.get('name', None)
            # weird getting some repos multiple times, distinct it
            if name and name not in self.github_repos:
                self.github_repos.append(name)

    def pull_request_info(self, sender, message, channel, repo, pull):
        self.log('looking for pull request %s in %s repo' % (pull, repo))
        link_url = 'https://github.com/Mediaphormedia/%s/pull/%s' % (repo, pull)
        return link_url

    def commit_info(self, sender, message, channel, sha):
        """ Retrieve commit info from Github, warm up repo cache if need be. """

        self.log('looking for commit %s' % sha)

        # check our local cache of commit info
        if sha in self.commits:
            return "%s: %s" % (sender, self.commits[sha])

        reply = None

        if not self.github_repos:
            self._populate_github_repos()

        for repo in self.github_repos:
            url = "%s/api/v2/json/commits/show/%s/%s/%s" % (self.github_url,
                self.github_user, repo, sha)
            try:
                content = fetch_content(url,
                    credentials=self.github_credentials)
                commit = json.loads(content).get('commit', None)
                if commit:
                    login = commit.get('committer', None).get('login', '')
                    date = commit.get('committed_date', '')
                    commit_url = commit.get('url', None)
                    if commit_url:
                        commit_url = "%s%s" % (self.github_url, commit_url)
                    msg = truncate(commit.get('message', ''), 50)
                reply = self.commit_msg % (sha[0:10], login,
                    date, msg, commit_url)

                # save it to a local cache so we don't waste API calls
                self.commits[sha] = reply

                reply = "%s: %s" % (sender, reply)

                # got our commit, don't waste API calls
                break
            except WebAPIError, ex:
                pass
            except ValueError, ex:
                # apparent incomplete json, go ahead and return
                reply = "Incomplete response, please try again."
                self.log("%s: %s" % (reply, ex))
                break
            except Exception, ex:
                reply = "Unknown error: %s" % ex
                self.log(reply)
        if not reply:
            reply = "%s: could not find %s" % (sender, sha)
            self.log(reply)
        return reply

class RedmineMixin(IRCBotMixin):
    """ IRCBot mixin that provides Redmine lookup services """

    redmine_url = REDMINE_URL
    redmine_api_key = REDMINE_API_KEY
    redmine_format = REDMINE_FORMAT

    def redmine_command_patterns(self):
        """ Define command patterns for this mixin """
        return (
            ('.*#ticket (?P<number>\d{3,})', self.ticket_info),
            ('.*#(?P<number>\d{3,})', self.ticket_info),
        )


    def ticket_info(self, sender, message, channel, number=None):
        """ Set reply to sender and handle errors """
        self.log('looking for ticket %s' % number)
        try:
            url = '%s/issues/%s.%s' % (self.redmine_url, number,
                self.redmine_format)
            headers = {'X-Redmine-API-Key': self.redmine_api_key}
            content = fetch_content(url, headers=headers)

            issue = json.loads(content).get('issue', None)

            if issue is None:
                raise WebAPIError(number)

            status = issue.get('status', None).get('name', '')
            priority = issue.get('priority', None).get('name', '')
            subject = truncate(issue.get('subject', ''), 50)
            tracker = issue.get('tracker', None).get('name', '')
            ticket_url = '%s/issues/%s' % (self.redmine_url, number)

            reply = "%s: %s: %s Priority: %s Status: %s Subj: '%s' %s" % (
                sender, tracker, number, priority, status, subject, ticket_url)

        except WebAPIError, ex:
            reply = '%s: could not find ticket %s (also: %s)' % (sender,
                number, ex)
            self.log(reply)
        except Exception, ex:
            reply = 'Unknown error: %s' % ex
            self.log(reply)
        return reply


class MPMBot(IRCBot, GithubMixin, RedmineMixin):
    """
    Subclasses IRCBot to construct a bot that responds to request for commit
    and ticket information. Queries Redmine instances and Github accounts based
    on settings.py
    """

    def __init__(self, start=False):
        self.conn = IRCConnection(HOST, PORT, NICK)

        self.register_callbacks()
        if start:
            self.run()

    def run(self):
        """ Start the IRC bot and connect to our channels """

        while 1:
            self.conn.connect()

            channels = CHANNELS or []

            for channel in channels:
                self.conn.join(channel)

            self.conn.enter_event_loop()

    def log(self, text):
        """ Shortcut to our logger """
        self.conn.logger.info(text)

    def command_patterns(self):
        """ Define dispatch regexes """
        patterns = ()

        for base in MPMBot.mro():
            if issubclass(base, IRCBotMixin):
                func = '%s_command_patterns' % base.__name__[0:-5].lower()
                if hasattr(self, func):
                    func = getattr(self, func, None)
                    patterns += (func())

        return patterns

if __name__ == '__main__':
    MPMBot(start=True)
