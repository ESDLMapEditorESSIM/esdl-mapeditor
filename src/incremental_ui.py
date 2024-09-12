#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

"""
This file contains messages and message preparation for incremental ui updates.
"""
from typing import TypedDict, List, NotRequired

from esdl import esdl


###################################
# Update ports of assets in the GUI
###################################


class ConnectedTo(TypedDict):
    id: str  # port id
    a_name: str  # asset name


class PortMessage(TypedDict):
    name: str
    id: str
    type: str
    conn_to: List[ConnectedTo]
    carrier: str
    exposed: NotRequired[bool]  # remove field if not needed


class UpdateAssetMessage(TypedDict):
    asset_id: str
    """
    UUID of the asset
    """
    ports: List[PortMessage]
    """
    List of PortMessage data
    """
    exposed_port_asset: bool
    """
    Defines if the asset is an ExposedPortAsset or an EnergyAsset
    """


def create_update_asset_message(
    asset: esdl.EnergyAsset | esdl.ExposedPortsAsset, port_list: List[PortMessage] = None
) -> UpdateAssetMessage:
    """
    Create socket.io 'update_asset' message to the frontend.

    Most important data is the port information, such that markers on the map are updated (and context menus of these
    assets too)

    :param asset: an asset with ports (EnergyAsset, ExposedPort asset / connectable asset)
    :param port_list: optional use this port list instead of ports calculated based on the asset ports
    :return: UpdateAssetMessage that can be sent with emit('update_asset', UpdateAssetMessage)
    """
    if port_list is None:
        port_list = create_asset_port_message(asset)
    return UpdateAssetMessage(
        asset_id=asset.id, ports=port_list, exposed_port_asset=isinstance(asset, esdl.ExposedPortsAsset)
    )


def create_asset_port_message(asset: esdl.EnergyAsset | esdl.ExposedPortsAsset) -> List[PortMessage]:
    """
    Creates a list of PortMessages based on each port an asset has.

    PortMessage is used as part of 'asset_update' message UpdateAssetMessage
    :ref: UpdateAssetMessage
    """
    exposed_ports: List[esdl.Port] = []
    exposed_port_asset = asset.containingAsset or asset.containingBuilding
    if exposed_port_asset and len(exposed_port_asset.port) > 0:
        exposed_ports = exposed_port_asset.port
    port_list: List[PortMessage] = []
    for p in asset.port:
        port_list.append(
            create_port_message(p, exposed_port=(isinstance(asset, esdl.ExposedPortsAsset) or (p in exposed_ports)))
        )
    return port_list


def create_port_message(p: esdl.InPort | esdl.OutPort, exposed_port: bool = False) -> PortMessage:
    """
    Creates a PortMessage for a port
    :param p:
    :param exposed_port: if exposed_port is true, this is added to the PortMessage to be used in the Gui.
        This indicates that that specific port has been exposed in the parent building or compound asset.
    :return: PortMessage
    """
    p_message = PortMessage(
        name=p.name,
        id=p.id,
        type=type(p).__name__,
        conn_to=[ConnectedTo(id=pt.id, a_name=pt.energyasset.name if pt.energyasset else None) for pt in p.connectedTo],
        # conn_to_name=[pt.energyasset.name for pt in p.connectedTo],
        carrier=p.carrier.id if p.carrier else None,
    )
    if exposed_port:  # add only if port is exposed (smaller message size)
        p_message["exposed"] = exposed_port
    return p_message
