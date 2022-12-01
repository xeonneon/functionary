from collections.abc import Iterable

from django import template
from django.core.paginator import Paginator

register = template.Library()


@register.simple_tag
def get_updated_elided_page_range(
    paginator: Paginator, number: int, on_each_side: int = 3, on_ends: int = 2
) -> Iterable:
    """Get an updated list of elided pages based on the passed in page number

    Gets a new list of pages, including the ellipsis, in the pagination navbar whenever
    the user goes to a new page.

    Args:
        paginator: The Paginator for the paginated view
        number: An integer of the current page number
        on_each_side: An integer for how many pages should be displayed
            on both sides of the current page
        on_ends: An integer for how many pages should be displayed
            on the end of the page list, past the ellipsis

    Returns:
        new_paginator: An iterable of the new list of elided pages
    """
    new_paginator = Paginator(paginator.object_list, paginator.per_page)
    return new_paginator.get_elided_page_range(
        number=number, on_each_side=on_each_side, on_ends=on_ends
    )
