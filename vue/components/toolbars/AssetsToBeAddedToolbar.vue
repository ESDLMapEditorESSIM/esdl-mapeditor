<template>
  <div
    v-show="assetList && assetList.length"
    class="my-control leaflet-assets-to-be-added-toolbar"
  >
    <p>Assets to be added:</p>
    <table class="asset-table">
      <tr>
        <td v-for="asset in assetList" :key="asset.id" class="icon">
          <div :title="asset.type" :class="'circle '+asset.cap" @click="buttonClick(asset)">
            <div class="image-div" style="font-size:0px">
              <img class="circle-img" :src="'images/' + asset.type + '.png'">
            </div>
          </div>
          <span class="badge">{{ asset.count }}</span>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>
import { ref } from 'vue';

const assetList = ref([]);
const visible = ref(true);

export default {
  name: "AssetsToBeAddedToolbar",
  setup() {
    return {
      assetList,
      visible,
    };
  },
  mounted() {
    window.addEventListener('load', () => {
      // run after everything is in-place
      window.socket.on('ATBA_assets_to_be_added', function(res) {
        console.log(res);
        assetList.value = res['assets_to_be_added'];
      });
      window.socket.on('ATBA_use_asset', function(info) {
        console.log(info);
        let asset_id = info['id'];
        for (let idx in assetList.value) {
          if (assetList.value[idx].id == asset_id) {
            assetList.value[idx].count -= 1;
            if (assetList.value[idx].count == 0) {
              assetList.value.splice(idx, 1);
            }
          }
        }
      });
    });
  },
  methods: {
    startDrawing: function(assetName) {
      var marker_class_name = window[assetName+ "Marker"];
      if (assetName == 'Pipe' || assetName == 'ElectricityCable')
        window.update_line_asset_menu(assetName);
      else
        window.update_asset_menu(assetName);

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
    buttonClick: function(asset) {
      if (asset.count > 0) {
        window.socket.emit('command', {
          'cmd': 'set_asset_drawing_mode',
          'mode': 'asset_from_measures',
          'asset_from_measure_id': asset.id
        });
        this.startDrawing(asset.type);   // communicate the ESDL class of the clicked asset
      }
    },
  },
};
</script>

<style>
.leaflet-assets-to-be-added-toolbar {
    padding: 5px;
    z-index: 2000;
    height: 70px;
    background: white;

    box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
    border-radius: 5px;
}

.leaflet-assets-to-be-added-toolbar p {
  margin-bottom: 0;
}

.leaflet-assets-to-be-added-toolbar .asset-table tr td.icon {
   width: 60px;
   height: 40px;
   text-align: center;
   padding: 20px 0px 0px 20px;
}

.badge {
  width: 20px;
  height: 20px;
  background-color: red;
  border-radius: 50%;
  color: white;
  position: relative;
  top: -40px;
  right: -5px;
  display: flex;
  justify-content: center;
  align-items: center;
}

</style>
