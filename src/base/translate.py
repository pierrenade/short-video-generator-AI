import logging

from ofscraper.filters.models.utils.logs import trace_log_user
import ofscraper.utils.settings as settings


def subType(filterusername):
    log = logging.getLogger("shared")
    log.debug(f"Renewal: {settings.get_settings().renewal}")
    if settings.get_settings().renewal:
        filterusername = list(filter(lambda x: x.renewed, filterusername))
        log.debug(f"active renewal filter username count: {len(filterusername)}")
        trace_log_user(filterusername, "active renewal filter")

    elif settings.get_settings().renewal is False:
        filterusername = list(filter(lambda x: not x.renewed, filterusername))
        log.debug(f"disabled renewal filter username counta: {len(filterusername)}")
        trace_log_user(filterusername, "disabled renewal filter")

    log.debug(f"Sub status: {settings.get_settings().sub_status}")
    if settings.get_settings().sub_status:
        filterusername = list(filter(lambda x: x.active, filterusername))
        log.debug(f"active subscription filter username count: {len(filterusername)}")
        trace_log_user(filterusername, "active subscription filter")

    elif settings.get_settings().sub_status is False:
        filterusername = list(filter(lambda x: not x.active, filterusername))
        log.debug(f"expired subscription filter username count: {len(filterusername)}")
        trace_log_user(filterusername, "expired subscription filter")

    return filterusername
