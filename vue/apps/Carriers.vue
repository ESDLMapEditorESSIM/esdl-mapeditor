<template>
  <h1>
    Energy Carriers and Commodities
  </h1>
  <a-space
    v-if="!isLoading"
    id="carriers"
    direction="vertical"
    style="width: 100%"
  >
    <a-table
      :columns="carrierColumns"
      :data-source="carrier_list"
      :row-key="(record, index) => {return record.id;}"
      size="middle"
      :pagination="paginationConfig"
      style="width: 100%"
    >
      <template #operation="{ record }">
        <div class="editable-row-operations">
          <a-space>
            <a @click="deleteCarrier(record.id)">
              <i class="fa fa-trash" />
            </a>
            <a @click="editCarrier(record.id)">
              <i class="fa fa-edit" />
            </a>
          </a-space>
        </div>
      </template>
      <template #color_select="{ record }">
        <span>
          <input
            type="color"
            :value="record.color"
            @change="e => changeColor(record.id, e.target.value)"
          >
        </span>
      </template>
    </a-table>
    <a-card style="width: 100%">
      <a-space
        direction="vertical"
        style="width: 100%"
      >
        <!------------------------------------>
        <!-- Carrier type                   -->
        <!------------------------------------>
        <a-row :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Carrier type</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edit_carrier.type"
              style="width: 100%"
              :options="carrier_types"
              @change="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Name                           -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type != 'None'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Name</span>
          </a-col>
          <a-col :span="15">
            <a-input
              v-model:value="edit_carrier.name"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Emission                       -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'EnergyCarrier'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Emission [kg/GJ]</span>
          </a-col>
          <a-col :span="15">
            <FancyNumberEdit
              v-model:value="edit_carrier.emission"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Energy Content                 -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'EnergyCarrier'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Energy content</span>
          </a-col>
          <a-col :span="15">
            <FancyNumberEdit
              v-model:value="edit_carrier.energy_content"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Energy Content Unit            -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'EnergyCarrier'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Energy content unit</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edit_carrier.energy_content_unit"
              style="width: 100%"
              :options="energy_content_units"
              @change="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- State of Matter                -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'EnergyCarrier'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>State of Matter</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edit_carrier.state_of_matter"
              style="width: 100%"
              :options="state_of_matters"
              @change="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Renewable type                 -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'EnergyCarrier'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Renewable type</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edit_carrier.renewable_type"
              style="width: 100%"
              :options="renewable_types"
              @change="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Voltage                        -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'ElectricityCommodity'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Voltage</span>
          </a-col>
          <a-col :span="15">
            <FancyNumberEdit
              v-model:value="edit_carrier.voltage"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Pressure                       -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'GasCommodity'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Pressure</span>
          </a-col>
          <a-col :span="15">
            <FancyNumberEdit
              v-model:value="edit_carrier.pressure"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Supply temperature             -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'HeatCommodity'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Supply temperature</span>
          </a-col>
          <a-col :span="15">
            <FancyNumberEdit
              v-model:value="edit_carrier.supply_temperature"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Return temperature             -->
        <!------------------------------------>
        <a-row v-if="edit_carrier.type == 'HeatCommodity'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Return temperature</span>
          </a-col>
          <a-col :span="15">
            <FancyNumberEdit
              v-model:value="edit_carrier.return_temperature"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <a-row v-if="edit_carrier.type != 'None'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Carrier cost</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edit_carrier.cost_sort"
              style="width: 100%"
              :options="cost_sorts"
              @change="value_changed"
            />
          </a-col>
        </a-row>

        <a-row v-if="edit_carrier.cost_sort == 'SingleValue'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Value</span>
          </a-col>
          <a-col :span="15">
            <FancyNumberEdit
              v-model:value="edit_carrier.cost_value"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <a-row v-if="edit_carrier.cost_sort == 'Profile'" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Profile</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edit_carrier.cost_profile"
              show-search
              style="width: 100%"
              :options="profiles_options"
              @change="value_changed"
            />
          </a-col>
        </a-row>

        <a-row v-if="edit_carrier.cost_sort != undefined" :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Unit</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edit_carrier.cost_unit"
              show-search
              placeholder="Please select a unit..."
              style="width: 100%"
              :options="cost_units"
              @change="value_changed"
            />
          </a-col>
        </a-row>

        <a-space>
          <a-button
            :disabled="!edit_carrier_changed"
            @click="addCarrier"
          >
            Add
          </a-button>
          <a-button
            :disabled="!(edit_carrier_changed && edit_carrier.id != '')"
            @click="saveCarrier"
          >
            Save
          </a-button>
          <a-button
            :disabled="edit_carrier.id == ''"
            @click="cancelEditCarrier"
          >
            Cancel
          </a-button>
        </a-space>
      </a-space>
    </a-card>
    <a-card
      v-if="edr_carriers_list"
      style="width: 100%"
    >
      <a-space
        direction="vertical"
        style="width: 100%"
      >
        <a-row :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>EDR Carriers</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edr_carriers"
              style="width: 100%"
              :options="edr_carriers_list"
            />
          </a-col>
        </a-row>
        <a-space>
          <a-button
            :disabled="edr_carriers == undefined"
            @click="addEDRCarriers"
          >
            Add
          </a-button>
        </a-space>
      </a-space>
    </a-card>
  </a-space>
</template>

<script>
import FancyNumberEdit from "../components/forms/FancyNumberEdit"
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';

const carrierColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', dataIndex: 'type', key: 'type' },
  { title: 'Color', slots: { customRender: 'color_select' }},
  { title: '', slots: { customRender: 'operation' }},
];

const paginationConfig = { hideOnSinglePage: true };

export default {
  components: {
    FancyNumberEdit,
  },
  data() {
    return {
      isLoading: true,
      carrierColumns,
      paginationConfig,
      carrier_list: [],
      carrier_info_mapping: {},

      carrier_types: [
        {label: 'No Carrier selected', value: 'None'},
        {label: 'Energy carrier', value: 'EnergyCarrier'},
        {label: 'Electricity Commodity', value: 'ElectricityCommodity'},
        {label: 'Gas Commodity', value: 'GasCommodity'},
        {label: 'Heat Commodity', value: 'HeatCommodity'},
        {label: 'EnergyCommodity', value: 'EnergyCommodity'},
      ],
      renewable_types: [
        {label: 'Undefined', value: 'Undefined'},
        {label: 'Fossil', value: 'Fossil'},
        {label: 'Renewable', value: 'Renewable'},
      ],
      state_of_matters: [
        {label: 'Undefined', value: 'Undefined'},
        {label: 'Solid', value: 'Solid'},
        {label: 'Liquid', value: 'Liquid'},
        {label: 'Gaseous', value: 'Gaseous'},
      ],
      energy_content_units: [
        {label: 'Please select...', value: 'Undefined'},
        {label: 'MJ/kg', value: 'MJ/kg'},
        {label: 'MJ/Nm3', value: 'MJ/m3'},
        {label: 'MJ/MJ', value: 'MJ/MJ'},
      ],
      cost_sorts: [
        {label: 'Please select...', value: 'Undefined'},
        {label: 'Single value', value: 'SingleValue'},
        {label: 'Profile', value: 'Profile'},
      ],
      cost_profiles: [
        {label: 'Please select...', value: 'Undefined'},
      ],
      // For the time being a fixed list of possible options
      cost_units: [
        { value: '', label: "Please select a unit..."},
        { value: 'EUR', label: "EUR"},
        { value: 'EUR/Wh', label: "EUR/Wh"},
        { value: 'EUR/kWh', label: "EUR/kWh"},
        { value: 'EUR/MWh', label: "EUR/MWh"},
        { value: 'EUR/GWh', label: "EUR/GWh"},
        { value: 'EUR/TWh', label: "EUR/TWh"},
        { value: 'EUR/J', label: "EUR/J"},
        { value: 'EUR/kJ', label: "EUR/kJ"},
        { value: 'EUR/MJ', label: "EUR/MJ"},
        { value: 'EUR/GJ', label: "EUR/GJ"},
        { value: 'EUR/TJ', label: "EUR/TJ"},
        { value: 'EUR/m3', label: "EUR/m3"},
      ],

      clear_inputs: false,
      edit_carrier_changed: false,
      edit_carrier: {
        id: '',
        name: '',
        type: 'None',
        emission: undefined,
        energy_content: undefined,
        energy_content_unit: 'Undefined',

        state_of_matter: 'Undefined',
        renewable_type: 'Undefined',
        voltage : undefined,
        pressure: undefined,
        supply_temperature: undefined,
        return_temperature: undefined,
        cost_sort: undefined,
        cost_value: undefined,
        cost_profile: undefined,
        cost_unit: undefined,
      },
      profiles_options: [],

      edr_carriers_list: undefined,
      edr_carriers: undefined,
    }
  },
  computed: {
  },
  mounted() {
    this.getData();
    this.getEDRCarriersList();
  },
  methods: {
    getData: function() {
      this.carrier_list = window.get_carrier_list(window.active_layer_id);
      this.carrier_info_mapping = window.get_carrier_info_mapping(window.active_layer_id);
      for (let i=0; i<this.carrier_list.length; i++) {
        this.carrier_list[i]['color'] = this.carrier_info_mapping[this.carrier_list[i]['id']]['color'];
      }
      let profiles_list = window.profiles_plugin.profiles_list;
      console.log(profiles_list);
      let profiles = Object.entries(window.profiles_plugin.profiles_list['profiles']);
      for (let gr=0; gr<profiles_list['groups'].length; gr++) {
        let options = [];
        for (let pr=0; pr<profiles.length; pr++) {
          if (profiles_list['groups'][gr].setting_type == profiles[pr][1].setting_type) {
            if (profiles[pr][1].setting_type == 'project' &&
              profiles[pr][1].project_name != profiles_list['groups'][gr].project_name) continue;

            options.push({
              'value': profiles[pr][1].profile_uiname,
              'label': profiles[pr][1].profile_uiname
            });
          }
        }
        console.log(options);
        this.profiles_options.push({
          'label': profiles_list['groups'][gr].name,
          'options': options
        });
      }
      this.isLoading = false;
    },
    value_changed: function(val) {
      if (!this.clear_inputs) {
        this.edit_carrier_changed = true;
      }
    },
    deleteCarrier: function(id) {
      let i=0;
      while (this.carrier_list[i]['id'] != id) i++;
      this.carrier_list.splice(i, 1);
      delete this.carrier_info_mapping[i];
      window.socket.emit('command', {cmd: 'remove_carrier', carrier_id: id});
    },
    editCarrier: function(id) {
      window.socket.emit('DLA_get_carrier_info', {'id': id}, (res) => {
        this.edit_carrier = res;
      });
    },
    changeColor(id, color) {
      window.set_carrier_color(window.active_layer_id, id, color);
      window.socket.emit('mapeditor_system_settings_set_dict_value', {
        'category': 'ui_settings',
        'name': 'carrier_colors',
        'key': window.active_layer_id+id,
        'value': {
            'es_id': window.active_layer_id,
            'carrier_id': id,
            'color': color
        }
      });
      window.socket.emit('command', {cmd: 'redraw_connections'});
    },
    clearInput() {
      this.clear_inputs = true;

      this.edit_carrier.id = '';
      this.edit_carrier.name = '';
      this.edit_carrier.type = 'None';
      this.edit_carrier.emission = undefined;
      this.edit_carrier.energy_content = undefined;
      this.edit_carrier.energy_content_unit = 'Undefined';

      this.edit_carrier.state_of_matter = 'Undefined';
      this.edit_carrier.renewable_type = 'Undefined';
      this.edit_carrier.voltage  = undefined;
      this.edit_carrier.pressure = undefined;
      this.edit_carrier.supply_temperature = undefined;
      this.edit_carrier.return_temperature = undefined;

      this.edit_carrier.cost_sort = undefined
      this.edit_carrier.cost_value = undefined
      this.edit_carrier.cost_profile = undefined
      this.edit_carrier.cost_unit = undefined

      this.edit_carrier_changed = false;
      this.clear_inputs = false;
    },
    addCarrier() {
      this.edit_carrier.id = uuidv4();
      this.saveCarrier();
    },
    saveCarrier() {
      window.socket.emit('DLA_update_carrier_info', {'id': this.edit_carrier.id, 'carr_info': this.edit_carrier},
        (res) => {
          window.set_carrier_list(window.active_layer_id, res);
          this.getData();
        });
      this.clearInput();
    },
    cancelEditCarrier() {
      this.clearInput();
    },
    getEDRCarriersList() {
      const path = '/edr_carriers';
      axios.get(path)
        .then((res) => {
          let result = res['data'];
          let carrier_list = result['item_list'];
          this.edr_carriers_list = carrier_list;
        });
    },
    addEDRCarriers() {
      console.log('add EDR Carriers', this.edr_carriers);
      window.socket.emit('DLA_add_EDR_carriers', {'id': this.edr_carriers},
        (res) => {
          window.set_carrier_list(window.active_layer_id, res);
          this.getData();
        });
    },
  }
};
</script>

<style>
</style>