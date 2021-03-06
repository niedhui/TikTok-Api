import asyncio
import pyppeteer
import random
import time
import string
import requests
import logging
from threading import Thread

# Import Detection From Stealth
from .stealth import stealth

from .get_acrawler import get_acrawler

async_support = False


def set_async():
    global async_support
    async_support = True


class browser:
    def __init__(
        self,
        url,
        language="en",
        proxy=None,
        find_redirect=False,
        api_url=None,
        debug=False,
        newParams=False,
        executablePath=None,
        custom_did=None,
    ):
        self.url = url
        self.debug = debug
        self.proxy = proxy
        self.api_url = api_url
        self.referrer = "https://www.tiktok.com/"
        self.language = language
        self.executablePath = executablePath
        self.did = custom_did

        self.userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
        self.args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certifcate-errors",
            "--ignore-certifcate-errors-spki-list",
            "--user-agent=" + self.userAgent,
        ]

        if proxy != None:
            if "@" in proxy:
                self.args.append(
                    "--proxy-server="
                    + proxy.split(":")[0]
                    + "://"
                    + proxy.split("://")[1].split(":")[1].split("@")[1]
                    + ":"
                    + proxy.split("://")[1].split(":")[2]
                )
            else:
                self.args.append("--proxy-server=" + proxy)
        self.options = {
            "args": self.args,
            "headless": True,
            "ignoreHTTPSErrors": True,
            "userDataDir": "./tmp",
            "handleSIGINT": False,
            "handleSIGTERM": False,
            "handleSIGHUP": False,
        }

        if self.executablePath != None:
            self.options["executablePath"] = self.executablePath

        if async_support:
            loop = asyncio.new_event_loop()
            t = Thread(target=self.__start_background_loop, args=(loop,), daemon=True)
            t.start()
            if find_redirect:
                fut = asyncio.run_coroutine_threadsafe(self.find_redirect(), loop)
            elif newParams:
                fut = asyncio.run_coroutine_threadsafe(self.newParams(), loop)
            else:
                fut = asyncio.run_coroutine_threadsafe(self.start(), loop)
            fut.result()
        else:
            try:
                self.loop = asyncio.new_event_loop()
                if find_redirect:
                    self.loop.run_until_complete(self.find_redirect())
                elif newParams:
                    self.loop.run_until_complete(self.newParams())
                else:
                    self.loop.run_until_complete(self.start())
            except:
                self.loop.close()

    def __start_background_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def newParams(self) -> None:
        self.browser = await pyppeteer.launch(self.options)
        self.page = await self.browser.newPage()
        await self.page.goto("about:blank")

        # self.browser_language = await self.page.evaluate("""() => { return navigator.language || navigator.userLanguage; }""")
        self.browser_language = ""
        # self.timezone_name = await self.page.evaluate("""() => { return Intl.DateTimeFormat().resolvedOptions().timeZone; }""")
        self.timezone_name = ""
        # self.browser_platform = await self.page.evaluate("""() => { return window.navigator.platform; }""")
        self.browser_platform = ""
        # self.browser_name = await self.page.evaluate("""() => { return window.navigator.appCodeName; }""")
        self.browser_name = ""
        # self.browser_version = await self.page.evaluate("""() => { return window.navigator.appVersion; }""")
        self.browser_version = ""

        self.width = await self.page.evaluate("""() => { return screen.width; }""")
        self.height = await self.page.evaluate("""() => { return screen.height; }""")

        await self.browser.close()
        self.browser.process.communicate()

        return 0

    async def start(self):
        self.browser = await pyppeteer.launch(self.options)
        self.page = await self.browser.newPage()

        await self.page.evaluateOnNewDocument(
            """() => {
    delete navigator.__proto__.webdriver;
        }"""
        )

        # Check for user:pass proxy
        if self.proxy != None:
            if "@" in self.proxy:
                await self.page.authenticate(
                    {
                        "username": self.proxy.split("://")[1].split(":")[0],
                        "password": self.proxy.split("://")[1]
                        .split(":")[1]
                        .split("@")[0],
                    }
                )

        await stealth(self.page)

        # might have to switch to a tiktok url if they improve security
        await self.page.goto("about:blank", {"waitUntil": "load"})

        self.userAgent = await self.page.evaluate(
            """() => {return navigator.userAgent; }"""
        )

        self.verifyFp = "".join(
            random.choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for i in range(16)
        )

        if self.did == None:
            self.did = str(random.randint(10000, 999999999))

        await self.page.evaluate("() => { " + get_acrawler() + " }")
        self.signature = await self.page.evaluate(
            '''() => {
        var url = "'''
            + self.url
            + "&verifyFp="
            + self.verifyFp
            + """&did="""
            + self.did
            + """"
        var token = window.byted_acrawler.sign({url: url});
        return token;
        }"""
        )

        if self.api_url != None:
            await self.page.goto(
                self.url
                + "&verifyFp="
                + self.verifyFp
                + "&_signature="
                + self.signature,
                {"waitUntil": "load"},
            )

            self.data = await self.page.content()
            # self.data = json.loads(self.data.replace("</pre></body></html>", "").replace(
            #    '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">', ""))

        await self.browser.close()
        self.browser.process.communicate()

    async def find_redirect(self):
        try:
            self.browser = await pyppeteer.launch(self.options)
            self.page = await self.browser.newPage()

            await self.page.evaluateOnNewDocument(
                """() => {
        delete navigator.__proto__.webdriver;
    }"""
            )

            # Check for user:pass proxy
            if self.proxy != None:
                if "@" in self.proxy:
                    await self.page.authenticate(
                        {
                            "username": self.proxy.split("://")[1].split(":")[0],
                            "password": self.proxy.split("://")[1]
                            .split(":")[1]
                            .split("@")[0],
                        }
                    )

            await stealth(self.page)

            # await self.page.emulate({'viewport': {
            #    'width': random.randint(320, 1920),
            #    'height': random.randint(320, 1920),
            #    'deviceScaleFactor': random.randint(1, 3),
            #    'isMobile': random.random() > 0.5,
            #    'hasTouch': random.random() > 0.5
            # }})

            # await self.page.setUserAgent(self.userAgent)

            await self.page.goto(self.url, {"waitUntil": "load"})

            self.redirect_url = self.page.url

            await self.browser.close()
            self.browser.process.communicate()

        except:
            await self.browser.close()
            self.browser.process.communicate()

    def __format_proxy(self, proxy):
        if proxy != None:
            return {"http": proxy, "https": proxy}
        else:
            return None

    def __get_js(self, proxy=None):
        return requests.get(
            "https://sf16-muse-va.ibytedtos.com/obj/rc-web-sdk-gcs/acrawler.js",
            proxies=self.__format_proxy(proxy),
        ).text
