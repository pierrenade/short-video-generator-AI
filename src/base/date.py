import logging
import arrow
import operator
from ofscraper.utils import settings  #
from ofscraper.filters.models.utils.logs import trace_log_user

log = logging.getLogger("shared")


def _apply_date_filter(
    items: list,
    setting_key: str,
    model_attr: str,
    op: callable,
    requires_arrow_parse: bool = False,
) -> list:
    """
    A helper function to apply a single date-based filter to a list of items.

    Args:
        items (list): The list of user objects to filter.
        setting_key (str): The key for the setting to retrieve.
        model_attr (str): The attribute on the user object to compare.
        op (callable): The comparison operator (e.g., operator.ge for >=).
        requires_arrow_parse (bool): Whether the model attribute needs parsing by arrow.

    Returns:
        list: The filtered list of user objects.
    """
    setting_value = getattr(settings.get_settings(), setting_key)
    if not setting_value:
        return items

    log.debug(f"{setting_key} filter: {setting_value}")

    # Convert the setting value to a float for comparison
    # If it's an Arrow object, use its float_timestamp, otherwise cast to float.
    comparison_value = (
        setting_value.float_timestamp
        if isinstance(setting_value, arrow.Arrow)
        else float(setting_value)
    )

    def filter_func(x):
        model_value = getattr(x, model_attr)
        if requires_arrow_parse:
            # If the model's date is a string, parse it with Arrow and get the float timestamp
            value_to_compare = arrow.get(model_value).float_timestamp
        else:
            # Otherwise, assume it's already a number (timestamp)
            value_to_compare = model_value
        return op(value_to_compare, comparison_value)

    filtered_list = list(filter(filter_func, items))
    log.debug(f"{setting_key} filter username count: {len(filtered_list)}")
    trace_log_user(filtered_list, setting_key)
    return filtered_list


def dateFilters(filterusername: list) -> list:
    """
    Applies a series of date-based filters to a list of users.
    Handles float and arrow type comparisons.

    Args:
        filterusername (list): The initial list of user objects.

    Returns:
        list: The final list of user objects after all filters have been applied.
    """
    # Define all filters in a data structure for a clean, data-driven approach
    filters_to_apply = [
        # (setting_key, model_attribute, operator, needs_arrow_parsing)
        ("last_seen_after", "final_last_seen", operator.ge, False),
        ("last_seen_before", "final_last_seen", operator.le, False),
        ("subscribed_after", "subscribed", operator.ge, True),
        ("subscribed_before", "subscribed", operator.le, True),
        ("expired_after", "expired", operator.ge, True),
        ("expired_before", "expired", operator.le, True),
    ]

    # Loop through and apply each filter sequentially
    for setting, model_key, op, parse in filters_to_apply:
        filterusername = _apply_date_filter(
            filterusername, setting, model_key, op, parse
        )

    return filterusername
