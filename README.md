# Microsoft Azure Cloud Provider for Idem

Azure is a cloud service offered by Microsoft that provides virtual machines, SQL services, media services, and more.
Azure Resource Manager is a next generation version of the Azure portal and API. This provider is an extension of Idem,
allowing it to leverage Microsoft Azure Resource Manager functionality to enforce the state of cloud infrastructure,
applications, configurations, and more.

## INSTALLATION
The azurerm idem provider can be installed via pip:
`pip install idem-azurerm`

## INSTALLATION FOR DEVELOPMENT
1. Clone the `idem_provider_azurerm` repository and install with pip:
`pip install -r requirements.txt`
2. Run `pip install -e <path to provider>` from your project's root directory

You are now fully set up to begin developing additional functionality for this provider.

## EXECUTION
After installation the Idem Azure Resource Manager Provider execution and state modules will be accessible to the hub.

Login data for Microsoft Azure is required for the Azure Resource Manager Provider. Unfortunately, a secure secret
storage system does not exist within Idem at the moment, so you will need to create a Jinja variable containing your
data in plain text. An example variable containing Azure login data is shown below.
```
{% set profile = {
    'client_id': '<YOUR CLIENT ID>',
    'secret': '<YOUR SECRET>',
    'subscription_id': '<YOUR SUBSCRIPTION ID>',
    'tenant': '<YOUR TENANT>' } %}
```
The following example below uses an azurerm state module to ensure the existence of a resource group.
```
Resource group exists:
  azurerm.resource.group.present:
    - name: idem
    - location: eastus
    - tags:
        organization: EITR Technologies
    - connection_auth: {{ profile }}
```
