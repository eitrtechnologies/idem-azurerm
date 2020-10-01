# -*- coding: utf-8 -*-
"""
Azure Resource Manager (ARM) Container Instance Execution Module

.. versionadded:: 3.0.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function or via acct in order to work properly.

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

"""
# Python libs
import logging
import platform
import select
import shutil
import signal
import sys

# Not supported for Windows machines.
try:
    import termios
    import tty
except ImportError:
    pass

# Not supported for Linux machines.
try:
    import msvcrt
    import threading
except ImportError:
    pass

# Azure libs
HAS_LIBS = False
try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import SerializationError
    import azure.mgmt.containerinstance  # pylint: disable=unused-import
    import websocket

    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)


def __virtual__(hub):
    """
    Only load when Azure SDK imports successfully.
    """
    return HAS_LIBS


def _cycle_exec_pipe(ws):
    """
    Convenience function for exec pipe handling.
    """
    r, _, _ = select.select([ws.sock, sys.stdin], [], [])
    if ws.sock in r:
        data = ws.recv()
        if not data:
            return False
        sys.stdout.write(data)
        sys.stdout.flush()
    if sys.stdin in r:
        x = sys.stdin.read(1)
        if not x:
            return True
        ws.send(x)
    return True


def _start_exec_pipe(web_socket_uri, password):
    """
    Start an interactive session on... not Windows.
    """
    ws = websocket.create_connection(web_socket_uri)

    oldtty = termios.tcgetattr(sys.stdin)
    old_handler = signal.getsignal(signal.SIGWINCH)

    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        ws.send(password)
        while True:
            try:
                if not _cycle_exec_pipe(ws):
                    break
            except (select.error, IOError) as e:
                if e.args and e.args[0] == errno.EINTR:
                    pass
                else:
                    raise
    except websocket.WebSocketException:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        signal.signal(signal.SIGWINCH, old_handler)


def _on_ws_msg(ws, msg):
    """
    Convenience function for Windows exec pipe handling.
    """
    sys.stdout.write(msg)
    sys.stdout.flush()


def _capture_stdin(ws):
    """
    Convenience function for Windows exec pipe handling.
    """
    while True:
        if msvcrt.kbhit:  # pylint: disable=using-constant-test
            x = msvcrt.getch()
            ws.send(x)


def _start_exec_pipe_win(web_socket_uri, password):
    """
    Start an interactive session on Windows.
    """

    def _on_ws_open(ws):
        ws.send(password)
        t = threading.Thread(target=_capture_stdin, args=[ws])
        t.daemon = True
        t.start()

    ws = websocket.WebSocketApp(
        web_socket_uri, on_open=_on_ws_open, on_message=_on_ws_msg
    )

    ws.run_forever()


async def execute_command(
    hub,
    ctx,
    name,
    container_group,
    resource_group,
    command="/bin/bash",
    terminal_size_cols=None,
    terminal_size_rows=20,
    **kwargs,
):
    """
    .. versionadded:: 3.0.0

    Creates an interactive shell for a specific container instance in a specified resource group and container group.

    Azure Container Instances currently only support launching a single process and you cannot pass command arguments.
    For example, you cannot chain commands like in ``sh -c "echo FOO && echo BAR"`` or execute ``echo FOO``.

    :param name: The name of the container instance.

    :param container_group: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    :param command: The command to be executed. Defaults to "/bin/bash" but will generally only be shells like "/bin/sh"
        or "cmd.exe" otherwise. Once ACI supports arguments, we can change this module to support non-interactive
        commands.

    :param terminal_size_cols: The column size of the terminal. If not provided, your current terminal size will be
        used.

    :param terminal_size_rows: The row size of the terminal.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.container.execute_command container containergroup resourcegroup

    """
    result = {}

    if not terminal_size_cols:
        term = shutil.get_terminal_size((80, terminal_size_rows))
        terminal_size_cols = term.columns

    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )

    try:
        ret = conconn.containers.execute_command(
            container_name=name,
            container_group_name=container_group,
            resource_group_name=resource_group,
            command=command,
            terminal_size={"cols": terminal_size_cols, "rows": terminal_size_rows,},
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        return {"error": str(exc)}

    if platform.system() == "Windows":
        _start_exec_pipe_win(result["web_socket_uri"], result["password"])
    else:
        _start_exec_pipe(result["web_socket_uri"], result["password"])

    return {}


async def list_logs(
    hub, ctx, name, container_group, resource_group, tail=None, **kwargs
):
    """
    .. versionadded:: 3.0.0

    Get the logs for a specified container instance in a specified resource group and container group.

    :param name: The name of the container instance.

    :param container_group: The name of the container group.

    :param resource_group: The name of the resource group to which the container group belongs.

    :param tail: The number of lines to show from the tail of the container instance log. If not provided, all
        available logs are shown up to 4mb.

    CLI Example:

    .. code-block:: bash

        azurerm.containerinstance.container.list_logs container containergroup resourcegroup

    """
    result = {}
    conconn = await hub.exec.azurerm.utils.get_client(
        ctx, "containerinstance", **kwargs
    )
    try:
        ret = conconn.containers.list_logs(
            container_name=name,
            container_group_name=container_group,
            resource_group_name=resource_group,
            tail=tail,
        )
        result = ret.as_dict()
    except CloudError as exc:
        await hub.exec.azurerm.utils.log_cloud_error(
            "containerinstance", str(exc), **kwargs
        )
        result = {"error": str(exc)}

    return result
