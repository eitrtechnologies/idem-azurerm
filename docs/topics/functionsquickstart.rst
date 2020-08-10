==========================
Quickstart - Function Apps
==========================
This quickstart guide servers as a tutorial of how you can deploy Microsoft Azure Functions to an Azure Function App using the
``idem-azurerm`` Function App state module. Refer to the "Installation" and "Credentials" sections of the
`Getting Started Guide <gettingstarted.html>`_ to get any prerequisites set up if this is your first time with
``idem-azurerm``.

Resource Definition
===================
Azure Function Apps are applications used to group Azure Functions together, allowing for easier
management, deployment, and resource sharing. Azure Functions let you execute your code in a serverless environment,
without having to create a VM or publish a web application. The ``idem-azurerm`` Function App state module provides
users with a way to build Function Apps and upload their Azure Function code to be serverlessly executed.

In order to use the ``idem-azurerm`` Function App state module, you must have a storage account of kind "Storage" or
"StorageV2" that will be used to store the Azure Functions for the Function App. A storage account can be created using
the following code:

.. code-block:: yaml

    Ensure storage account exists:
      azurerm.storage.account.present:
        - name: "stfunctionapp"
        - resource_group: "rg-function-app"
        - location: "eastus"
        - kind: "StorageV2"
        - sku: "Standard_LRS"
        - location: "eastus"

Now that you have a storage account set up, you can develop the Azure Functions that will be stored within it. You can
find information about developing Azure Functions locally `HERE <https://docs.microsoft.com/en-us/azure/azure-functions/functions-develop-local>`_.
In this quickstart example, we are going to be using the default HTTP Trigger function that will return "Hello, {name}"
upon being triggered. It is important to note that the Function App state module takes in a compressed (.zip) file
containing the function and its relevant files in order to upload it to the storage account. The compressed (.zip) file
will resemble the following folder structure::

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

Below are all relevant files for this example that will be inside of the functionapp.zip file:

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
                return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
            else:
                return func.HttpResponse(
                    "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
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

The example used for this quickstart utilizes the following folder structure::

    | functionapp.zip
    |   - host.json
    |   - HttpTrigger/
    |     - function.json
    |     - __init__.py

After you create a compressed (.zip) file using the folder structure outlined abobe, you are ready to use the
Function App state module. There are a few important things to note about the module:

* The Function App state module requires a Consumption Plan. If you do not already have a Consumption Plan, the module
  will create one for you (using a name you specify or a default name).
* The Function App allows you to enable Application Insights. Application Insights serve as a monitoring and analytics
  tool, enabling users to do things like diagnose issues or analyze application usage. If you want to enable Application
  Insights, you can pass the name of an existing Application Insights Component or one will be created for you (using a
  name you specify or a default name).
* The functions_file_path parameter should be the *absolute* path of the .zip file (i.e., "/root/dev/functions.zip").
  This .zip file will be uploaded to the specified storage account every time the state is run and will overwrite any
  existing file with the same name.

