import argparse
import asyncio
from datetime import datetime, timedelta
import logging
import platform

import aiohttp


parser = argparse.ArgumentParser(description="Exchange rate")
parser.add_argument("days", type=int, help="Number of days up to 10")
parser.add_argument(
    "--currency",
    "-c",
    default="EUR",
    help="Currency: EUR, USD, GBP, PLN, CHF",
)
args = vars(parser.parse_args())
days = args.get("days")
currency = args.get("currency")

from datetime import datetime, timedelta


def make_date_list(days: str):
    date_list = []
    date_now = datetime.now().date()
    day_delta = timedelta(days=1)
    count = 1
    while count <= int(days):
        count += 1
        date_list.append(date_now.strftime("%d.%m.%Y"))
        date_now -= timedelta(days=1)
    return date_list


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    r = await resp.json()
                    return r
                logging.error(f"Error status: {resp.status} for {url}")
                return None
        except aiohttp.ClientConnectorError as err:
            logging.error(f"Connection error: {str(err)}")
            return None


async def get_exchange():
    result = await request(
        f"https://api.privatbank.ua/p24api/exchange_rates?json&date={datetime.now().date().strftime('%d.%m.%Y')}"
    )
    if result:
        result = result.get("exchangeRate")
        print(make_date_list(days))

        # try:
        exchange, *_ = list(filter(lambda el: el["currency"] == currency, result))
        date_exc = f"{datetime.now().date().strftime('%d.%m.%Y')}"
        sale_exc = f"{exchange['saleRate']}"
        purchase_exc = f"{exchange['purchaseRate']}"
        currency_rate = {
            date_exc: {currency: {"sale": sale_exc, "purchase": purchase_exc}}
        }

        # currency_rate = f"{currency}: buy: {exchange['purchaseRate']}, sale: {exchange['saleRate']}. Date: {datetime.now().date().strftime('%d.%m.%Y')}"
        return currency_rate

        # except (KeyError, ValueError) as e:
        #     return f"{datetime.now().date().strftime('%d.%m.%Y')} Privatbank do not change {currency}.\n"
    return "Failed to retrieve data"


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    result = asyncio.run(get_exchange())
    print(result)
