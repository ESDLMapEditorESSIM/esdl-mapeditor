<template>
  <h1>Asset Draw Toolbar - EDR assets</h1>
  <p>
    Select the assets from the Energy Data Repository that you want to add to your Asset Draw Toolbar
  </p>
  <a-space
    direction="vertical"
  >
    <a-transfer
      v-if="!isLoading"
      :data-source="EDRAssets"
      :titles="['EDR Assets', 'Available at Asset Draw Toolbar']"
      :list-style="{
        width: '400px',
        height: '300px',
      }"
      :target-keys="targetKeys"
      :selected-keys="selectedKeys"
      :render="item => `${item.label} (${item.asset_type})`"
      :row-key="item => item.value"
      @change="handleChange"
      @selectChange="handleSelectChange"
    />
    <spinner v-else />
    <a-button
      type="primary"
      @click="saveEDRAssets"
    >
      Save
    </a-button>
  </a-space>
</template>

<script>
import { ref } from 'vue';
import spinner from "../Spinner.vue";
import axios from 'axios';

const EDRAssets = ref([]);
const targetKeys = ref([]);

export default {
  name: "AssetDrawToolbarEDRAssetsSettings",
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

    const saveEDRAssets = () => {
      // console.log(targetKeys.value);
      let edr_asset_list = [];
      for (let i=0; i<targetKeys.value.length; i++) {
        for (let j=0; j<EDRAssets.value.length; j++) {
          if (targetKeys.value[i] == EDRAssets.value[j].value) {
            let item = {
              edr_asset_id: EDRAssets.value[j].value,
              edr_asset_name: EDRAssets.value[j].label,
              edr_asset_type: EDRAssets.value[j].asset_type,
            };
            edr_asset_list.push(item);
            break;
          }
        }
      }
      // console.log(edr_asset_list);
      window.socket.emit('save_asset_draw_toolbar_edr_assets', edr_asset_list);
    };

    return {
      isLoading,
      EDRAssets,
      targetKeys,
      selectedKeys,
      handleChange,
      handleSelectChange,
      saveEDRAssets,
    };
  },
  mounted() {
    this.getEDRAssets();
  },
  methods: {
    getEDRAssets: function() {
      const path = '/edr_assets';
      axios.get(path)
        .then((res) => {
          // console.log(res);
          for (let i=0; i<res['data']['asset_list'].length; i++) {
            res['data']['asset_list'][i].key = res['data']['asset_list'][i].value;
            res['data']['asset_list'][i].title = res['data']['asset_list'][i].label;
          }
          EDRAssets.value = res['data']['asset_list'];

          window.socket.emit('load_asset_draw_toolbar_edr_assets', (edr_assets) => {
            for (let i=0; i<edr_assets.length; i++) {
              targetKeys.value.push(edr_assets[i].edr_asset_id);
            }
            this.isLoading = false;
          });
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
  }
};
</script>

<style>
</style>
