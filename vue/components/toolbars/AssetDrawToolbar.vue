<template>
  <div
    v-if="!isLoading"
    v-show="showAssetDrawToolbar"
    class="my-control leaflet-asset-draw-toolbar"
  >
    <table class="asset-table">
      <tr>
        <template v-for="(capabilityList, capability) in assetList" :key="capability">
          <td v-for="asset in capabilityList" :key="asset">
            <div :title="asset" :class="'circle '+capability" @click="buttonClick(asset)">
              <div class="image-div" style="font-size:0px">
                <img class="circle-img" :src="'images/' + asset + '.png'">
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
      isLoading: true
    };
  },
  mounted() {
    this.getAssetList();
  },
  methods: {
    getAssetList: function() {
      console.log('getAssetList');
      const path = '/DLA_get_asset_toolbar_list';
      axios.get(path)
        .then((res) => {
          console.log(res);
          this.assetList = res["data"]["asset_list"];
          this.isLoading = false;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    buttonClick: function(assetName) {
      var marker_class_name = window[assetName+ "Marker"];
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

      console.log('Button');
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

.asset-table tr td {
   width: 40px;
   height: 40px;
   text-align: center;
   padding: 20px 0px 0px 20px;
}

</style>
