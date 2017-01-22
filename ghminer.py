import requests
import sqlite3
from time import time, sleep

# The metadata keys we're interested in. See get_user().
__KEEP = ('login', 'id', 'type', 'name', 'company', 'blog',
    'location', 'email', 'hireable', 'public_repos', 'followers',
    'following', 'created_at', 'updated_at')

with open('oauthtk.txt', 'r') as f:
    __OAUTHTK = f.read()


def _req(url):
    '''Request wrapper. Returns dict representation of JSON response.
    Blocks and retries if request is not 200 or has hit the rate limit.'''
    try:
        r = requests.get(url, headers={'Authorization':'token ' + __OAUTHTK})
    except requests.ConnectionError:
        print('[-] Internet connection error, retrying in 3...')
        sleep(3)
        return _req(url)
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 403:
        wait_amt = int(int(r.headers['X-RateLimit-Reset']) - time()) + 3
        print('[-] Rate limit exceeded, sleeping for {} seconds ...'.format(wait_amt))
        sleep(wait_amt)
        return _req(url)
    else:
        raise Exception('FATAL: (strange request) {} [{}]'.format(r.url, r.status_code))

def get_usernames(since_id):
    '''Returns a list of 100 usernames starting from a since id.'''
    data = _req('https://api.github.com/users?per_page=100&since=' + str(since_id))
    return [user.get('login', '') for user in data]

def get_user(username):
    '''Returns a dict containing an account's desired metadata.'''
    data = _req('https://api.github.com/users/' + username)
    return {k: data.get(k, None) for k in __KEEP}


def main():
    print('Connecting to database')
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
    while start_id < 25*10**6:
        print('Retrieving usernames after id #{}'.format(start_id))
        usernames = get_usernames(start_id)
        for i, name in enumerate(usernames):
            u = get_user(name)
            conn.execute("INSERT INTO accounts({}) values ({})".format(
                ', '.join(__KEEP), ', '.join(['?']*len(__KEEP))),
                [u[k] for k in __KEEP])
            conn.commit()
            print('[+] metadata saved for account id #{}'.format(u['id']))
            if i == len(usernames) - 1:
                start_id = u['id']

if __name__ == '__main__':
    main()