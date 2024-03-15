const startDrawMarkerAsset = (asset_name) => {
  var marker_class_name = window[asset_name + "Marker"];
  window.update_asset_menu(asset_name);
  window.remove_tooltip();

  // Disable the leaflet draw toolbars, such that the shown icon can be updated
  window.draw_control._toolbars.draw._modes.polyline.handler.disable();
  window.draw_control._toolbars.draw._modes.polygon.handler.disable();
  window.draw_control._toolbars.draw._modes.marker.handler.disable();

  window.draw_control.setDrawingOptions({
      marker: {
          icon: new marker_class_name()
      }
  });

  window.draw_control._toolbars.draw._modes.marker.handler.enable();

}
window.startDrawMarkerAsset = startDrawMarkerAsset;