=====================
Getting Started Guide
=====================
Azure is a cloud service offered by Microsoft that provides virtual machines, SQL services, media services, and more.
Azure Resource Manager is the next generation of the Azure portal and API. This provider is a
`POP <https://gitlab.com/saltstack/pop/pop>`_ plugin and an extension of
`Idem <https://gitlab.com/saltstack/pop/idem>`_, allowing Idem users to leverage Microsoft Azure Resource Manager
functionality to enforce the state of cloud infrastructure, applications, configurations, and more.

Installation
============
Idem is a Python 3 application, as are the plugins. In order to install the application we only have to look so far as
``pip``. Following best practices, let’s use a virtual environment so we don’t clutter our system Python packages:

.. code-block:: bash

    $ python3 -m venv idemenv

    $ source idemenv/bin/activate

    (idemenv) $ pip3 install idem-azurerm

This creates a virtual Python 3 environment, enters that environment, and then installs ``idem-azurerm``... which
automatically installs the required ``pop``, ``idem``, and Azure SDK libraries from PyPi. That’s it!

Credentials
===========
This provider requires that a dictionary populated with valid Azure credentials be passed via
`acct <https://gitlab.com/saltstack/pop/acct>`_.

The credentials can be stored in an arbitrarily named file, such as ``myawesomecreds.yml``

.. code-block:: yaml

    azurerm:
      default:
        client_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        secret: "X2KRwdcdsQn9mwjdt0EbxsQR3w5TuBOR"
        subscription_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        tenant: "cccccccc-cccc-cccc-cccc-cccccccccccc"

The root key of that YAML file shows that the credentials are for the ``azurerm`` plugin. Other plugins will have a
different root key based on their name. Underneath that key, we’re providing the default credentials. This is the key
that acct will attempt to present to states unless otherwise specified. Then, under the default key we have our service
principal credentials.

If you have another set of credentials you’d also like to use, then you’d just specify them under a different arbitrary
key name:

.. code-block:: yaml

    azurerm:
      default:
        client_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        secret: "X2KRwdcdsQn9mwjdt0EbxsQR3w5TuBOR"
        subscription_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        tenant: "cccccccc-cccc-cccc-cccc-cccccccccccc"
      medical:
        client_id: "dddddddd-dddd-dddd-dddd-dddddddddddd"
        secret: "JY7TzXdRVqV8swwH2gcJMZ9sIa9uAKGO"
        subscription_id: "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
        tenant: "cccccccc-cccc-cccc-cccc-cccccccccccc"

In order to prepare the credentials file for use, the acct command can be run to encrypt the file with the Fernet
algorithm.

.. code-block:: bash

    (idemenv) $ acct myawesomecreds.yml
    New encrypted file at: myawesomecreds.yml.fernet
    The file was encrypted with this key:
    71Gbz2oDSv40Er9YUFBJPzOjtCi6Z2-5niBHPekkvqs=

Now we have an encrypted file containing the credentials and a symmetric key for decryption. Since you have encrypted
the file with the key, you can now remove the original plaintext file.

.. code-block:: bash

    (idemenv) $ rm myawesomecreds.yml

All we have to do now is to tell idem where to get the file and key for acct. This information can be passed to acct on
the command line as parameters, but we will set up environment variables for the purposes of this tutorial.

.. code-block:: bash

    (idemenv) $ export ACCT_FILE="/path/to/myawesomecreds.yml.fernet"
    (idemenv) $ export ACCT_KEY="1Gbz2oDSv40Er9YUFBJPzOjtCi6Z2-5niBHPekkvqs="

Resource Definition
===================
After installation and configuration, the Azure Resource Manager Idem Provider execution and state modules will be
accessible to the hub. This will allow you to write YAML state files that use the Azure modules to interact with
Azure cloud resources.

The YAML below creates two resource groups, each using a different set of credentials provided by acct. The first will
attempt to use the default credentials because we haven’t explicitly defined them. The second has defined the "medical"
profile to be used for its credentials.

Put the following code in a file named ``mytest.sls``:

.. code-block:: yaml

    Ensure resource group exists:
      azurerm.resource.group.present:
        - name: "idem"
        - location: "eastus"
        - tags:
            Owner: "Elmer Fudd Gantry"
            Organization: "Everest"

    Ensure another resource group exists:
      azurerm.resource.group.present:
        - name: "medi"
        - location: "westus"
        - tags:
            Owner: "Dr. Rosenrosen"
            Organization: "General Hospital"
        - acct_profile: medical

If you didn't enter a second set of credentials for ``acct`` in the "Credentials" section above, feel free to omit the
``acct_profile`` parameter in the second resource group definition above.

Testing and Building Resources
==============================
Before you build the resources defined in the ".sls" file you may want to test what will happen when the state file is
run. To do this, run idem with the ``--test`` option.

.. code-block:: bash

    (idemenv) $ idem state mytest.sls --test

Once you determine that your state file with perform the intended operations, then you can build the defined resources
by running idem like so:

.. code-block:: bash

    (idemenv) $ idem state mytest.sls

Now you're ready to start building real resources in Azure! Consult the
`Idem State Module Reference <../ref/states/all/index.html>`_ for YAML examples of the creation of specific resources.

**Happy Idemizing!**
