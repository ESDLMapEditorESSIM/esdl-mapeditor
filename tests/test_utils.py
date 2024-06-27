from pyecore.ecore import EObject

from esdl import EnergySystem


def find_asset_in_es(es: EnergySystem, asset_type, asset_name: str) -> EObject | None:
    """
    Find an asset in an EnergySystem by type and name.
    :param es: EnergySystem
    :param asset_type: type of asset, for example esdl.Pipe
    :param asset_name: name of the asset
    :return:
    """
    contents = es.eAllContents()
    for asset in contents:
        if isinstance(asset, asset_type):
            if asset.name == asset_name:
                return asset
    return None
