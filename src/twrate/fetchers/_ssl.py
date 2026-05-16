"""SSL helpers for bank endpoints with non-standard certificate chains."""

import ssl

import httpx


def create_bank_ssl_context() -> ssl.SSLContext:
    """Create an SSL context that keeps verification but relaxes OpenSSL strict mode.

    Some Taiwanese bank endpoints currently serve certificate chains that fail
    OpenSSL's strict RFC 5280 checks with ``Missing Subject Key Identifier``.
    Clearing ``VERIFY_X509_STRICT`` preserves CA and hostname verification while
    avoiding a full ``verify=False`` bypass.
    """
    context = httpx.create_ssl_context()
    strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)
    if strict_flag:
        context.verify_flags &= ~strict_flag
    return context
