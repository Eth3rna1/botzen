"""
A module that offers an API with the ability to configure
each web action arbitrarily depending on the regarded action.

The API makes possible to:
    - Open a browser in headless mode or not
    - Click a button
    - Write into a text box
    - Screenshot the DOM
    - Find an element via css, id, class, text, or xpath
    - Redirect the page
"""

from typing import Literal
from playwright.sync_api import Locator
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


By = Literal["xpath", "css", "id", "class", "text"]


class Web:
    """
    An API with the necessary abstraction
    to allow webscraping and interaction
    with a websites DOM.
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self.headless = False

    def enable_headless(self):
        self.headless = True

    def start(self):
        """
        Initiates all the necessary variables
        and opens the browser
        """
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.response = self.page.goto(self.url)

    def redirect(self, url):
        """
        Changes the website
        """
        self.url = url
        self.response = self.page.goto(self.url)

    def find(self, selector: str, by: By) -> Locator:
        """
        Given a selector and selector type, the function
        will attempt to find the element and return if it does
        amount of times.

        :param str       selector: The name of the element or expression
        :param Literal[...]    by: Specifies whether the query is selecting an:
            - "id"
            - "css"
            - "class"
            - "xpath"
        """
        match by:
            case "css":
                return self.page.locator(selector)
            case "id":
                return self.page.locator(f"#{selector}")
            case "class":
                return self.page.locator(f".{selector}")
            case "xpath":
                return self.page.locator(f"xpath={selector}")
            case "text":
                return self.page.locator(f"text={selector}")
            case _:
                raise ValueError(f"`{by}` is unsupported")

    def exists(self, selector: str, by: By) -> bool:
        """
        Given a selector and selector type, the function
        will attempt to find the element and return True if
        it does, otherwise, False.

        :param str       selector: The name of the element or expression
        :param Literal[...]    by: Specifies whether the query is selecting an:
            - "id"
            - "css"
            - "class"
            - "xpath"
        """
        loc: Locator = self.find(selector, by)
        return loc.count() > 0 and loc.first.is_visible()

    def wait_for(
        self,
        selector: str,
        by: By,
        timeout_ms: int = 5000,  # 5 seconds
        state: Literal[
            "attached",
            "detached",
            "visible",
            "hidden",
        ] = "visible",
    ) -> bool:
        """
        Given a selector and selector type, the function
        will attempt to find the element and click it a specified
        amount of times.

        :param str       selector: The name of the element or expression
        :param Literal[...]    by: Specifies whether the query is selecting an:
            - "id"
            - "css"
            - "class"
            - "xpath"
        :param str     timeout_ms: Wanted milliseconds to wait (DEFAULT = 5,000)
        :param Literal[...] state: Specifies in what state can the element ultimately
            be found in (DEFAULT = "visible"). All states include:
            - "attached"
            - "detached"
            - "visible"
            - "hidden"
        """
        try:
            self.find(selector, by).wait_for(state=state, timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            return False

    def click_and_wait_for_navigation(
        self, selector: str, by: By, timeout_ms: int = 10000
    ):
        """
        Given a selector and selector type, the function
        will attempt to find the element, click it, and wait
        for redirection.

        :param str    selector: The name of the element or expression
        :param Literal[...] by: Specifies whether the query is selecting an:
            - "id"
            - "css"
            - "class"
            - "xpath"
        :param str  timeout_ms: Wanted milliseconds to wait (DEFAULT = 10,000)
        """
        with self.page.expect_navigation(timeout=timeout_ms):
            self.find(selector, by).click()

    def fill(self, selector: str, by: By, text: str):
        """
        Given a selector and selector type, the function
        will attempt to find the element and write the specified
        text into it.

        :param str    selector: The name of the element or expression
        :param Literal[...] by: Specifies whether the query is selecting an:
            - "id"
            - "css"
            - "class"
            - "xpath"
        :param str        text: The wanted text to write into such element
        """
        self.find(selector, by).fill(text)

    def click(self, selector: str, by: By, amount: int = 1):
        """
        Given a selector and selector type, the function
        will attempt to find the element and click it a specified
        amount of times.

        :param str    selector: The name of the element or expression
        :param Literal[...] by: Specifies whether the query is selecting an:
            - "id"
            - "css"
            - "class"
            - "xpath"
        :param int      amount: Amount of times to click (DEFAULT = 1)
        """
        for _ in range(amount):
            self.find(selector, by).click()

    def screenshot(self, path_to_save: str):
        """
        Screenshots the current state of the page
        regardless if it's in headless mode by using
        a virtual framebuffer.

        :param str path_to_save: The path to save the screenshot in
        """
        self.page.screenshot(path=path_to_save)

    def current_url(self):
        """
        Returns the current page URL
        """
        return self.page.url

    def content(self):
        """
        Returns the pages HTML content
        """
        return self.page.content()

    def headers(self):
        """
        Returns the response headers, if any.
        """
        return self.response.headers if self.response else {}

    def close(self):
        """
        Terminates `Web` gracefully
        """
        self.page.close()
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    def __enter__(self):
        """
        Allows to use `Web` with the `with` keyword
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Allows to use `Web` with the `with` keyword.
        The specified parameters are used consider
        certain exceptions.
        """
        self.close()
