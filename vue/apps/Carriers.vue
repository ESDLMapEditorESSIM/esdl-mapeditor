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
              @change="value_changed"
            >
              <a-select-option
                v-for="carr in carrier_types"
                :key="carr.value"
                :value="carr.value"
              >
                {{ carr.name }}
              </a-select-option>
            </a-select>
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
              @change="value_changed"
            >
              <a-select-option
                v-for="ecu in energy_content_units"
                :key="ecu.value"
                :value="ecu.value"
              >
                {{ ecu.name }}
              </a-select-option>
            </a-select>
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
              @change="value_changed"
            >
              <a-select-option
                v-for="som in state_of_matters"
                :key="som.value"
                :value="som.value"
              >
                {{ som.name }}
              </a-select-option>
            </a-select>
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
              @change="value_changed"
            >
              <a-select-option
                v-for="rt in renewable_types"
                :key="rt.value"
                :value="rt.value"
              >
                {{ rt.name }}
              </a-select-option>
            </a-select>
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
  </a-space>
</template>

<script>
import FancyNumberEdit from "../components/forms/FancyNumberEdit"
import { v4 as uuidv4 } from 'uuid';

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
        {name: 'No Carrier selected', value: 'None'},
        {name: 'Energy carrier', value: 'EnergyCarrier'},
        {name: 'Electricity Commodity', value: 'ElectricityCommodity'},
        {name: 'Gas Commodity', value: 'GasCommodity'},
        {name: 'Heat Commodity', value: 'HeatCommodity'},
        {name: 'EnergyCommodity', value: 'EnergyCommodity'},
      ],
      renewable_types: [
        {name: 'Undefined', value: 'Undefined'},
        {name: 'Fossil', value: 'Fossil'},
        {name: 'Renewable', value: 'Renewable'},
      ],
      state_of_matters: [
        {name: 'Undefined', value: 'Undefined'},
        {name: 'Solid', value: 'Solid'},
        {name: 'Liquid', value: 'Liquid'},
        {name: 'Gaseous', value: 'Gaseous'},
      ],
      energy_content_units: [
        {name: 'Please select...', value: 'Undefined'},
        {name: 'MJ/kg', value: 'MJ/kg'},
        {name: 'MJ/Nm3', value: 'MJ/m3'},
        {name: 'MJ/MJ', value: 'MJ/MJ'},
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
      },
    }
  },
  computed: {
  },
  mounted() {
    this.getData();
  },
  methods: {
    getData: function() {
      this.carrier_list = window.get_carrier_list(window.active_layer_id);
      this.carrier_info_mapping = window.get_carrier_info_mapping(window.active_layer_id);
      for (let i=0; i<this.carrier_list.length; i++) {
        this.carrier_list[i]['color'] = this.carrier_info_mapping[this.carrier_list[i]['id']]['color'];
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
      this.edit_carrier_id = id;
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

      this.edit_carrier_changed = false;
      this.clear_inputs = false;
    },
    addCarrier() {
      this.edit_carrier.id = uuidv4();
      window.socket.emit(
        'DLA_update_carrier_info',
        {'id': this.edit_carrier.id, 'carr_info': this.edit_carrier},
        (res) => {
          window.set_carrier_list(window.active_layer_id, res);
          this.getData();
        });
      this.clearInput();
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
  }
};
</script>

<style>
</style>