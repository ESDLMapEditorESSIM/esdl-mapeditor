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
        show-search
        option-filter-prop="children"
        :filter-option="filter_asset_type"
        placeholder="Filter EDR assets on..."
        style="width: 100%"
      >
        <a-select-option
          v-for="at in asset_type_list"
          :key="at"
        >
          {{ at }}
        </a-select-option>
      </a-select>
    </div>

    <div>
      <h3>Select asset:</h3>
      <a-select
        v-model:value="selected_asset"
        show-search
        option-filter-prop="children"
        :filter-option="filter_asset"
        placeholder="Select an asset from the EDR"
        style="width: 100%"
      >
        <a-select-option
          v-for="asset in filtered_asset_list"
          :value="asset.id"
          :key="asset.id"
          :title="asset.title"
        >
          {{ asset.title }}
        </a-select-option>
      </a-select>
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
  mounted() {
    this.getDataSocketIO();
  },
  computed: {
    filtered_asset_list: function() {
      if (this.selected_asset_type != 'No filter' && this.selected_asset_type != undefined) {
        return this.asset_list.filter(item => item.asset_type == this.selected_asset_type);
      } else {
        return this.asset_list;
      }
    }
  },
  methods: {
    getDataSocketIO: function() {
      // console.log(currentObjectID.value);
      // window.socket.emit('edr_assets', (res) => {
      const path = '/edr_assets';
      axios.get(path)
        .then((res) => {
          this.asset_list = res['data']['asset_list'];
          this.asset_type_list = ['No filter'].concat(res['data']['asset_type_list']);
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
      return option.props.key.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    },
    filter_asset: function(input, option) {
      return option.props.title.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    },
    buildResultInfo: function() {
      let result = {};
      return result;
    },
  }
};
</script>
