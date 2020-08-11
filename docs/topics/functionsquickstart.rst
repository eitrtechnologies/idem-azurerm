==========================
Quickstart - Function Apps
==========================
Azure Functions let you execute your code in a serverless environment, without having to create a VM or publish a web
application. Azure Function Apps are applications used to group Azure Functions together, allowing for easier
management, deployment, and resource sharing. The ``idem-azurerm`` Function App state module provides users with a way
to build Function Apps and upload their Azure Functions to be serverlessly executed. This quickstart guide demonstrates
that functionality, showing the creation of a Function App containing a HTTP trigger function. The HTTP trigger function
will be run whenever it receives an HTTP request, responding based on information passed within the request. In this
case, the HTTP trigger function will respond to the HTTP request with "Hello, {name}" where {name} is passed in as a
query parameter.

Azure Function Creation
=======================
Refer to the "Installation" and "Credentials" sections of the `Getting Started Guide <gettingstarted.html>`_ to get any
prerequisites set up if this is your first time with ``idem-azurerm``.

The first step of this demonstration is to create any Azure Functions you want stored within your function App. You can
develop find information about developing Azure Functions locally `here <https://docs.microsoft.com/en-us/azure/azure-functions/functions-develop-local>`_.
The Function App state module will upload any Azure Functions you create into a storage account. The Azure Functions
must be stored within a compressed (.zip) file when uploaded to the storage account. The contents of the compressed
(.zip) file will resemble the following file structure::

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

The .zip file used for this demonstration will employ the following file structure::

    | functionapp.zip
    |   - host.json
    |   - HttpTrigger/
    |     - function.json
    |     - __init__.py

Below is the content of each files used for this demonstration:

**host.json**
    .. code-block:: JSON

        {
            "version": "2.0",
            "logging": {
                "applicationInsights": {
                    "samplingSettings": {
                        "isEnabled": true,
                        "excludedTypes": "Request"
                    }
                }
            },
            "extensionBundle": {
                "id": "Microsoft.Azure.Functions.ExtensionBundle",
                "version": "[1.*, 2.0.0)"
            }
        }

**__init__.py**
    .. code-block:: python

        import logging
        import azure.functions as func

        def main(req: func.HttpRequest) -> func.HttpResponse:
            logging.info('Python HTTP trigger function processed a request.')

            name = req.params.get('name')
            if not name:
                try:
                    req_body = req.get_json()
                except ValueError:
                    pass
                else:
                    name = req_body.get('name')

            if name:
                return func.HttpResponse(f"Hello, {name}")
            else:
                return func.HttpResponse(
                    "This HTTP triggered function executed successfully, but no name was passed to the function.",
                    status_code=200
                )

**function.json**
    .. code-block:: JSON

        {
            "scriptFile": "__init__.py",
            "bindings": [
                {
                    "authLevel": "anonymous",
                    "type": "httpTrigger",
                    "direction": "in",
                    "name": "req",
                    "methods": [
                        "get",
                        "post"
                    ]
                },
                {
                    "type": "http",
                    "direction": "out",
                    "name": "$return"
                }
            ]
        }

You can use the provided files and folder structure to create the necessary .zip file.

State Usage
===========
In order to use the ``idem-azurerm`` Function App state module, you must have a resource group for the Function App to
preside within and storage account of kind "Storage" or "StorageV2" that will be used to store the Azure Functions for
the Function App. Below is a state file setting up the resource group and storage account that will be used for
this demonstration:

**setup.sls**
    .. code-block:: yaml

        Ensure resource group exists:
          azurerm.resource.group.present:
            - name: "rg-function-app"
            - location: "eastus"
            - tags:
                Organization: "EITR Technologies"

        Ensure storage account exists:
          azurerm.storage.account.present:
            - name: "stfunctionapp"
            - resource_group: "rg-function-app"
            - location: "eastus"
            - kind: "StorageV2"
            - sku: "Standard_LRS"
            - location: "eastus"

Now that you have the .zip file containg Azure Functions created and the appropriate infrastructure deployed, you are
ready to run the Function App state module. There are a few important things to note about the module:

* The Function App state module requires a Consumption Plan. If you do not already have a Consumption Plan, the module
  will create one for you (using a name you specify or a default name).
* The Function App allows you to enable Application Insights. Application Insights serve as a monitoring and analytics
  tool, enabling users to do things like diagnose issues or analyze application usage. If you want to enable Application
  Insights, you can pass the name of an existing Application Insights Component or one will be created for you (using a
  name you specify or a default name).
* The functions_file_path parameter should be the *absolute* path of the .zip file (i.e., "/root/dev/functions.zip").
  This .zip file will be uploaded to the specified storage account every time the state is run and will overwrite any
  existing file with the same name.
* The value of runtime_stack parameter must match the runtime language used by the Azure Functions.
* If it does not already present, a container named "function-releases" will be created within the storage account to
  hold the .zip file containing the Azure Functions.

The following are parameters of the Function App state module:

* name: The name of your Function App.
* resource_group: The resource group of your Function App
* functions_file_path: The absolute path to the zip file containing your Azure Functions.
* os_type: The operation system utilized by the Function App. This cannot be changed after the Function App has
  been created. Possible values include "linux" and "windows".
* runtime_stack: The language stack to be used for functions in this Function App. Possible values are "dotnet",
  "node", "java", "python", or "powershell".
* storage_account: The name of the storage account used by the Function App.
* storage_rg: (Optional, used with storage_account) The resource group of the storage account passed. This parameter
  is only necessary if the storage account has a different resource group than the one specified for the Function App.
* app_service_plan: The name of the App Service (Consumption) Plan used by the Function App. As previously stated, if
  this parameter is not provided or the provided plan name does not exist, then a Consumption Plan will be built for the
  Function App with the name "plan-{name}". If an existing Consumption Plan is specified, it should have the same OS as
  specified by the os_type parameter.
* functions_version: The version of Azure Functions to use. Defaults to 2.
* enable_app_insights: Boolean flag for enabling Application Insights. Defaults to None.
* app_insights: (Optional, used with enable_app_insights set as True) The name of the Application Insights Component to
  use for the Function App. If this parameter is not specified or the provided component does not exist, then an
  Application Insights Component named "app-insights-{name}" will be created and used.
* tags: A dictionary of strings representing tag metadata for the Function App.

In order to run the HTTP trigger function created above, we want to create a Function App with a Python runtime stack
running a Linux OS. The state below does just that, creating a Consumption Plan named "plan-function-app", an
Application Insights Component named "appi-function-app", and a Function App named "func-idem".

**function_app.sls**
    .. code-block:: yaml

        Ensure function app exists:
          azurerm.web.function_app.present:
            - name: "func-idem"
            - resource_group: "rg-function-app"
            - functions_file_path: "/root/dev/functioncode.zip"
            - os_type: "linux"
            - runtime_stack: "python"
            - app_service_plan: "plan-function-app"
            - storage_account: "stfunctionapp"
            - enable_app_insights: True
            - app_insights: "appi-function-app"

After the execution of the state successfully completes, the function(s) you uploaded to the Function App are ready for
use. Every Azure Function within a Function App has its own unique function URL in the format ``https://{function_app_name}.azurewebsites.net/api/{function_name}?``.
If you open a browser session and enter the function URL of our HTTP trigger, passing a query string that specifies a
value for the ``name`` parameter (i.e., ``https://func-idem.azurewebsites.net/api/HttpTrigger?name=Alex``), then you
will get a response displaying "Hello, {name}" on the screen. You have now succesfully deployed your first Azure
Function using ``idem-azurerm``!
