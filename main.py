import argparse
import asyncio
from datetime import datetime, timedelta
import logging
import platform

import aiohttp


PB_API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
CURRENCIES_LIST = ["EUR", "USD"]
HTTP_STATUS_OK = 200
MAX_DAYS = 10

parser = argparse.ArgumentParser(description="Exchange rate")
parser.add_argument(
    "days",
    type=int,
    help="Number of days up to 10.",
)
parser.add_argument(
    "currency",
    type=str,
    nargs="?",
    help="Currency: GBP, PLN, CHF",
)
args = vars(parser.parse_args())
days = args.get("days")
currency_add = args.get("currency")
if currency_add:
    CURRENCIES_LIST.append(currency_add)


def make_date_list(days: str):
    date_list = []
    if days > MAX_DAYS:
        days = MAX_DAYS
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
                if resp.status == HTTP_STATUS_OK:
                    r = await resp.json()
                    return r
                logging.error(f"Error status: {resp.status} for {url}")
                return None
        except aiohttp.ClientConnectorError as err:
            logging.error(f"Connection error: {str(err)}")
            return None


async def get_exchange():
    tasks = [
        asyncio.create_task(request(f"{PB_API_URL}{date}"))
        for date in make_date_list(days)
    ]
    feature = asyncio.gather(*tasks)
    result = await feature
    return result


def data_processing(data):
    if data:
        exchange_result = []
        for item in data:
            result = item.get("exchangeRate")
            for currency in CURRENCIES_LIST:
                try:
                    exchange, *_ = list(
                        filter(lambda el: el["currency"] == currency, result)
                    )
                    date_exc = f"{item.get('date')}"
                    sale_exc = f"{exchange['saleRate']}"
                    purchase_exc = f"{exchange['purchaseRate']}"
                    currency_rate = {
                        date_exc: {
                            currency: {"sale": sale_exc, "purchase": purchase_exc}
                        }
                    }
                    exchange_result.append(currency_rate)

                except (KeyError, ValueError) as e:
                    logging.error(f"{date_exc} Privatbank do not change {currency}.\n")

        return exchange_result

    logging.error(f"Failed to retrieve data")
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s: %(message)s")
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    result = asyncio.run(get_exchange())
    print(data_processing(result))
