# -*- coding: utf-8 -*-
"""
Azure Key Vault Backend for Acct

:configuration: Get secrets from Azure Key Vault.

    Example:

    .. code-block:: yaml

        acct-backend:
            azure_keyvault: {}

"""

# Python libs
from typing import Dict
import logging


# Azure libs
HAS_LIBS = False
try:

    from azure.core.exceptions import (
        ResourceNotFoundError,
        HttpResponseError,
        ResourceExistsError,
    )
    from azure.identity import (
        DefaultAzureCredential,
        KnownAuthorities,
    )
    from azure.keyvault.secrets import SecretClient
    from msrest.exceptions import SerializationError

    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)


def __virtual__(hub):
    """
    Only load when Azure SDK imports successfully.
    """
    return HAS_LIBS


def _get_identity_credentials(ctx, **kwargs):
    """
    Acquire Azure RM Credentials from the identity provider

    We basically set environment variables based upon incoming parameters and then pass off to
    the DefaultAzureCredential object to correctly parse those environment variables. See the
    `Microsoft Docs on EnvironmentCredential <https://aka.ms/azsdk-python-identity-default-cred-ref>`_
    for more information.
    """
    if ctx["acct"]:
        for key, val in ctx["acct"].items():
            # explicit kwargs override acct
            kwargs.setdefault(key, val)

    kwarg_map = {
        "tenant": "AZURE_TENANT_ID",
        "client_id": "AZURE_CLIENT_ID",
        "secret": "AZURE_CLIENT_SECRET",
        "client_certificate_path": "AZURE_CLIENT_CERTIFICATE_PATH",
        "username": "AZURE_USERNAME",
        "password": "AZURE_PASSWORD",
    }

    for kw in kwarg_map:
        if kwargs.get(kw):
            os.environ[kwarg_map[kw]] = kwargs[kw]

    try:
        if kwargs.get("cloud_environment") and kwargs.get(
            "cloud_environment"
        ).startswith("http"):
            authority = kwargs["cloud_environment"]
        else:
            authority = getattr(
                KnownAuthorities, kwargs.get("cloud_environment", "AZURE_PUBLIC_CLOUD")
            )
        log.debug("AUTHORITY: %s", authority)
    except AttributeError as exc:
        log.error('Unknown authority presented for "cloud_environment": %s', exc)
        authority = KnownAuthorities.AZURE_PUBLIC_CLOUD

    credential = DefaultAzureCredential(authority=authority)

    return credential


def _get_secret_client(ctx, vault_url, **kwargs):
    """
    Load the secret client and return a SecretClient object.

    :param vault_url: The URL of the vault that the client will access.

    """
    credential = _get_identity_credentials(ctx, **kwargs)

    secret_client = SecretClient(vault_url=vault_url, credential=credential)

    return secret_client


def unlock(
    hub, vault_url: str, designator: str = "acct-provider-", **kwargs
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    .. versionadded:: SOMEVERSIONHERE

    Get secrets from the Azure Key Vault.

    Example:

    .. code-block:: yaml

        acct-backend:
            azure_keyvault:
                vault_url: https://myvault.vault.azure.net

    """
    ret = {}

    sconn = _get_secret_client(ctx, vault_url, **kwargs)

    try:
        secrets = sconn.list_properties_of_secrets()

        for secret in secrets:
            if secret.name.startswith(designator):
                key = secret.name[len(designator) :]
                # We expect a dash-delimited string here:
                #     {PROVIDER}-{PROFILE}-{parameter}
                # Any dashes that are left in {parameter} will get converted to underscores.
                if key.count("-") < 2:
                    raise ValueError(
                        f"A dash-delimited string is expected after '{designator}'"
                        "with the format: PROVIDER-PROFILE-parametername"
                    )
                parts = key.split("-")
                provider = parts[0]
                profile = parts[1]
                param = "_".join(parts[2:])
                if provider not in ret:
                    ret[provider] = {}
                if profile not in ret[provider]:
                    ret[provider][profile] = {}
                # ret[provider][profile][param] = secret
    except (AttributeError, ResourceNotFoundError, TypeError, ValueError) as exc:
        hub.log.error("Unable to unlock Azure Key Vault: %s", exc)

    return ret
