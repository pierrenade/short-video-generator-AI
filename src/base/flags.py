import logging

from ofscraper.filters.models.utils.logs import trace_log_user
import ofscraper.utils.settings as settings


def promoFilterHelper(filterusername):
    log = logging.getLogger("shared")

    log.debug(f"Promo flag: {settings.get_settings().promo}")
    if settings.get_settings().promo:
        filterusername = list(
            filter(lambda x: x.lowest_promo_claim is not None, filterusername)
        )
        log.debug(f"Promo flag yes username count: {len(filterusername)}")
        trace_log_user(filterusername, "promo flag yes")

    elif settings.get_settings().promo is False:
        filterusername = list(
            filter(lambda x: x.lowest_promo_claim is None, filterusername)
        )
        log.debug(f"Promo flag no username count: {len(filterusername)}")
        trace_log_user(filterusername, "promo flag no")

    log.debug(f"All promo flag: {settings.get_settings().all_promo}")
    if settings.get_settings().all_promo:
        filterusername = list(
            filter(lambda x: x.lowest_promo_all is not None, filterusername)
        )
        log.debug(f"All promo flag yes username count: {len(filterusername)}")
        trace_log_user(filterusername, "all promo flag yes")

    elif settings.get_settings().all_promo is False:
        filterusername = list(
            filter(lambda x: x.lowest_promo_all is None, filterusername)
        )
        log.debug(f"All promo flag no username count: {len(filterusername)}")
        trace_log_user(filterusername, "all promo flag no")

    log.debug(f"Last seen flag: {settings.get_settings().last_seen}")
    if settings.get_settings().last_seen:
        filterusername = list(filter(lambda x: x.last_seen is not None, filterusername))
        log.debug(f"Last seen flag yes username count: {len(filterusername)}")
        trace_log_user(filterusername, "last seen flag yes")

    elif settings.get_settings().last_seen is False:
        filterusername = list(filter(lambda x: x.last_seen is None, filterusername))
        log.debug(f"Last seen flag no username count: {len(filterusername)}")
        trace_log_user(filterusername, "last seen flag no")
    log.debug(f"Free trial flag: {settings.get_settings().free_trial}")

    if settings.get_settings().free_trial:
        filterusername = list(
            filter(
                lambda x: (
                    (x.final_current_price == 0 or x.final_promo_price == 0)
                    and x.final_regular_price > 0
                ),
                filterusername,
            )
        )
        log.debug(f"Free trial flag yes username count: {len(filterusername)}")
        trace_log_user(filterusername, "free trial flag yes")

    elif settings.get_settings().free_trial is False:
        filterusername = list(
            filter(
                lambda x: (x.final_current_price > 0 and x.final_promo_price > 0)
                or x.final_regular_price == 0,
                filterusername,
            )
        )
        log.debug(f"Free trial flag no username count: {len(filterusername)}")
        trace_log_user(filterusername, "free trial flag no")

    return filterusername
