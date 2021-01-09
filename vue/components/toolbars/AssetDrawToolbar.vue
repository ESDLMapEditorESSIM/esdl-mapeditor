<template>
  <div
    v-if="!isLoading"
    v-show="showAssetDrawToolbar"
    class="my-control leaflet-asset-draw-toolbar"
  >
    <table class="asset-table">
      <tr>
        <template v-for="(capabilityList, capability) in assetList" :key="capability">
          <td v-for="asset in capabilityList" :key="asset" class="icon">
            <div :title="asset" :class="'circle '+capability" @click="buttonClick(asset)">
              <div class="image-div" style="font-size:0px">
                <img class="circle-img" :src="'images/' + asset + '.png'">
              </div>
            </div>
          </td>
        </template>
        <template v-if="recentEDRassets && recentEDRassets.length">
          <td>Recent EDR: </td>
          <td v-for="asset in recentEDRassets" :key="asset.edr_asset_id" class="icon">
            <div :title="asset.edr_asset_name" :class="'circle '+asset.edr_asset_cap" @click="buttonEDRClick(asset)">
              <div class="image-div" style="font-size:0px">
                <img class="circle-img" :src="'images/' + asset.edr_asset_type + '.png'">
              </div>
            </div>
          </td>
        </template>
      </tr>
    </table>
  </div>
</template>

<script>
import axios from 'axios';
import { useAssetDrawToolbar } from "../../composables/assetDrawToolbar.js";

const { showAssetDrawToolbar, toggleShowAssetDrawToolbar } = useAssetDrawToolbar();

export default {
  name: "AssetDrawToolbar",
  setup() {
    return {
      showAssetDrawToolbar,
      toggleShowAssetDrawToolbar
    }
  },
  data() {
    return {
      assetList: [],
      recentEDRassets: [],
      isLoading: true
    };
  },
  mounted() {
    this.getAssetList();
    window.addEventListener('load', () => {
      // run after everything is in-place
      window.socket.on('recently_used_edr_assets', function(res) {
        this.recentEDRassets = res;
      });
    })
  },
  methods: {
    getAssetList: function() {
      console.log('getAssetList');
      const path = '/DLA_get_asset_toolbar_info';
      axios.get(path)
        .then((res) => {
          // console.log(res);
          this.assetList = res["data"]["assets_per_cap_dict"];
          this.recentEDRassets = res["data"]["recent_edr_assets"];
          this.isLoading = false;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    startDrawing: function(assetName) {
      var marker_class_name = window[assetName+ "Marker"];
      if (assetName == 'Pipe' || assetName == 'ElectricityCable')
        window.update_line_asset_menu(assetName);
      else
        window.update_asset_menu(assetName);

      window.remove_tooltip();

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
    },
    buttonClick: function(assetName) {
      window.socket.emit('command', {
        'cmd': 'set_asset_drawing_mode',
        'mode': 'empty_assets'
      });
      this.startDrawing(assetName);   // communicate the ESDL class of the clicked asset

    },
    buttonEDRClick: function(asset) {
      window.socket.emit('command', {
        'cmd': 'set_asset_drawing_mode',
        'mode': 'edr_asset',
        'edr_asset_info': asset
      });
      this.startDrawing(asset.edr_asset_type);   // communicate the ESDL class of the clicked EDR asset
    }
  },
};
</script>

<style>
.leaflet-asset-draw-toolbar {
    padding: 5px;
    z-index: 2000;
    height: 50px;
    background: white;

    box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
    border-radius: 5px;
}
to
.leaflet-asset-draw-toolbar p {
  margin-bottom: 0;
}

.asset-table tr td.icon {
   width: 40px;
   height: 40px;
   text-align: center;
   padding: 20px 0px 0px 20px;
}

</style>
