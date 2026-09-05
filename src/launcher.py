import asyncio
import argparse
from random import randint
from typing import Any
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions
from bot.utils.accounts import Accounts
from bot.core.TgManager.tg_manager import SessionManager


start_text = """

░██████╗░░█████╗░██████╗░██╗░░░░░██╗███╗░░██╗███╗░░░███╗██╗███╗░░██╗███████╗██████╗░░█████╗░████████╗
██╔════╝░██╔══██╗██╔══██╗██║░░░░░██║████╗░██║████╗░████║██║████╗░██║██╔════╝██╔══██╗██╔══██╗╚══██╔══╝
██║░░██╗░██║░░██║██████╦╝██║░░░░░██║██╔██╗██║██╔████╔██║██║██╔██╗██║█████╗░░██████╦╝██║░░██║░░░██║░░░
██║░░╚██╗██║░░██║██╔══██╗██║░░░░░██║██║╚████║██║╚██╔╝██║██║██║╚████║██╔══╝░░██╔══██╗██║░░██║░░░██║░░░
╚██████╔╝╚█████╔╝██████╦╝███████╗██║██║░╚███║██║░╚═╝░██║██║██║░╚███║███████╗██████╦╝╚█████╔╝░░░██║░░░
░╚═════╝░░╚════╝░╚═════╝░╚══════╝╚═╝╚═╝░░╚══╝╚═╝░░░░░╚═╝╚═╝╚═╝░░╚══╝╚══════╝╚═════╝░░╚════╝░░░░╚═╝░░░
                                                                                           by Desamod                                                              

Important! This is public version of bot. 
Information about Pro version with more features available in https://t.me/desforge_cryptwo channel

Select an action:

    1. Run bot
    2. Create session
"""


def get_proxy(raw_proxy: str) -> Proxy:
    return Proxy.from_str(proxy=raw_proxy).as_url if raw_proxy else None


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")
    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2"]:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break

    if action == 2:
        await register_sessions()
    elif action == 1:
        accounts = await Accounts().get_accounts()
        await run_tasks(accounts=accounts)


async def run_tasks(accounts: [Any, Any, list]):
    tasks = []
    manager = SessionManager(api_id=settings.API_ID,
                             api_hash=settings.API_HASH,
                             peer='GoblinMine_bot',
                             short_name='start',
                             start_param=settings.REF_ID,
                             check_first_run=True)

    for account in accounts:
        session_name, user_agent, raw_proxy = account.values()
        tg_session = await manager.get_tg_session(session_name=session_name, proxy=raw_proxy)
        proxy = get_proxy(raw_proxy=raw_proxy)
        tasks.append(asyncio.create_task(run_tapper(tg_session=tg_session, user_agent=user_agent, proxy=proxy)))
        await asyncio.sleep(delay=randint(settings.START_DELAY[0], settings.START_DELAY[1]))

    await asyncio.gather(*tasks)
