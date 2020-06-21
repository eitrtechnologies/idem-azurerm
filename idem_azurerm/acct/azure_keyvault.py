# -*- coding: utf-8 -*-
"""
Azure Key Vault Backend for Acct

.. versionadded:: 2.4.0

:configuration: Get secrets from Azure Key Vault.

    Example:

    .. code-block:: yaml

        acct-backend:
            azure_keyvault: {}

"""

# Python libs
from typing import Dict


def unlock(
    hub, designator: str = "acct-provider-", **kwargs
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    .. versionadded:: SOMEVERSIONHERE

    Get secrets from the Azure Key Vault.

    Example:

    .. code-block:: yaml

        acct-backend:
            azure_keyvault: {}

    """
    ret = {}

    # secrets = hub.exec.azurerm.keyvault.
    # ret[provider] = {}
    # ret[provider][profile] = {}
    # ret[provider][profile][name] = secret

    return ret
