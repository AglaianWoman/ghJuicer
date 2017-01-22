# Mini/ugly version of ghminer, just for kicks
# Python can scrape metadata on all github accounts in just 36 LoC, neat huh?

import requests, sqlite3, time
__KEEP = ('login', 'id', 'type', 'name', 'company', 'blog', 'location', 'email', 'hireable', 'public_repos', 'followers', 'following', 'created_at', 'updated_at')
with open('oauthtk.txt', 'r') as f:
    __OAUTHTK = f.read()
def _req(url):
    try:
        r = requests.get(url, headers={'Authorization':'token ' + __OAUTHTK})
    except requests.ConnectionError:
        time.sleep(1)
        return _req(url)
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 403:
        wait_amt = int(r.headers['X-RateLimit-Reset']) - time.time()
        time.sleep(int(wait_amt + 3))
        return _req(url)
    else:
        raise Exception('Strange request: {} [{}]'.format(r.url, r.status_code))
def get_usernames(since_id):
    return [user.get('login', '') for user in _req('https://api.github.com/users?per_page=100&since=' + str(since_id))]
def get_user(username):
    data = _req('https://api.github.com/users/' + username)
    return {k: data[k] for k in __KEEP}
conn = sqlite3.connect('ghaccounts.sqlite3', detect_types=sqlite3.PARSE_DECLTYPES)
conn.execute("CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY, login TEXT unique, type TEXT, name TEXT, company TEXT, blog TEXT, location TEXT, email TEXT, hireable INTEGER, public_repos INTEGER, followers INTEGER, following INTEGER, created_at DATE, updated_at DATE)")
cursor = conn.execute('SELECT max(id) FROM accounts')
start_id = cursor.fetchone()[0]
while start_id < 25*10**6:
    usernames = get_usernames(start_id)
    for i, name in enumerate(usernames):
        u = get_user(name)
        conn.execute("INSERT INTO accounts({}) values ({})".format(', '.join(__KEEP), ', '.join(['?']*len(__KEEP))), [u[k] for k in __KEEP])
        conn.commit()
        print('done uid', u['id'])
        if i == len(usernames) - 1:
            start_id = u['id']
