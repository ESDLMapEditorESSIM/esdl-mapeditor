from dataclasses import dataclass
from typing import Dict, List, Optional, Union

@dataclass
class MouseEventLatLng:
    """Leaflet MouseClick event object"""
    lat: float
    lng: float

@dataclass
class WmsLayerRequestInfo:
    """
    WMS layer info. passed from frontend to backend to request the layer feature properties.
    """
    name: str
    """WMS layer name"""
    url: str
    """WMS layer GetFeatureInfo Url"""

@dataclass
class WmsLayerFeatureRequestBody:
    """
    The request body passed from frontend to backend for querying WMS layers features.
    """
    ev_lat_lng: MouseEventLatLng
    """Geographical LatLng property of the Leaflet MouseClick event"""
    layers: List[WmsLayerRequestInfo]
    """List of WmsLayerRequestInfo used for querying WMS layers features"""

@dataclass
class LayerFeaturePropsResp:
    """
    Layer feature properties response
    """
    name: str
    """Layer name"""
    feature_props: Optional[Dict]
    """Layer feature properties in dictionary. None is returned when the request is not successful."""

@dataclass
class WmsLayerFeatureResp:
    """
    The response passed from backend to frontend after receiving WMS layers features properties.
    """
    ev_lat_lng: MouseEventLatLng
    """Geographical LatLng property of the Leaflet MouseClick event"""
    layers_features_props: List[LayerFeaturePropsResp]
    """List of WMS layers features properties query response dictionary"""

@dataclass
class WmsGetCapabilitiesRequestBody:
    """
    The request body passed from the frontend to the backend for fetching WMS GetCapabilities.
    """
    url: str
    """WMS service URL"""

@dataclass
class WmsServiceLayerInfo:
    """
    The extracted layer information required by the frontend from the requested WMS service.
    """
    name: str
    """Layer name"""
    title: str
    """Layer title"""
    legend_url: str
    """Layer legend URL"""

@dataclass
class WmsGetCapabilitiesResp:
    """
    The response of the WMS GetCapabilities request passed from the backend to the frontend.
    """
    success: bool
    """WMS GetCapabilities request is successful or not"""
    result: Union[List[WmsServiceLayerInfo], str]
    """If successful, a list of WmsServiceLayerInfo is returned; Otherwise, an error message is returned"""