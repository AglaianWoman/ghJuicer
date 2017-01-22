import requests

# The metadata keys we're interested in. See get_user().
__KEEP = ('login', 'id', 'type', 'name', 'company', 'blog',
    'location', 'email', 'hireable', 'public_repos', 'followers',
    'following', 'created_at', 'updated_at')

with open('oauthtk.txt', 'r') as f:
    __OAUTHTK = f.read()


def _req(url):
    '''Request wrapper. Returns dict representation of JSON response.
    Blocks and retries if request is not 200 or has hit the rate limit.'''
    r = requests.get(url, headers={'Authorization':'token ' + __OAUTHTK})
    if r.status_code == 200:
        # TODO handle rate limit
        return r.json()
    else:
        pass # TODO handle connectivity issues

def get_usernames(since_id):
    '''Returns a list of 100 usernames starting from a since id.'''
    data = _req('https://api.github.com/users?per_page=100&since=' +
        str(since_id))
    return [user.get('login', '') for user in data]

def get_user(username):
    '''Returns a dict containing an account's desired metadata.'''
    data = _req('https://api.github.com/users/' + username)
    return {k: data[k] for k in __KEEP}


def main():
    for u in get_usernames(0):
        print(get_user(u))

if __name__ == '__main__':
    main()