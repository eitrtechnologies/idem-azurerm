# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Function App State Module

.. versionadded:: 3.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed via acct. Note that the
    authentication parameters are case sensitive.

    Required provider parameters:

    if using username and password:
      * ``subscription_id``
      * ``username``
      * ``password``

    if using a service principal:
      * ``subscription_id``
      * ``tenant``
      * ``client_id``
      * ``secret``

    Optional provider parameters:

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
      * ``AZURE_PUBLIC_CLOUD`` (default)
      * ``AZURE_CHINA_CLOUD``
      * ``AZURE_US_GOV_CLOUD``
      * ``AZURE_GERMAN_CLOUD``

    Example acct setup for Azure Resource Manager authentication:

    .. code-block:: yaml

        azurerm:
            default:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass

    The authentication parameters can also be passed as a dictionary of keyword arguments to the ``connection_auth``
    parameter of each state, but this is not preferred and could be deprecated in the future.

"""
# Python libs
from __future__ import absolute_import
from dict_tools import differ
import logging
from datetime import datetime, timedelta
import os

# Azure libs
HAS_LIBS = False
try:
    from azure.storage.blob import (
        ResourceTypes,
        AccountSasPermissions,
        generate_account_sas,
    )

    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)


async def present(
    hub,
    ctx,
    name,
    resource_group,
    functions_file_path,
    os_type,
    runtime_stack,
    storage_account,
    storage_rg=None,
    app_service_plan=None,
    functions_version=2,
    enable_app_insights=None,
    app_insights=None,
    tags=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Ensure that a Function App exists.

    :param name: The name of the Function App.

    :param resource_group: The name of the resource group of the Function App.

    :param functions_file_path: The file path of the compressed (zip) file containing any Azure Functions that should
        be deployed to the Function App. The Azure Functions inside of this zip file should be using the same runtime
        stack or language that is specified within the runtime_stack parameter. This file will be uploaded every
        successfully run of this state. If there is a prior version of the zip file it will be overwritten. IMPORTANT:
        The code for all the functions in a specific function app should be located in a root project folder that
        contains a host configuration file and one or more subfolders. Each subfolder contains the code for a separate
        function. The folder structure is shown in the representation below::

        | functionapp.zip
        |   - host.json
        |   - MyFirstFunction/
        |     - function.json
        |     - ..
        |   - MySecondFunction/
        |     - function.json
        |     - ..
        |   - SharedCode/
        |   - bin/

    :param os_type: The operation system utilized by the Function App. This cannot be changed after the Function App
        has been created. Possible values are "linux" or "windows".

    :param runtime_stack: The language stack to be used for functions in this Function App. Possible values are
        "dotnet", "node", "java", "python", or "powershell".

    :param storage_account: The name of the storage account that will hold the Azure Functions used by the Function App.
        This storage account must be of the kind "Storage" or "StorageV2". If not already present, a container named
        "function-releases" will be created within this storage account to hold the zip file containing any Azure
        Functions.

    :param storage_rg: (Optional, used with storage_account) The resource group of the storage account passed. This
        parameter is only necessary if the storage account has a different resource group than the one specified for
        the Function App.

    :param app_service_plan: The name of the App Service (Consumption) Plan used by the Function App. If this
        parameter is not provided or the provided name is invalid/does not exist, then an App Service (Consumption)
        Plan will be built for the Function App with the name "plan-{name}". This plan should have the same OS as
        specified by the os_type parameter.

    :param functions_version: The version of Azure Functions to use. Additional information about Azure Functions
        versions can be found here: https://docs.microsoft.com/en-us/azure/azure-functions/functions-versions.
        Possible values include: 1, 2, and 3. Defaults to 2.

    :param enable_app_insights: Boolean flag for enabling Application Insights.

    :param app_insights: (Optional, used with enable_app_insights) The name of the Application Insights Component to
        use for the Function App. If the specified Application Insights Component does not exist, then it will be
        created. If this parameter is not specified, then an Application Insights Component named "app-insights-{name}"
        will be created and used.

    :param tags: A dictionary of strings representing tag metadata for the Function App.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure function app exists:
            azurerm.web.function_app.present:
                - name: my_app
                - resource_group: my_group
                - functions_file_path: "/path/to/functions.zip"
                - os_type: "linux"
                - runtime_stack: "python"
                - storage_account: my_account
                - app_service_plan: my_plan
                - enable_app_insights: True
                - tags:
                    "Owner": "EITR Technologies"

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"
    app_settings = [
        {"name": "FUNCTIONS_WORKER_RUNTIME", "value": runtime_stack.lower()},
        {"name": "FUNCTIONS_EXTENSION_VERSION", "value": f"~{functions_version}",},
        {"name": "FUNCTION_APP_EDIT_MODE", "value": "readonly"},
        {"name": "SCM_DO_BUILD_DURING_DEPLOYMENT", "value": "false"},
    ]

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    # Ensures location is specified
    if "location" not in kwargs:
        rg_props = await hub.exec.azurerm.resource.group.get(
            ctx, resource_group, **kwargs
        )

        if "error" in rg_props:
            log.error("Unable to determine location from resource group specified.")
            return {
                "error": "Unable to determine location from resource group specified."
            }
        kwargs["location"] = rg_props["location"]

    # Handle storage account validation
    if not storage_rg:
        storage_rg = resource_group

    storage_acct = await hub.exec.azurerm.storage.account.get_properties(
        ctx, name=storage_account, resource_group=storage_rg
    )

    if "error" in storage_acct:
        log.error(
            f"The storage account {storage_account} does not exist within the given resource group {resource_group}."
        )
        ret[
            "comment"
        ] = f"The storage account {storage_account} does not exist within the given resource group {resource_group}."
        return ret

    # Ensure that the file path contains a zip file
    filename = os.path.basename(functions_file_path)
    if not filename.lower().endswith(".zip"):
        log.error(
            "The specified file in functions_file_path is not a compressed (zip) file."
        )
        ret[
            "comment"
        ] = "The specified file in functions_file_path is not a compressed (zip) file."
        return ret

    # Set reserved for the ASP and Function App based upon OS type
    if os_type.lower() == "windows":
        reserved = False
    else:  # linux
        reserved = True

    # Handle App Service Plan creation
    if not app_service_plan:
        app_service_plan = f"plan-{name}"

    plan = await hub.exec.azurerm.web.app_service_plan.get(
        ctx, name=app_service_plan, resource_group=resource_group
    )

    if "error" in plan:
        plan = await hub.exec.azurerm.web.app_service_plan.create_or_update(
            ctx,
            name=app_service_plan,
            resource_group=resource_group,
            kind="functionapp",
            reserved=reserved,
            sku="Y1",
            **connection_auth,
        )

        if "error" in plan:
            log.error(
                f"Unable to create the App Service Plan {app_service_plan} in the resource group {resource_group}."
            )
            ret[
                "comment"
            ] = f"Unable to create the App Service Plan {app_service_plan} in the resource group {resource_group}."
            return ret
    elif plan["reserved"] != reserved:
        log.error(
            f"The OS of the App Service Plan {app_service_plan} does not match the specified OS type for the Function App and thus cannot be used."
        )
        ret[
            "comment"
        ] = f"The OS of the App Service Plan {app_service_plan} does not match the specified OS type for the Function App and thus cannot be used."
        return ret

    # Gets the resource ID of the ASP
    server_farm_id = plan["id"]

    # Handle App Insights Validation and Creation
    if enable_app_insights:
        if not app_insights:
            app_insights = f"app-insights-{name}"

        component = await hub.exec.azurerm.application_insights.component.get(
            ctx, name=app_insights, resource_group=resource_group
        )

        if "error" in component:
            component = await hub.exec.azurerm.application_insights.component.create_or_update(
                ctx,
                name=app_insights,
                resource_group=resource_group,
                kind="web",
                application_type="web",
            )

            if "error" in component:
                log.error(
                    f"Unable to create the Application Insights Component {app_insights} within the resource group {resource_group}."
                )
                ret[
                    "comment"
                ] = f"Unable to create the Application Insights Component {app_insights} within the resource group {resource_group}."
                return ret

        instrumentation_key = component["instrumentation_key"]
        # Configures the application insights for the app settings
        app_settings.append(
            {"name": "APPINSIGHTS_INSTRUMENTATIONKEY", "value": instrumentation_key}
        )

    # Builds a storage container named "function-releases" within the specified storage account if not already present
    container = await hub.exec.azurerm.storage.container.get(
        ctx,
        name="function-releases",
        account=storage_account,
        resource_group=storage_rg,
    )

    if "error" in container:
        container = await hub.exec.azurerm.storage.container.create(
            ctx,
            name="function-releases",
            account=storage_account,
            resource_group=storage_rg,
            public_access="None",
        )

    # Upload the zip file containing the Azure Functions
    upload_zip = await hub.exec.azurerm.storage.container.upload_blob(
        ctx,
        name=filename,
        container="function-releases",
        account=storage_account,
        resource_group=storage_rg,
        file_path=functions_file_path,
        overwrite=True,
    )

    if "error" in upload_zip:
        log.error(
            f"Unable to upload {filename} to the function-releases container within the storage account {storage_account}."
        )
        ret[
            "comment"
        ] = f"Unable to upload {filename} to the function-releases container within the storage account {storage_account}."
        return ret

    # Retrieves the access keys for the storage account
    storage_acct_keys = await hub.exec.azurerm.storage.account.list_keys(
        ctx, name=storage_account, resource_group=storage_rg
    )
    if "error" not in storage_acct_keys:
        storage_acct_key = storage_acct_keys["keys"][0]["value"]
    else:
        log.error(
            f"Unable to get the account access key for the specified storage account {storage_account} within the given resource group {storage_rg}."
        )
        ret[
            "comment"
        ] = f"Unable to get the account access key for the specified storage account {storage_account} within the given resource group {storage_rg}."
        return ret

    # Generate the sas token used within app settings
    sas_token = generate_account_sas(
        account_name=storage_account,
        account_key=storage_acct_key,
        resource_types=ResourceTypes(object=True, container=True, service=True),
        permission=AccountSasPermissions(read=True, write=True, list=True, delete=True),
        expiry=datetime.utcnow() + timedelta(days=2),
    )

    # Update app settings information from the storage account
    app_settings.append(
        {
            "name": "AzureWebJobsStorage",
            "value": f"DefaultEndpointsProtocol=https;AccountName={storage_account};AccountKey={storage_acct_key}",
        }
    )
    app_settings.append(
        {
            "name": "WEBSITE_RUN_FROM_PACKAGE",
            "value": f"https://{storage_account}.blob.core.windows.net/function-releases/{filename}?{sas_token}",
        }
    )

    # Add any app settings related to a specific OSs
    if os_type.lower() == "windows":
        app_settings.append(
            {
                "name": "WEBSITE_CONTENTAZUREFILECONNECTIONSTRING",
                "value": f"DefaultEndpointsProtocol=https;AccountName={storage_account};AccountKey={storage_acct_key}",
            }
        )
        app_settings.append({"name": "WEBSITE_CONTENTSHARE", "value": name.lower()})

    # Check for the existence of the Function App
    function_app = await hub.exec.azurerm.web.app.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" not in function_app:
        action = "update"

        # tag changes
        tag_changes = differ.deep_diff(function_app.get("tags", {}), tags or {})
        if tag_changes:
            ret["changes"]["tags"] = tag_changes

        # app service plan changes
        if function_app.get("server_farm_id") != server_farm_id:
            ret["changes"]["server_farm_id"] = {
                "new": server_farm_id,
                "old": function_app.get("server_farm_id"),
            }

        # app setting changes
        existing_settings = await hub.exec.azurerm.web.app.list_application_settings(
            ctx, name=name, resource_group=resource_group
        )
        old_settings = existing_settings["properties"]
        new_settings = {}
        for setting in app_settings:
            new_settings.update({setting.get("name"): setting.get("value")})

        # Checks specifically for changes within the WEBSITE_RUN_FROM_PACKAGE app setting because the value of that
        # setting is changed every run.
        new_run_package_setting = new_settings.pop("WEBSITE_RUN_FROM_PACKAGE", "")
        old_run_package_setting = old_settings.pop("WEBSITE_RUN_FROM_PACKAGE", "")

        new_beginning = (new_run_package_setting.split("?"))[0]
        old_beginning = (old_run_package_setting.split("?"))[0]

        run_package_changes = False
        if old_beginning != new_beginning:
            run_package_changes = True

        # If there are changes within WEBSITE_RUN_FROM_PACKAGE, then that app setting should be readded to both settings
        # dictionaries to be recorded as app setting changes changes
        if run_package_changes:
            new_settings.update({"WEBSITE_RUN_FROM_PACKAGE": new_run_package_setting})
            old_settings.update({"WEBSITE_RUN_FROM_PACKAGE": old_run_package_setting})

        app_settings_changes = differ.deep_diff(old_settings, new_settings)
        if app_settings_changes:
            ret["changes"]["site_config"] = {"app_settings": app_settings_changes}

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = "Function App {0} is already present.".format(name)
            return ret

        if ctx["test"]:
            ret["result"] = None
            ret["comment"] = "Function App {0} would be updated.".format(name)
            return ret

    else:
        ret["changes"] = {
            "old": {},
            "new": {
                "name": name,
                "resource_group": resource_group,
                "app_service_plan": app_service_plan,
                "os_type": os_type,
                "runtime_stack": runtime_stack,
                "site_config": {"app_settings": app_settings},
                "tags": tags,
            },
        }

        if enable_app_insights:
            ret["changes"]["new"]["application_insights"] = app_insights

    if ctx["test"]:
        ret["comment"] = "Function App {0} would be created.".format(name)
        ret["result"] = None
        return ret

    app_kwargs = kwargs.copy()
    app_kwargs.update(connection_auth)

    kind = "functionapp"
    if os_type.lower() == "linux":
        kind = kind + ",Linux"

    function_app = await hub.exec.azurerm.web.app.create_or_update(
        ctx=ctx,
        name=name,
        resource_group=resource_group,
        tags=tags,
        server_farm_id=server_farm_id,
        kind=kind,
        site_config={"app_settings": app_settings},
        **app_kwargs,
    )

    if "error" not in function_app:
        ret["result"] = True
        ret["comment"] = f"Function App {name} has been {action}d."
        return ret

    ret["comment"] = "Failed to {0} Function App {1}! ({2})".format(
        action, name, function_app.get("error")
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


async def absent(hub, ctx, name, resource_group, connection_auth=None, **kwargs):
    """
    .. versionadded:: 3.0.0

    Ensure a Function App does not exist within the specified resource group.

    :param name: The name of the Function App.

    :param resource_group: The name of the resource group of the Function App.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure function app is absent:
            azurerm.web.function_app.absent:
                - name: my_app
                - resource_group: my_group

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}

    if not isinstance(connection_auth, dict):
        if ctx["acct"]:
            connection_auth = ctx["acct"]
        else:
            ret[
                "comment"
            ] = "Connection information must be specified via acct or connection_auth dictionary!"
            return ret

    function_app = await hub.exec.azurerm.web.app.get(
        ctx, name, resource_group, azurerm_log_level="info", **connection_auth
    )

    if "error" in function_app:
        ret["result"] = True
        ret["comment"] = "Function App {0} was not found.".format(name)
        return ret

    if ctx["test"]:
        ret["comment"] = "Function App {0} would be deleted.".format(name)
        ret["result"] = None
        ret["changes"] = {
            "old": function_app,
            "new": {},
        }
        return ret

    deleted = await hub.exec.azurerm.web.app.delete(
        ctx, name, resource_group, **connection_auth
    )

    if deleted:
        ret["result"] = True
        ret["comment"] = "Function App {0} has been deleted.".format(name)
        ret["changes"] = {"old": function_app, "new": {}}
        return ret

    ret["comment"] = "Failed to delete Function App {0}!".format(name)
    return ret
