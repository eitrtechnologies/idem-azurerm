==========================
Quickstart - Function Apps
==========================
Azure Functions let you execute your code in a serverless environment, without having to create a VM or publish a web
application. Azure Function Apps are applications used to group Azure Functions together, allowing for easier
management, deployment, and resource sharing. The ``idem-azurerm`` Function App state module provides users with a way
to build Function Apps and upload their Azure Functions to be executed serverlessly. This quickstart guide demonstrates
the deployment of a HTTP trigger function within a Function App created using the state module. The HTTP trigger
function will run whenever it receives an HTTP request, responding based on information passed in the request. In
this case, the HTTP trigger function will respond to the HTTP request with "Hello, {name}" where {name} is passed as a
query parameter.

Azure Function Creation
=======================
If it is your first time using ``idem-azurerm``, please refer to the "Installation" and "Credentials" sections of the
`Getting Started Guide <gettingstarted.html>`_ to get any prerequisites set up.

The first step is to create the Azure Functions you will store within your function App. Information about developing
Azure Functions locally can be found `here <https://docs.microsoft.com/en-us/azure/azure-functions/functions-develop-local>`_.
The Function App state module will upload any Azure Functions you create into a storage account. The Azure Functions
must be stored within a compressed (.zip) file in order to be uploaded to the storage account via the state module. The
contents of the compressed (.zip) file will resemble the following file structure::

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

The zip file used for this demonstration will utilize the following file structure::

    | functionapp.zip
    |   - host.json
    |   - HttpTrigger/
    |     - function.json
    |     - __init__.py

Below is the content of each file necessary for the demonstration:

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

You can create the zip file yourself using the provided folder structure and file content specified above.

Infrastructure Setup
====================
In order to use the ``idem-azurerm`` Function App state module, you must have a resource group for the Function App to
preside within and a storage account of the kind "Storage" or "StorageV2." The Azure Functions will be stored with that
storage account and then the Function App will run the file containing all of the functions. Below is a state file that
sets up the resource group and storage account for this demonstration:

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

State Module Usage
==================
Now that you have deployed the appropriate infrastructure and created the zip file for the Azure Functions, you are
ready to run the Function App state module. Here are a few important things to note about the module:

* The Function App state module requires a Consumption Plan. If you do not already have a Consumption Plan, the module
  will create one for you (using a name you specify or a default name). If you do use an existing Consumption Plan, the
  OS of that plan must match the OS specified within the os_type parameter.
* The module also allows you to enable Application Insights. Application Insights serve as a monitoring and analytics
  tool, enabling users to do things like diagnose issues or analyze application usage. If you want to enable Application
  Insights, you can specify the name of an existing Application Insights Component or one will be created for you (using a
  name you specify or a default name).
* The functions_file_path parameter should be the *absolute* path of the .zip file (i.e., "/root/dev/functions.zip").
  This file will be uploaded to the specified storage account every time the state is run and will overwrite any
  existing file with the same name.
* The value of runtime_stack parameter must match the runtime language used by the Azure Functions.
* If it is not already present, a container named "function-releases" will be created within the storage account to
  hold the zip file.
* The OS type of the Function App cannot be changed once initially set.

In order to run the HTTP trigger function created above, you will want to create a Function App running a Linux OS with a
Python runtime stack. The state below does just that, creating a Consumption Plan named "plan-function-app", an
Application Insights Component named "appi-function-app", and a Function App named "func-idem". More information
regarding the parameters used within the state module can be found in the module reference documentation.

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
use. Every Azure Function within a Function App has its own unique function URL in the following format: ``https://{function_app_name}.azurewebsites.net/api/{function_name}?``.
In order to test that the HTTP trigger function is working properly, you can open a browser session and go to the
function URL of the function. You will want to add the ``name`` parameter to the query string for the request. (i.e.,
``https://func-idem.azurewebsites.net/api/HttpTrigger?name=Alex``), then you notice that the response "Hello, {name}" is
displayed in your browser. Once you see that message you know that you have succesfully deployed your first Azure
Function to a Function App using ``idem-azurerm``!
