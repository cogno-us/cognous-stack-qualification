"""Destination-only comparator wiring (decision D1, option A).

Corner (19) and baseline (24): the registered OPA application `Conventional` is
reused unchanged (pinned adapters.py); nothing is rebuilt. Wiki subset: the
Wiki OPA application. The profile id is the registered one in both cases, so
one plan schema addresses both. OCS appears only as the registered
`Cognous` protected-destination configuration; there is no mixed scoring and
no OCS code here.
"""
from . import _base
from ..apps.wiki_config import PROFILE_ID


def registered_adapters():
    a = _base.pinned_adapters()
    return {'cognous-protected-destination': a.Cognous, 'opa-transactional-application': a.Conventional,
            'langgraph-opa-transactional-application': a.LangGraphOPA}


def wiki_adapters_opa_only():
    """Mapping to install as the runner's ADAPTERS for Wiki scenarios, OPA application only.
    The OCS destination and the graph application are supplied by other work packages."""
    from ..apps.wiki_opa_app import WikiOpaApp
    return {PROFILE_ID: WikiOpaApp}


def wiki_adapters_langgraph():
    """Mapping to install as the runner's ADAPTERS for Wiki scenarios, LangGraph graph over the Wiki OPA
    application only (registered profile id of the graph configuration; scoring interface unchanged)."""
    from ..apps.wiki_langgraph_app import WikiLangGraphOPA, PROFILE_ID as GRAPH_PROFILE_ID
    return {GRAPH_PROFILE_ID: WikiLangGraphOPA}
