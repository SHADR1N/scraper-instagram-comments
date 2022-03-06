from instabot import insta_request
from multiprocessing import * 
import os 
from time import time
from config import delay_itter, delay_requests, count_itter
import random

def main(info):
    accounts, queue = info
    if accounts == '':
        return

    data = accounts.split('#')
    login = data[0]
    password = data[1]

    post_link = queue.get()
    if post_link == '':
        return
    try:
        start = time()
        with open('proxy.txt', 'r') as f:
            proxys = f.read().split('\n')
        

        proxys = [i for i in proxys if i != '']
        if len(proxys) == 0:
            proxy = False
        else:
            proxy = random.choice(proxys)

        session = insta_request(login = login, 
                        password = password, 
                        proxy = proxy, 
                        post_link = post_link, 
                        debug = False, 
                        headless = False,
                        count_itter = count_itter,
                        delay_itter = delay_itter,
                        delay_requests = delay_requests)
        
        print(f'Time worked {round((time() - start) / 60, 2)} min. to account {login}')
    except Exception as error: print(f'[{login}]', error)

    return


if  __name__ == '__main__':
    if not os.path.exists(path = 'accounts.txt'): 
        with open('accounts.txt', 'w') as f: 
            pass
    if not os.path.exists(path = 'post_links.txt'): 
        with open('post_links.txt', 'w') as f: 
            pass
    
    with open('accounts.txt', 'r') as f:
        _accounts = f.read().split('\n')
        _accounts = [i for i in _accounts if i != '']

    with open('post_links.txt', 'r') as f:
        post_links = f.read().split('\n')
        post_links = [i for i in post_links if i != '']


    queue = Manager().Queue(maxsize=len(_accounts))
    process = [Process(target = main, args = ([i, queue],)) for i in _accounts]

    for proc in process:
        proc.start()

    for task in post_links:
        queue.put(task)
            
    for proc in process:
        proc.join()

