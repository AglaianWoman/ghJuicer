#!/usr/bin/env python3

import click
import requests
import sqlite3
from time import time, sleep

# The metadata keys (GitHub API v3 compatible) we're interested in.
# Used in get_user() and SQL insert.
# See the JSON response for this example call: https://api.github.com/users/joshuarli
KEEP = ('login', 'id', 'type', 'name', 'company', 'blog',
    'location', 'email', 'hireable', 'public_repos', 'followers',
    'following', 'created_at', 'updated_at')

with open('oauthtk.txt', 'r') as f:
    OAUTHTK = f.read()


class GHMinerException(Exception):
    ''' Custom exception class to report unexpected response error codes. '''
    def __init__(self, url, err_code):
        self.url = url
        self.err_code = err_code

    def __str__(self):
        return '{} ({})'.format(self.url, self.err_code)


def _req(endpoint, retry_in=3):
    ''' Request wrapper. Returns dict representation of JSON response.
    Blocks and retries if request is not 200 or has hit the rate limit. '''
    url = 'https://api.github.com' + endpoint
    try:
        r = requests.get(url, headers={'Authorization':'token ' + OAUTHTK})
    except requests.ConnectionError:
        print('[-] Connection error, retrying in {}'.format(retry_in))
        sleep(retry_in)
        return _req(url)
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 403:
        wait_amt = int(int(r.headers['X-RateLimit-Reset']) - time()) + 3
        print('[-] Rate limit exceeded, sleeping for {} seconds'.format(wait_amt))
        sleep(wait_amt)
        return _req(url)
    else:
        raise GHMinerException(url, r.status_code)


def get_usernames(since_id):
    ''' Returns a list of 100 usernames starting from a since id.
    A KeyError will stop the program if GitHub changes their API such that
    account names are not contained under the key "login". '''
    data = _req('/users?per_page=100&since={}'.format(since_id))
    return [user['login'] for user in data]


def get_user(username):
    ''' Returns a dict containing an account's desired metadata. '''
    data = _req('/users/{}'.format(username))
    return {k: data.get(k, None) for k in KEEP}


@click.command()
@click.option('-l', '--limit', default=30*10**6,
    help='Program will stop upon reaching this specified account id number.')
def main(limit):
    print('[!] Connecting to database')
    conn = sqlite3.connect('ghaccounts.sqlite3', detect_types=sqlite3.PARSE_DECLTYPES)

    conn.execute('''
        CREATE TABLE IF NOT EXISTS accounts(
        id INTEGER PRIMARY KEY,
        login TEXT unique,
        type TEXT,
        name TEXT,
        company TEXT,
        blog TEXT,
        location TEXT,
        email TEXT,
        hireable INTEGER,
        public_repos INTEGER,
        followers INTEGER,
        following INTEGER,
        created_at DATE,
        updated_at DATE)
    ''')

    cursor = conn.execute('SELECT max(id) FROM accounts')
    start_id = cursor.fetchone()[0]
    if start_id is None:
        start_id = 0
    print('[!] Last entry in database is account id #{}'.format(start_id))
    print('[!] Program will extract metadata until id #{}'.format(limit))

    while start_id < limit:
        print('[!] Retrieving usernames after id #{}'.format(start_id))
        usernames = get_usernames(start_id)
        for i, name in enumerate(usernames, 1):
            # Some accounts exist in /users listings but their usernames are reserved keywords.
            # Example: https://api.github.com/users?since=41448 shows user "readme",
            #          but https://api.github.com/users/readme results in a 404.
            try:
                u = get_user(name)
            except GHMinerException as e:
                if e.err_code == 404:
                    print('[-] Skipped nonexistent account: {}'.format(e))
                    continue
                raise e

            if u['id'] >= limit:
                return

            conn.execute("INSERT INTO accounts({}) values ({})".format(
                ', '.join(KEEP), ', '.join(['?'] * len(KEEP))),
                [u[k] for k in KEEP]
            )
            conn.commit()

            print('[+] metadata saved for account id #{}'.format(u['id']))
            if i == len(usernames):
                start_id = u['id']

if __name__ == '__main__':
    main()
