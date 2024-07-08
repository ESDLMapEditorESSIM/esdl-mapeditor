from dataclasses import dataclass
from typing import Dict, List, Optional

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