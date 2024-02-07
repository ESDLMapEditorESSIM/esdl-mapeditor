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

    <div>
      <h3>Filter asset list on type:</h3>
      <a-select
        v-model:value="selected_asset_type"
        :options="asset_type_list"
        show-search
        option-filter-prop="label"
        :filter-option="filter_asset_type"
        placeholder="Filter EDR assets on..."
        style="width: 100%"
        @popupScroll="hide_jquery_ui_popup()"
      />
    </div>

    <div>
      <h3>Select asset:</h3>
      <a-select
        v-model:value="selected_asset"
        :options="filtered_asset_list"
        show-search
        option-filter-prop="label"
        :filter-option="filter_asset"
        placeholder="Select an asset from the EDR"
        style="width: 100%"
        @popupScroll="hide_jquery_ui_popup()"
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
</template>

<script>
import axios from 'axios'

export default {
  components: {
  },
  data() {
    return {
      asset_list: [],
      selected_asset: undefined,
      asset_type_list: [],
      selected_asset_type: undefined,
      isLoading: true
    }
  },
  computed: {
    filtered_asset_list: function() {
      if (this.selected_asset_type != 'No filter' && this.selected_asset_type != undefined) {
        return this.asset_list.filter(item => item.item_type == this.selected_asset_type);
      } else {
        return this.asset_list;
      }
    }
  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    getDataSocketIO: function() {
      // console.log(currentObjectID.value);
      // window.socket.emit('edr_assets', (res) => {
      const path = '/edr_assets';
      axios.get(path)
        .then((res) => {
          this.asset_list = res['data']['item_list'];
          const asset_types = ['No filter'].concat(res['data']['item_type_list']);
          this.asset_type_list = asset_types.map((asset_type) => {
            return {
              label: asset_type,
              value: asset_type,
            }
          });
          this.isLoading = false;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    select: function() {
      const selected_value = this.selected_asset;
      if (selected_value) {
        window.socket.emit('command', {cmd: 'get_edr_asset', edr_asset_id: selected_value});
        window.sidebar.hide();
      }
    },
    cancel: function() {
      window.sidebar.hide();
    },
    filter_asset_type: function(input, option) {
      return option.props.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    },
    filter_asset: function(input, option) {
      return option.props.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    },
    buildResultInfo: function() {
      let result = {};
      return result;
    },
    hide_jquery_ui_popup: function() {
      $(".ui-tooltip-content").parents('div').remove();
    },
  }
};
</script>
