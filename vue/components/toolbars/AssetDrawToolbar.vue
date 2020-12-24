Ini<template>
  <div v-show="showAssetDrawToolbar" class="my-control leaflet-asset-draw-toolbar">
    <h1>Assets</h1>
    <button @click="buttonClick('PVInstallation')">PVInstallation</button>
    <div class="circle Producer" />
  </div>
</template>

<script>
import { useAssetDrawToolbar } from "../../composables/assetDrawToolbar.js";

export default {
  name: "AssetDrawToolbar",
  setup() {
    const { showAssetDrawToolbar, toggleShowAssetDrawToolbar, } = useAssetDrawToolbar();

    function buttonClick(assetName) {
      var marker_class_name = window[assetName+ "Marker"];

      window.draw_control.setDrawingOptions({
          marker: {
              icon: new marker_class_name()
          }
      });

      var line_assets = ["ElectricityCable", "Pipe"];
      var area_assets = ["Area", "PVPark", "WindPark"];
      if (line_assets.includes(assetName)) {
          window.draw_control._toolbars.draw._modes.polyline.handler.enable();
      } else if (area_assets.includes(assetName)) {
          window.socket.emit('command', {'cmd': 'set_area_drawing_mode', 'mode': 'asset_with_polygon'});
          window.draw_control._toolbars.draw._modes.polygon.handler.enable();
      } else {
          window.draw_control._toolbars.draw._modes.marker.handler.enable();
      }

      console.log('Button');
    }

    return {
      buttonClick,
      showAssetDrawToolbar,
      toggleShowAssetDrawToolbar,
    };
  }
};
</script>

<style>
.leaflet-asset-draw-toolbar {
    padding: 10px;
    z-index: 2000;
    width: 500px;
    height: 120px;
    background: white;

    box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
    border-radius: 5px;
}

.leaflet-asset-draw-toolbar p {
  margin-bottom: 0;
}
</style>
