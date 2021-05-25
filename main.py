from colorama import init, Fore
from threading import Thread, Lock
import requests
import json


go = False
sold = 0


class User:
    def __init__(self, u):
        self.tokens = u['tokens']
        self.name = u['name']
        self.id = u['_id']


def login(method, username, password):
    if method == 'google':
        return 'not supported yet', None
    else:
        response = requests.post('https://api.blooket.com/api/users/login', json={
            'name': username,
            'password': password
        }, headers=headers).json()

        if response['success']:
            return response['token'], User(response['user'])
        else:
            return response, None


# success, blook | error, new?
def open_box(box):
    response = requests.put('https://api.blooket.com/api/users/unlockblook', json={
        'box': box,
        'name': user.name
    }, headers=headers)

    try:
        response_json = response.json()

        user.tokens = response_json['tokens']

        return True, response_json['unlockedBlook'], response_json['isNewBlook']
    except:
        return False, response.text, False


def sell_blook(blook, amount=1):
    response = requests.put('https://api.blooket.com/api/users/sellblook', json={
        'blook': blook,
        'name': user.name,
        'numSold': amount
    }, headers=headers)

    try:
        return response.json(), True
    except:
        return response.text, False


def get_blooks():
    return requests.get(f'https://api.blooket.com/api/users/blooks?name={user.name}', headers=headers).json()


def sell_mt(blook=None, amount=1):
    global sold

    with lock:
        x = go

    while x is False:
        with lock:
            x = go

    data, success = sell_blook(blook, amount)

    if success:
        with lock:
            sold += 1


def buy_mt(box=None):
    with lock:
        x = go

    while x is False:
        with lock:
            x = go

    success, blook, new = open_box(box)

    if success:
        if new:
            with lock:
                print(f'{Fore.LIGHTYELLOW_EX}Unlocked new blook: {blook}; Tokens: {Fore.LIGHTRED_EX + str(user.tokens)}')


def sell_all(keep=1):
    global go, sold

    blooks = get_blooks()

    for blook in list(blooks.keys()):
        sold = 0
        go = False

        to_sell = blooks[blook] - keep
        threads = []

        if to_sell > 1:
            print(f'{Fore.LIGHTYELLOW_EX}Now selling {blook} in batches of {to_sell if keep != 0 else 1}.')

            for _ in range(1500):
                threads.append(Thread(target=sell_mt, kwargs={
                    'blook': blook,
                    'amount': to_sell if keep != 0 else 1
                }))

            for thread in threads:
                thread.start()

            go = True

            for thread in threads:
                thread.join()

            print(f'{Fore.LIGHTGREEN_EX}Sold {sold * to_sell if keep != 0 else 1} {blook}{"s" if sold != 1 and blook[-1] != "s" else ""}')


def buy(box, amount=500):
    global go

    threads = []

    print(f'{Fore.LIGHTYELLOW_EX}Now attempting to buy {amount} {box} Box{"es" if amount != 1 else ""}')

    for _ in range(amount):
        threads.append(Thread(target=buy_mt, kwargs={
            'box': box
        }))

    for thread in threads:
        thread.start()

    go = True

    for thread in threads:
        thread.join()


def daily_500():
    response = requests.put('https://api.blooket.com/api/users/addtokens', json={
        'addedTokens': 500,
        'name': user.name
    }, headers=headers).json()

    user.tokens = response['tokens']

    return print(f'{Fore.LIGHTGREEN_EX}Claimed daily 500 tokens; Tokens: {Fore.LIGHTRED_EX + str(user.tokens)}')


if __name__ == '__main__':
    init(autoreset=True)

    lock = Lock()

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0',
        'DNT': '1'
    }

    config = json.loads(open('config.json', 'r').read())

    token, user = login('email', config['email'], config['password'])

    headers['Authorization'] = token

    print(f'{Fore.LIGHTYELLOW_EX}Successfully logged in as {user.name} ({user.id}); Tokens: {Fore.LIGHTRED_EX + str(user.tokens)}')

    daily_500()

    while user.tokens < config['desired']:
        sell_all(0)
        buy('Space', 500)
