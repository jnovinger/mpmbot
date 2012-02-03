# MPMbot - Hackday Project at Mediaphormedia
### 2/4/2012

MPMbot provides an IRC interface for our Redmine instance and possibly also for Github (time allowing).

## Dependencies:
- Python 2.x+
- httplib2
- requests
- simplejson
- Redmine instance
- IRC channel
- coleifers irc library
    - requires gevent (which required an apt-get install libevent-dev on my machine)

## How to use
- To get Github commit info:
    - #{{ commit_hash }}
        - ex: #7ca88483fb8af105a8920eb36f06688bdf35fda7
    - #commit {{ commit_has }}
        - ex: #commit 7ca88483fb8af105a8920eb36f06688bdf35fda7

- To get Redmine ticket info:
    - #{{ ticket_number }}
        - ex: #5000
    - #ticket {{ ticket_number }}
        - ex: #ticket 5000
