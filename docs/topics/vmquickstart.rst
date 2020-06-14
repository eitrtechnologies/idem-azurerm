============================
Quickstart - Virtual Machine
============================
This quickstart is guide is meant to give you a state file you can modify to deploy a simple Linux virtual machine
that's accessible via SSH over a public IP address. Refer to the "Installation" and "Credentials" sections of the
`Getting Started Guide <gettingstarted.html>`_ to get any prerequisites set up if this is your first time with
``idem-azurerm``.

Resource Definition
===================
The YAML below creates a resource group, a virtual network, and a small Linux virtual machine. It will also create a
network interface and public IP address automatically for us even though we didn't explicitly define them. Look at Idem
being all helpful!

Put the following code in a file named ``basicvm.sls``:

.. code-block:: yaml

    Ensure resource group exists:
      azurerm.resource.group.present:
        - name: "rg-basicvm"
        - location: "eastus"

    Ensure virtual network exists:
      azurerm.network.virtual_network.present:
        - name: "vnet-basicvm-eastus-001"
        - resource_group: "rg-basicvm"
        - address_prefixes:
          - "192.168.0.0/16"
        - subnets:
          - name: "default"
            address_prefix: "192.168.0.0/24"

    Ensure virtual machine exists:
      azurerm.compute.virtual_machine.present:
        - name: "vmbasic001"
        - resource_group: "rg-basicvm"
        - vm_size: "Standard_B2S"
        - image: "OpenLogic|CentOS|7.7|latest"
        - virtual_network: "vnet-basicvm-eastus-001"
        - subnet: "default"
        - allocate_public_ip: True
        - admin_username: "idem"
        - ssh_public_keys:
          - "/path/to/my/ssh/id_rsa.pub"

Be sure to change the ``ssh_public_keys`` parameter to an actual SSH public key location on your system. If you'd rather
pass a username and password, you can remove the ``ssh_public_keys`` parameter altogether and replace it with the
the proper password parameters. Therefore, the virtual machine state would look like this:

.. code-block:: yaml

    Ensure virtual machine exists:
      azurerm.compute.virtual_machine.present:
        - name: "vmbasic001"
        - resource_group: "rg-basicvm"
        - vm_size: "Standard_B2S"
        - image: "OpenLogic|CentOS|7.7|latest"
        - virtual_network: "vnet-basicvm-eastus-001"
        - subnet: "default"
        - allocate_public_ip: True
        - admin_username: "idem"
        - admin_password: "HeyThere!IhopeURgoing2ChangeThis!"
        - disable_password_auth: False

Make sure you change that password!

Testing and Building Resources
==============================
Before you build the resources defined in the ".sls" file you may want to test what will happen when the state file is
run. To do this, run idem with the ``--test`` option.

.. code-block:: bash

    (idemenv) $ idem state basicvm.sls --test

Once you determine that your state file with perform the intended operations, then you can build the defined resources
by running idem like so:

.. code-block:: bash

    (idemenv) $ idem state basicvm.sls

If you're curious as to what the public IP address is, you don't even have to switch over to the Azure Portal. Just run
this execution module command in order to get that information:

.. code-block:: bash

    (idemenv) $ idem exec azurerm.network.public_ip_address.get vmbasic001-pip0 rg-basicvm --output=nested

Now you're ready to start building more resources in Azure! Consult the
`Idem State Module Reference <../ref/states/all/index.html>`_ for YAML examples of the creation of specific resources.

**Happy Idemizing!**
