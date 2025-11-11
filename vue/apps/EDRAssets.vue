<!--
  - This work is based on original code developed and copyrighted by TNO 2020.
  - Subsequent contributions are licensed to you by the developers of such code and are
  - made available to the Project under one or several contributor license agreements.
  -
  - This work is licensed to you under the Apache License, Version 2.0.
  - You may obtain a copy of the license at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Contributors:
  -     TNO         - Initial implementation
  - Manager:
  -     TNO
  -->

<template>
  <h1>
    EDR Assets
  </h1>
  <a-space
    v-if="!isLoading"
    id="edr_assets"
    direction="vertical"
    style="width: 100%"
  >
    <a-card style="width: 100%">
      <p>
        The EDR (Energy Data Repository) contains standard ESDL asset descriptions that can be shared between models.
        Please visit the <a href="https://edr.hesi.energy" target="#">EDR website</a> for more information and to browse
        the contents of the EDR
      </p>
    </a-card>

    <a-space direction="horizontal">
      <a-checkbox
        v-model:checked="filter_status_experimental"
        @change="e => filterOnExperimental(e)"
      >
        Status:Experimental
      </a-checkbox>
      <a-checkbox
        v-model:checked="filter_status_final"
        @change="e => filterOnFinal(e)"
      >
        Status:Final
      </a-checkbox>
    </a-space>

    <a-space direction="horizontal">
      <a-checkbox
        v-model:checked="filter_cost_information"
      >
        esdl:CostInformation
      </a-checkbox>
      <a-checkbox
        v-model:checked="filter_input_output_relation"
      >
        esdl:InputOutputRelation
      </a-checkbox>
    </a-space>

    <div>
      <h3>Filter asset list on EDR asset category:</h3>
      <a-select
        v-model:value="selected_asset_category"
        :options="asset_categories"
        show-search
        option-filter-prop="label"
        :filter-option="filter_select"
        placeholder="Filter EDR assets on..."
        style="width: 100%"
        @popup-scroll="hide_jquery_ui_popup()"
      />
    </div>
    <div>
      <h3>Filter asset list on type:</h3>
      <a-select
        v-model:value="selected_asset_type"
        :options="asset_type_list"
        :disabled="!allow_selection_of_asset_type"
        show-search
        option-filter-prop="label"
        :filter-option="filter_select"
        placeholder="Filter EDR assets on..."
        style="width: 100%"
        @popup-scroll="hide_jquery_ui_popup()"
      />
    </div>

    <div>
      <h3>Select asset:</h3>
      <a-select
        v-model:value="selected_asset"
        :options="filtered_asset_list"
        show-search
        option-filter-prop="label"
        :filter-option="filter_select"
        placeholder="Select an asset from the EDR"
        style="width: 100%"
        @popup-scroll="hide_jquery_ui_popup()"
      />
    </div>

    <a-space>
      <a-button
        type="primary"
        @click="select"
      >
        Select
      </a-button>
      <a-button
        type="primary"
        @click="cancel"
      >
        Cancel
      </a-button>
    </a-space>
  </a-space>
  <template v-else>
    <span>Loading EDR data...</span>
    <spinner />
  </template>
</template>

<script>
import axios from 'axios'
import {useReplaceEDRAsset} from "@/composables/replaceEDRAsset";
import spinner from "@/components/Spinner.vue";

const { assetIdList, assetClass } = useReplaceEDRAsset();

export default {
  components: {
    spinner,
  },
  data() {
    return {
      asset_list: [],
      selected_asset: undefined,
      asset_type_list: [],
      asset_categories: [],
      selected_asset_category: undefined,
      selected_asset_type: undefined,
      isLoading: true,
      filter_status_experimental: false,
      filter_status_final: true,
      filter_cost_information: false,
      filter_input_output_relation: false,
      allow_selection_of_asset_type: true,
    }
  },
  computed: {
    filtered_asset_list: function() {
      let temp_list = [...this.asset_list];
      if (this.selected_asset_type !== 'No filter' && this.selected_asset_type !== undefined) {
        temp_list = temp_list.filter(item => item.item_type === this.selected_asset_type);
      }
      if (this.selected_asset_category !== 'No filter' && this.selected_asset_category !== undefined) {
        temp_list = temp_list.filter(item => item.edr_cat === this.selected_asset_category);
      }
      if (this.filter_status_experimental) {
        temp_list = temp_list.filter(item => (item.tags.includes("status:Experimental")));
      }
      if (this.filter_status_final) {
        temp_list = temp_list.filter(item => (item.tags.includes("status:Final")));
      }
      if (this.filter_cost_information) {
        temp_list = temp_list.filter(item => (item.tags.includes("esdl:CostInformation")));
      }
      if (this.filter_input_output_relation) {
        temp_list = temp_list.filter(item => (item.tags.includes("esdl:InputOutputRelation")));
      }
      return temp_list;
    }
  },
  mounted() {
    this.getDataSocketIO();

    if (assetIdList.value !== undefined && assetClass.value !== undefined) {
      this.selected_asset_type = assetClass.value;
      this.allow_selection_of_asset_type = false;
    }
  },
  methods: {
    getDataSocketIO: function () {
      // console.log(currentObjectID.value);
      // window.socket.emit('edr_assets', (res) => {
      let path = '/edr_assets';
      if (assetIdList.value !== undefined && assetClass.value !== undefined) {
        path = path + "/" + assetClass.value;
      }
      axios.get(path)
        .then((res) => {
          this.asset_list = res['data']['item_list'];
          const cat_list = ['No filter'].concat(res['data']['edr_cat_list']);
          const asset_types = ['No filter'].concat(res['data']['item_type_list']);
          // Create a list that can directly be used by the Antdv Select component
          this.asset_type_list = asset_types.map((asset_type) => {
            return {
              label: asset_type,
              value: asset_type,
            }
          });
          // Create a list that can be used by the Antdv Select component
          this.asset_categories = cat_list.map((cat) => {
            return {label: cat, value: cat};
          });
          this.isLoading = false;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    clear_replace_asset_info: function () {
      // clear values for next check (could be a regular "get asset from EDR" request)
      assetIdList.value = null;
      assetClass.value = null;
    },
    select: function () {
      const selected_value = this.selected_asset;
      if (selected_value) {
        if (assetIdList.value !== undefined && assetClass.value !== undefined) {
          // replace with EDR asset was choosen

          for (let idx=0; idx<assetIdList.value.length; idx++) {
            let asset_id = assetIdList.value[idx];
            let asset = find_layer_by_id(active_layer_id, 'esdl_layer', asset_id);
            console.log(asset);

            window.socket.emit('command', {
              cmd: 'replace_edr_asset',
              original_asset_id: asset_id,
              edr_asset_id: selected_value
            });
          }
          this.clear_replace_asset_info();
        } else {
          window.socket.emit('command', {cmd: 'get_edr_asset', edr_asset_id: selected_value});
        }
        window.sidebar.hide();
      }
    },
    cancel: function () {
      this.clear_replace_asset_info();
      window.sidebar.hide();
    },
    filter_select: function (input, option) {
      return option.props.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    },
    buildResultInfo: function () {
      let result = {};
      return result;
    },
    hide_jquery_ui_popup: function () {
      window.jquery(".ui-tooltip-content").parents('div').remove();
    },
    filterOnExperimental: function (e) {
      // The tags experimental and final should be mutually exclusive
      // If experimental is checked, uncheck final
      if (e.target.checked) {
        this.filter_status_final = false;
      }
    },
    filterOnFinal: function (e) {
      // The tags experimental and final should be mutually exclusive
      // If final is checked, uncheck experimental
      if (e.target.checked) {
        this.filter_status_experimental = false;
      }
    },
  }
};
</script>
