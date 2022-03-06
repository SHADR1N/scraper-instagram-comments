from time import sleep, time
import asyncio
from pyppeteer import launch
import os
import pickle
import unicodecsv
import json 
import gc
import urllib.parse
from pyppeteer_stealth import stealth
import random
from config import delay_itter, delay_requests, count_itter


class insta_request():
    def __init__(self, post_link, login, password, count_itter, delay_itter, delay_requests, headless = False, proxy = None, debug = True):
        self.page = False
        self.browser = False
        self.debug = debug
        self.login = login
        self.proxy = proxy
        self.password = password
        self.headless = headless
        self.post_link = post_link
        self.users_data = []
        self.type = 'one'
        self.delay = 15000
        self.count = 0
        self.count_itter = count_itter
        self.delay_itter = delay_itter
        self.delay_requests = delay_requests

        with open(f'log_{self.login}.txt', 'w') as f: 
            pass
                
        asyncio.run(self.get_browser())
        
    async def intercept(self, request):

        if 'https://www.instagram.com/graphql/query/?query_hash=' not in str(request.url) and any(request.resourceType == _ for _ in ('fetch', 'xhr')):
            await request.abort()

        elif any(request.resourceType == _ for _ in ('image', 'font', 'fetch', 'other')):
            await request.abort()

        else:
            await request.continue_()

    async def get_browser(self, proxy = False):
        if not proxy and not self.proxy:
            self.browser = await launch({
                'defaultViewport': {'width': 1200, 'height': 800},
                'slowMo': 1,
                'args': [
                '--disable-setuid-sandbox',
                "--fast-start", 
                '--incognito',
                '--disable-infobars',
                '--window-size=1200,800',
                ],
                'headless': self.headless,
                'ignoreDefaultArgs': ["--enable-automation"],
                "ignoreHTTPSErrors": True
                })


            self.page = await self.browser.pages()
            self.page = self.page[0]
            await self.page.setCacheEnabled(False)

            #await self.page.setRequestInterception(True)
            #self.page.on('request', lambda req: asyncio.ensure_future(self.intercept(req)))

            await self.page.evaluateOnNewDocument('navigator.mediaDevices.getUserMedia = navigator.webkitGetUserMedia = navigator.mozGetUserMedia = navigator.getUserMedia = webkitRTCPeerConnection = RTCPeerConnection = MediaStreamTrack = undefined')
            await stealth(self.page)

            if not os.path.exists(path = f"{self.login}.pkl"):
                await self.sign_in()
            else:
                await self.page.goto(self.post_link)
                await self.page.waitFor(3000)
                self.cookies = pickle.load(open(f"{self.login}.pkl", "rb"))
                for cookie in self.cookies:
                    await self.page.setCookie(cookie)

            await self.get_commentr()
            return


        elif self.proxy:
            proxy = self.proxy.split(':')

            login = proxy[2]
            password = proxy[3]
            ip = proxy[0]
            port = proxy[1]

            self.browser = await launch({
                'defaultViewport': {'width': 1200, 'height': 800},
                'slowMo': 1,
                'args': [
                "--fast-start", 
                '--start-maximized',
                '--disable-infobars',
                '--incognito',
                '--window-size=1200,800',
                f'--proxy-server={ip}:{port}',
                ],
                'headless': self.headless,
                'ignoreDefaultArgs': ["--enable-automation"],
                "ignoreHTTPSErrors": True
                })


            page = await self.browser.pages()
            self.page = page[0]

            await self.page.evaluateOnNewDocument('navigator.mediaDevices.getUserMedia = navigator.webkitGetUserMedia = navigator.mozGetUserMedia = navigator.getUserMedia = webkitRTCPeerConnection = RTCPeerConnection = MediaStreamTrack = undefined')
            await self.page.authenticate({'username': login, 'password': password})
            await stealth(self.page)

            if not os.path.exists(path = f"{self.login}.pkl"):
                await self.sign_in()
            else:
                await self.page.goto(self.post_link)
                await self.page.waitFor(3000)
                self.cookies = pickle.load(open(f"{self.login}.pkl", "rb"))
                for cookie in self.cookies:
                    await self.page.setCookie(cookie)

             
            await self.get_commentr()
            return



    async def sign_in(self):
        await self.page.goto('https://www.instagram.com/accounts/login/')
        await self.page.waitForSelector("#loginForm")

        username_input = await self.page.type("input[name='username']", self.login)
        password_input = await self.page.type("input[name='password']", self.password)
        login_button = await self.page.click("button[type='submit']")
        await self.page.waitFor(4000)
        pickle.dump( await self.page.cookies(), open(f"{self.login}.pkl","wb"))
        return

    async def save_csv(self):
        try:
            if self.users_data != []:
                with open(f"{self.post_link.split('p/')[1].split('/')[0].strip()}.csv", 'wb') as cv:
                    writer = unicodecsv.writer(cv, encoding = 'utf-8-sig', delimiter=';')
                    writer.writerows(self.users_data)

                cv.close()
                if self.debug: print('Saved file csv')
        except Exception as error: return print(error)

    async def get_json(self, url):
        while True:
            try:
                await self.page.goto(str(url))
                await self.page.waitFor(self.delay_requests * 1000)
                html = await self.page.J('td[class="line-content"]')
                html = await self.page.evaluate('(html) => html.innerText',html)
                json_html = json.loads(html)
                break
            except: pass
        return json_html

    async def get_url(self):
        if self.type == 'two':
            qh = 'view-source:https://www.instagram.com/graphql/query/?query_hash=bc3296d1ce80a24b1b6e40b1e72903f5'
            url = "{}&variables={}".format(qh, f"%7B%22shortcode%22%3A%22{self.post_link.split('p/')[1].split('/')[0].strip()}%22%2C%22first%22%3A20%2C%22after%22%3A%22%7B%5C%22cached_comments_cursor%5C%22%3A+%5C%22{self.after[0]}%5C%22%2C+%5C%22bifilter_token%5C%22%3A+%5C%22{self.after[1]}%3D%3D%5C%22%7D%22%7D")
        
        elif self.type == 'one':
            key = str(urllib.parse.quote(self.after, safe = ''))
            if key[:3] != '%22' and key[:-3] != '%22':
                key = '%22' + key + '%22'

            qh = 'view-source:https://www.instagram.com/graphql/query/?query_hash=bc3296d1ce80a24b1b6e40b1e72903f5'
            url = "{}&variables={}".format(qh, f"%7B%22shortcode%22%3A%22{self.post_link.split('p/')[1].split('/')[0].strip()}%22%2C%22first%22%3A20%2C%22after%22%3A{key}%7D")
            

        elif self.type == 'three': 
            key = str(urllib.parse.quote(self.after[0], safe = ''))

            tao = str(urllib.parse.quote(self.after[1], safe = ''))

            qh = 'view-source:https://www.instagram.com/graphql/query/?query_hash=bc3296d1ce80a24b1b6e40b1e72903f5'
            url = "{}&variables={}".format(qh, f"%7B%22shortcode%22%3A%22{self.post_link.split('p/')[1].split('/')[0].strip()}%22%2C%22first%22%3A20%2C%22after%22%3A%22%7B%5C%22bifilter_token%5C%22%3A+%5C%22{key}%5C%22%2C+%5C%22tao_cursor%5C%22%3A+%5C%22{tao}%5C%22%7D%22%7D")
        
        elif self.type == 'five':
            key = str(urllib.parse.quote(self.after, safe = ''))

            qh = 'view-source:https://www.instagram.com/graphql/query/?query_hash=bc3296d1ce80a24b1b6e40b1e72903f5'
            url = "{}&variables={}".format(qh, f"%7B%22shortcode%22%3A%22{self.post_link.split('p/')[1].split('/')[0].strip()}%22%2C%22first%22%3A20%2C%22after%22%3A%22%7B%5C%22bifilter_token%5C%22%3A+%5C%22{key}%5C%22%7D%22%7D")
        
        elif self.type == 'four':
            url = False
            await self.save_csv()

        return url

    async def find_after(self):
        self.after = self.after['shortcode_media']['edge_media_to_parent_comment']['page_info']['end_cursor']

        if str(self.after) == 'null':
            self.after = []
            self.type = 'four'

        elif 'cached_comments_cursor' in self.after:
            self.cached_comments_cursor = self.after.split('"cached_comments_cursor": "')[1].split('", "bifilter_token":')[0].strip()
            bifilter_token = self.after.split('"bifilter_token": "')[1].split('"')[0].strip()
            self.after = [self.cached_comments_cursor, urllib.parse.quote(bifilter_token, safe = '')]
            self.type = 'two'

        elif 'tao_cursor' in self.after and 'bifilter_token' in self.after:
            bifilter_token = self.after.split('"bifilter_token": "')[1].split('"')[0].strip()
            tao_cursor = self.after.split('"tao_cursor": "')[1].split('"')[0].strip()
            self.after =  [bifilter_token, tao_cursor]
            self.type = 'three'
            
        elif 'cached_comments_cursor' not in self.after and 'bifilter_token' not in self.after:
            self.type = 'one'

        elif 'bifilter_token' in self.after and 'cached_comments_cursor' not in self.after and 'tao_cursor' not in self.after:
            bifilter_token = self.after.split('"bifilter_token": "')[1].split('"')[0].strip()
            self.after = bifilter_token
            self.type = 'five'

        else: 
            self.type = 'four'

        return

    async def get_commentr(self):
        self.start = time()
        await self.page.goto(self.post_link+'comments/')
        await self.page.waitFor(self.delay_requests * 1000)
            
        js = await self.page.JJ('script[type="text/javascript"]')
        for js in js:
            js = await self.page.evaluate('(js) => js.outerHTML',js)
            if '"end_cursor":"' in str(js):
                self.after = str(js).split('"end_cursor":')[1].split('},"edges"')[0].replace('"{\\', '').replace('}"', '').replace('\\"', '"').strip()
                
                if str(self.after) == 'null':
                    self.after = []
                    self.type = 'four'

                elif 'cached_comments_cursor' in self.after:
                    self.cached_comments_cursor = self.after.split('"cached_comments_cursor": "')[1].split('", "bifilter_token":')[0].strip()
                    bifilter_token = self.after.split('"bifilter_token": "')[1].split('"')[0].strip()
                    self.after = [self.cached_comments_cursor, urllib.parse.quote(bifilter_token, safe = '')]
                    self.type = 'two'

                elif 'tao_cursor' in self.after and 'bifilter_token' in self.after:
                    bifilter_token = self.after.split('"bifilter_token": "')[1].split('"')[0].strip()
                    tao_cursor = self.after.split('"tao_cursor": "')[1].split('"')[0].strip()
                    self.after =  [bifilter_token, tao_cursor]
                    self.type = 'three'
                    
                elif 'cached_comments_cursor' not in self.after and 'bifilter_token' not in self.after:
                    self.type = 'one'

                elif 'bifilter_token' in self.after and 'cached_comments_cursor' not in self.after and 'tao_cursor' not in self.after:
                    bifilter_token = self.after.split('"bifilter_token": "')[1].split('"')[0].strip()
                    self.after = bifilter_token
                    self.type = 'five'

                else: 
                    self.type = 'four'

                break

        _count_itter = 0
        while True: 
            url = await self.get_url()

            if not url: 
                break
            json_html = await self.get_json(url)
            if 'message' in json_html or 'spam' in json_html:
                await self.save_csv()
                break

            self.after = json_html['data']
            with open('log.txt', 'w', encoding = 'utf-8') as f:
                f.write(str(self.after))

            if 'shortcode_media' not in self.after:
                await self.save_csv()
                if self.debug: print('Not found "end_cursor"')
                break
            else: 
                try:
                    await self.find_after()
                except Exception as er: self.type = 'four'

            users = json_html['data']['shortcode_media']['edge_media_to_parent_comment']['edges']
            count = json_html['data']['shortcode_media']['edge_media_to_parent_comment']['count']
            for user in users:
                data = user['node']
                id = data['id']
                username = data['owner']['username']
                text = data['text']
                if [id.replace('﻿', ''), username, text] not in self.users_data:
                    self.users_data.append([id.replace('﻿', ''), username, text])


            if len(self.users_data) - self.count >= 1000:
                await self.save_csv()
                self.count = len(self.users_data)


            with open(f'log_{self.login}.txt', 'a') as f: 
                f.write(f'{len(self.users_data)} = worked time { round((time() - self.start) / 60, 2) } min.\n')

            if self.debug: print(f'{len(self.users_data)} = worked time { round((time() - self.start) / 60, 2) } min.')
            if self.type == 'four':
                if self.debug: print('Scrapp completed.')
                break
            else:
                await self.page.waitFor(self.delay_requests * 1000)

            _count_itter += 1
            if _count_itter >= self.count_itter:
                _count_itter = 0
                await self.save_csv()
                await self.page.waitFor(self.delay_itter * 1000)

        await self.save_csv()
        await self.end()
        return

    async def end(self):
        await self.browser.close()
        return


if  __name__ == '__main__':
    with open('accounts.txt', 'r') as f:
        row = f.read().split('\n')[0] 

    data = row.split('#')
    login = data[0]
    password = data[1]

    with open('post_links.txt', 'r') as f:
        post_link = f.read().split('\n')[0] 


    with open('proxy.txt', 'r') as f:
        proxys = f.read().split('\n')
    

    proxys = [i for i in proxys if i != '']
    if len(proxys) == 0:
        proxy = False
    else:
        proxy = random.choice(proxys)
    

    api = insta_request(login = login,
                        password = password, 
                        post_link = post_link,
                        headless = False,
                        debug = True,
                        proxy = proxy,
                        count_itter = count_itter,
                        delay_itter = delay_itter,
                        delay_requests = delay_requests)
 
