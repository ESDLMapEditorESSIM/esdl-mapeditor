default_wms_layers = {
    "AHN2_5m": {
        "description": "AHN2 5 meter",
        "url": "http://geodata.nationaalgeoregister.nl/ahn2/wms?",
        "layer_name": "ahn2_5m",
        "layer_ref": None,
        "visible": False
    },
    "RVO_Restwarmte": {
        "description": "Restwarmte (RVO: ligging industrie)",
        "url": "https://geodata.nationaalgeoregister.nl/restwarmte/wms?",
        "layer_name": "liggingindustrieco2",
        "layer_ref": None,
        "visible": True
    }
}

class WMSLayers:

    def __init__(self):
        self.list = default_wms_layers

    def add_wms_layer(self, id, layer):
        self.list[id] = layer

    def remove_wms_layer(self, id):
        del(self.list[id])

    def get_layers(self):
        return self.list

