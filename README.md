# Microsoft Azure Cloud Provider for Idem

Azure is a cloud service offered by Microsoft that provides virtual machines, SQL services, media services, and more.
Azure Resource Manager is the next generation of the Azure portal and API. This provider is a [POP](https://gitlab.com/saltstack/pop/pop) 
plugin and an extension of [Idem](https://gitlab.com/saltstack/pop/idem), allowing Idem users to leverage Microsoft 
Azure Resource Manager functionality to enforce the state of cloud infrastructure, applications, configurations, and 
more. 

## INSTALLATION
The azurerm idem provider can be installed via pip:
`pip install idem-azurerm`

## INSTALLATION FOR DEVELOPMENT
1. Clone the `idem_provider_azurerm` repository and install with pip:
`pip install -r requirements.txt`
2. Run `pip install -e <path to provider>` from your project's root directory

You are now fully set up to begin developing additional functionality for this provider.

## EXECUTION
After installation the Azure Resource Manager Idem Provider execution and state modules will be accessible to the hub.

The provider authenticates with a service principal, so all state and execution modules require that a dictionary 
populated with the data shown below be passed to them.
```
{% set profile = {
    'client_id': '<YOUR CLIENT ID>',
    'secret': '<YOUR SECRET>',
    'subscription_id': '<YOUR SUBSCRIPTION ID>',
    'tenant': '<YOUR TENANT>' } %}
```
The following example uses an azurerm state module to ensure the existence of a resource group.
```
Resource group exists:
  azurerm.resource.group.present:
    - name: idem
    - location: eastus
    - tags:
        organization: EITR Technologies
    - connection_auth: {{ profile }}
```
