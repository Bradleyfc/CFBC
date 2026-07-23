"""
Template tags for advanced fragment caching with versioning support.
Provides cache_fragment, cache_bust, and invalidate_cache_group tags.

Usage:
    {% load cache_fragment %}

    {% cache_fragment 300 "sidebar_categorias" group="categorias" %}
        ... fragment content ...
    {% endcache_fragment %}

    {# Cache bust for static files #}
    <link rel="stylesheet" href="{% static 'css/tailwind.css' %}{% cache_bust %}">

    {# Invalidate a cache group (admin/debug usage) #}
    {% invalidate_cache_group "noticias" %}
"""

from django import template
from django.core.cache import cache
from django.template.base import Node, TemplateSyntaxError, token_kwargs
from django.utils.safestring import SafeString
from cfbc.cache_utils import (
    FRAGMENT_CACHE_PREFIX,
    CacheVersion,
    generate_cache_key,
    invalidate_cache_pattern,
)
import hashlib
import time
import logging

logger = logging.getLogger(__name__)

register = template.Library()


# ─────────────────────────────────────────────────────────────────────────────
# Cache Fragment Tag — like Django's {% cache %} but with versioning
# ─────────────────────────────────────────────────────────────────────────────

class CacheFragmentNode(Node):
    """
    Template node that caches its rendered content with versioning support.

    Syntax:
        {% cache_fragment <timeout> <key> [group=<group>] [vary_on=<user|auth>] %}
            ... content to cache ...
        {% endcache_fragment %}

    Examples:
        {% cache_fragment 3600 "sidebar_categorias" group="categorias" %}
            ... sidebar with categories ...
        {% endcache_fragment %}

        {% cache_fragment 600 "user_menu" vary_on="auth" %}
            ... user menu ...
        {% endcache_fragment %}
    """

    def __init__(self, nodelist, timeout, fragment_key, group="general", vary_on=None):
        self.nodelist = nodelist
        self.timeout = timeout
        self.fragment_key = fragment_key
        self.group = group
        self.vary_on = vary_on

    def render(self, context):
        request = context.get("request")

        # Build the base cache key
        key_parts = [str(self.fragment_key)]

        # Add variation based on vary_on parameter
        if self.vary_on == "user" and request and request.user.is_authenticated:
            key_parts.append(f"user:{request.user.id}")
        elif self.vary_on == "auth" and request:
            key_parts.append(f"auth:{request.user.is_authenticated}")

        base_key = generate_cache_key(FRAGMENT_CACHE_PREFIX, *key_parts)

        # Apply versioning for group-based invalidation
        cache_key = CacheVersion.make_key(base_key, self.group)

        # Try to get from cache
        cached_content = cache.get(cache_key)
        if cached_content is not None:
            logger.debug(f"Fragment cache HIT: {cache_key}")
            return SafeString(cached_content)

        logger.debug(f"Fragment cache MISS: {cache_key}")

        # Render the content and cache it
        rendered = self.nodelist.render(context)
        cache.set(cache_key, rendered, self.timeout)
        return rendered


@register.tag
def cache_fragment(parser, token):
    """
    Template tag for caching template fragments with versioning.

    Usage:
        {% cache_fragment 3600 "unique_key" group="noticias" %}
            HTML to cache
        {% endcache_fragment %}
    """
    bits = token.split_contents()
    tag_name = bits[0]

    if len(bits) < 3:
        raise TemplateSyntaxError(
            f"'{tag_name}' tag requires at least 2 arguments: timeout and key"
        )

    # Parse timeout
    try:
        timeout = template.Variable(bits[1]).resolve({})
    except (template.VariableDoesNotExist, ValueError):
        try:
            timeout = int(bits[1])
        except (ValueError, TypeError):
            raise TemplateSyntaxError(
                f"'{tag_name}' tag's first argument must be a valid timeout (integer seconds)"
            )

    # Parse fragment key
    fragment_key = bits[2]

    # Parse keyword arguments (group, vary_on)
    group = "general"
    vary_on = None

    for bit in bits[3:]:
        try:
            kwarg = token_kwargs([bit], parser)
            if kwarg:
                for key, value in kwarg.items():
                    resolved = value.resolve({})
                    if key == "group":
                        group = resolved
                    elif key == "vary_on":
                        vary_on = resolved
        except Exception:
            pass

    nodelist = parser.parse(("endcache_fragment",))
    parser.delete_first_token()

    return CacheFragmentNode(nodelist, timeout, fragment_key, group, vary_on)


# ─────────────────────────────────────────────────────────────────────────────
# Cache Bust Filter — adds timestamp to static URLs
# ─────────────────────────────────────────────────────────────────────────────

@register.simple_tag
def cache_bust():
    """
    Returns a cache-busting query string based on current timestamp.
    Use with static files to force browser refreshes after deployment.

    Usage:
        <link rel="stylesheet" href="{% static 'css/tailwind.css' %}{% cache_bust %}">
    """
    return f"?v={int(time.time())}"


# ─────────────────────────────────────────────────────────────────────────────
# Invalidate Cache Group Tag — for admin/debug templates
# ─────────────────────────────────────────────────────────────────────────────

@register.simple_tag
def invalidate_cache_group(group):
    """
    Invalidate all cached content for a specific version group.

    Usage:
        {% invalidate_cache_group "noticias" %}
    """
    new_version = CacheVersion.increment(group)
    logger.info(f"Cache group '{group}' invalidated (v{new_version}) via template tag")
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Cache Stats Tag — for debug/status pages
# ─────────────────────────────────────────────────────────────────────────────

@register.simple_tag
def cache_stats():
    """
    Returns cache statistics as a JSON-like dict: hit ratio and version info.

    Usage in template:
        {% cache_stats as stats %}
        Hits: {{ stats.hits }}, Ratio: {{ stats.hit_ratio }}
    """
    from cfbc.cache_utils import CacheMetrics

    try:
        return CacheMetrics.get_stats()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "hits": 0,
            "misses": 0,
            "hit_ratio": 0,
            "versions": {},
            "error": str(e),
        }
