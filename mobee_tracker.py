#!/usr/bin/env python3
__all__ = (
    'render_target_url',
    'get_current_rates',
)
import random as rand

from decimal import Decimal
from pprint import pprint
from time import sleep

import requests_html


TARGET_URL = 'https://hive.moneybees.ph/rates?ccy=php'
RETRY = 10
MIN_PAUSE = 0
MAX_PAUSE = 3

USER_AGENTS = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4464.5 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.7113.93 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
)


def default_validator(html):
    """Returns True if html contains valid data"""
    prices = [
        i.text or None
        for i in html.find('span[class*="font-rubik tracked"]')
    ]
    return all(prices)


def get_user_agent():
    """Return a random user agent"""
    return rand.choice(USER_AGENTS)


def render_target_url(
    url, ss=None, headers=None, is_js=False,
    validator=default_validator, retry=RETRY,
    min_pause=MIN_PAUSE, max_pause=MAX_PAUSE
):
    """Generate HTML object from the given URL"""
    ss = ss or requests_html.HTMLSession()
    _headers = {
        'User-Agent': get_user_agent(),
    }
    _headers.update(headers or {})

    def _exec():
        res = ss.get(url, headers=_headers)
        res.raise_for_status()
        if is_js:
            res.html.render()
        return res.html

    html = _exec()
    runs = 0
    while not validator(html) and runs < retry:
        html = _exec()
        runs += 1
        sleep(rand.randrange(min_pause, max_pause))

    if not validator(html):
        raise ValueError(f'Failed to find valid data after {retry} retries!')

    return html


def parse_name(cell):
    return cell[0].text.strip()


def parse_price(cell):
    return Decimal(cell[-1].text.replace(',', ''))


def get_current_rates(html):
    """Returns a list of all tracked currency rates"""
    # Columns: Coin name, Buy Price, Sell Price
    rates_table = html.find(
        'div#table-view>div>div>div[class*="flex-column"]')[0]
    rates_rows = rates_table.find('div.mb1px.justify-center')[1:]
    data = [{
        'name': parse_name(i.find(
            'div.flex.items-center > div > span:nth-child(1)')),
        'symbol': parse_name(i.find(
            'div.flex.items-center > div > span:nth-child(3)')),
        'buy_price': parse_price(i.find('div:nth-child(2)')),
        'sell_price': parse_price(i.find('div:nth-child(3)')),
    } for i in rates_rows]
    return data


def main():
    html = render_target_url(TARGET_URL, is_js=True)
    rates = get_current_rates(html)
    pprint(rates)


if __name__ == '__main__':
    main()
