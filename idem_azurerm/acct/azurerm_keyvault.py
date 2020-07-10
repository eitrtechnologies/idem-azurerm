# -*- coding: utf-8 -*-
"""
Azure Key Vault Backend for Acct

:depends:
    * `azure-identity <https://pypi.python.org/pypi/azure-identity>`_ == 1.3.0
    * `azure-keyvault-secrets <https://pypi.python.org/pypi/azure-keyvault-secrets>`_ == 4.1.0

:configuration: Get secrets from Azure Key Vault.

    Example:

    .. code-block:: yaml

        acct-backend:
            azurerm_keyvault:
                designator: "acct-provider-"
                vault_url: "https://myvault.vault.azure.net"
                client_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
                secret: "X2KRwdcdsQn9mwjdt0EbxsQR3w5TuBOR"
                subscription_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
                tenant: "cccccccc-cccc-cccc-cccc-cccccccccccc"

    To use this backend, configure the backend YAML as shown above for the
    credentials which can be used to access the Key Vault URL provided. A
    username and password or Managed Service Identities can be used in lieu of
    the service principal credentials shown in the example. Any identity used
    will need secrets/list and secrets/get permissions to the vault in order to
    retrieve the credentials.

    Credentials stored in the Key Vault will need to be named in a prescribed
    way in order to be properly retrieved and used for acct:

    .. code-block::

        {designator}{provider}-{profile}-{parameter}

    So, an example of secret names stored in Key Vault to be used for
    ``idem-azurerm`` would be:

    .. code-block::

        acct-provider-azurerm-default-client-id
        acct-provider-azurerm-default-secret
        acct-provider-azurerm-default-subscription-id
        acct-provider-azurerm-default-tenant

    This backend will only retrieve the latest version of a given secret, and
    the secret's value will only be retrieved from the vault if the naming
    matches the expected format. Note that any dashes after the profile field
    will be converted to underscores. This is due to limitations in secret
    naming and the fact that Python parameters shouldn't have dashes.

"""

# Python libs
from typing import Dict
import logging
import os


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

    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)


def __virtual__(hub):
    """
    Only load when Azure SDK imports successfully.
    """
    return HAS_LIBS


def _get_identity_credentials(**kwargs):
    """
    Acquire Azure RM Credentials from the identity provider

    We basically set environment variables based upon incoming parameters and then pass off to
    the DefaultAzureCredential object to correctly parse those environment variables. See the
    `Microsoft Docs on EnvironmentCredential <https://aka.ms/azsdk-python-identity-default-cred-ref>`_
    for more information.
    """
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


def _get_secret_client(vault_url: str, **kwargs):
    """
    Load the secret client and return a SecretClient object.

    :param vault_url: The URL of the vault that the client will access.

    """
    credential = _get_identity_credentials(**kwargs)

    secret_client = SecretClient(vault_url=vault_url, credential=credential)

    return secret_client


def unlock(
    hub, vault_url: str, designator: str = "acct-provider-", **kwargs
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Get secrets from the Azure Key Vault.
    """
    ret = {}

    try:
        sconn = _get_secret_client(vault_url, **kwargs)
        secrets = sconn.list_properties_of_secrets()
    except (HttpResponseError, ResourceExistsError, ResourceNotFoundError) as exc:
        log.error("Unable to unlock Azure Key Vault: %s", exc)
        return ret

    for secret in secrets:
        if secret.name.startswith(designator):
            try:
                key = secret.name[len(designator) :]

                # We expect a dash-delimited string here:
                #     {PROVIDER}-{PROFILE}-{parameter}
                if key.count("-") < 2:
                    log.error(
                        "A dash-delimited string is expected after '%s'"
                        "with the format 'PROVIDER-PROFILE-parametername', but got"
                        "'%s' instead.",
                        designator,
                        secret.name,
                    )
                    continue

                log.debug("acct found azurerm_keyvault secret: %s", key)
                parts = key.split("-")

                provider = parts[0]
                log.debug("acct found azurerm_keyvault provider: %s", provider)

                profile = parts[1]
                log.debug("acct found azurerm_keyvault profile: %s", profile)

                # Any dashes that are left in will get converted to underscores.
                param = "_".join(parts[2:])
                log.debug("acct found azurerm_keyvault parameter: %s", param)

                if provider not in ret:
                    ret[provider] = {}
                if profile not in ret[provider]:
                    ret[provider][profile] = {}

                sec = sconn.get_secret(name=secret.name)
                ret[provider][profile][param] = sec.value
            except (AttributeError, IndexError, TypeError) as exc:
                log.error("Unable to handle secret processing: %s", exc)
                continue

    return ret
