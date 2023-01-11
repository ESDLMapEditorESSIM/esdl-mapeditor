<template>
  <h1>Asset Draw Toolbar - Standard assets</h1>
  <p>
    Select the assets that you want to add to your Asset Draw Toolbar
  </p>
  <a-space
    direction="vertical"
  >
    <a-select
      v-model:value="currentViewMode"
      :options="possibleViewModes"
      @change="selectViewMode"
    />
    <a-transfer
      v-if="!isLoading"
      :data-source="standardAssets"
      :titles="['Standard Assets', 'Available at Asset Draw Toolbar']"
      :list-style="{
        width: '400px',
        height: '300px',
      }"
      :target-keys="targetKeys"
      :selected-keys="selectedKeys"
      :render="item => `${item.asset_cap}: ${item.asset_type}`"
      :row-key="item => item.id"
      @change="handleChange"
      @selectChange="handleSelectChange"
    />
    <spinner v-else />
    <a-button
      type="primary"
      @click="saveStandardAssets"
    >
      Save
    </a-button>
  </a-space>
</template>

<script>
import { ref } from 'vue';
import spinner from "../Spinner.vue";

const standardAssetsInfo = ref({});
const standardAssets = ref([]);
const targetKeys = ref([]);
const currentViewMode = ref();
const possibleViewModes = ref([]);

export default {
  name: "AssetDrawToolbarStandardAssetsSettings",
  components: {
    spinner
  },
  data() {
    const isLoading = ref(true);
    const selectedKeys = ref([]);

    const handleChange = (nextTargetKeys) => {
      targetKeys.value = nextTargetKeys;
    };

    const handleSelectChange = (sourceSelectedKeys, targetSelectedKeys) => {
      selectedKeys.value = [...sourceSelectedKeys, ...targetSelectedKeys];
    };

    const saveStandardAssets = () => {
      // console.log(targetKeys.value);
      let standard_asset_list = standardAssetsInfo.value['standard_assets'];
      standard_asset_list[currentViewMode.value] = {};
      for (let i=0; i<targetKeys.value.length; i++) {
        for (let j=0; j<standardAssets.value.length; j++) {
          if (targetKeys.value[i] == standardAssets.value[j].id) {
            if (!(standardAssets.value[j].asset_cap in standard_asset_list[currentViewMode.value])) {
              standard_asset_list[currentViewMode.value][standardAssets.value[j].asset_cap] = [];
            }
            standard_asset_list[currentViewMode.value][standardAssets.value[j].asset_cap].push(standardAssets.value[j].id);
            break;
          }
        }
      }
      // console.log(standard_asset_list);
      window.socket.emit('save_asset_draw_toolbar_standard_assets', standard_asset_list);
    };

    return {
      isLoading,
      standardAssets,
      targetKeys,
      selectedKeys,
      handleChange,
      handleSelectChange,
      saveStandardAssets,
      currentViewMode,
      possibleViewModes,
    };
  },
  mounted() {
    this.getStandardAssets();
  },
  methods: {
    getStandardAssets: function() {
      standardAssets.value = this.createTransferDataStructure(window.cap_pot_list['capabilities']);

      window.socket.emit('load_asset_draw_toolbar_standard_assets_info', (standard_assets_info) => {
        standardAssetsInfo.value = standard_assets_info;
        currentViewMode.value = standard_assets_info['current_mode'];
        possibleViewModes.value = standard_assets_info['possible_modes'].map((item) => {
          return {
            value: item,
            label: item,
          }
        });

        let standard_assets = standard_assets_info['standard_assets'][currentViewMode.value];
        for (const [cap_type, asset_list] of Object.entries(standard_assets)) {
          for (let i=0; i<asset_list.length; i++) {
            targetKeys.value.push(asset_list[i]);
          }
        }
        this.isLoading = false;
      });
    },
    createTransferDataStructure: function(cpdict) {
      let transfer_ds = [];
      // console.log(cpdict);
      for (const [cap_type, asset_list] of Object.entries(cpdict)) {
        for (let i=0; i<asset_list.length; i++) {
          let item = {
            id: asset_list[i],
            key: asset_list[i],
            title: asset_list[i],
            asset_type: asset_list[i],
            asset_cap: cap_type,
          };
          transfer_ds.push(item);
        }
      }
      // console.log(transfer_ds);
      return transfer_ds
    },
    selectViewMode: function(view_mode) {
      let standard_assets = standardAssetsInfo.value['standard_assets'][view_mode];
      targetKeys.value = [];
      for (const [cap_type, asset_list] of Object.entries(standard_assets)) {
        for (let i=0; i<asset_list.length; i++) {
          targetKeys.value.push(asset_list[i]);
        }
      }
    }
  }
};
</script>

<style>
</style>
