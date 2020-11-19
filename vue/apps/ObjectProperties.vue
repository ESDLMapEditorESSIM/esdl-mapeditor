<template>
  <h1>
    Properties
  </h1>
  <a-space
    v-if="!isLoading"
    id="object-properties"
    direction="vertical"
  >
    <a-collapse v-model:activeKey="activePanels" width="100%">
      <a-collapse-panel
        v-for="(cat, key) in obj_properties.attributes"
        :key="key" :header="key + ' attributes'">
        <table>
          <tr v-for="attr in cat" :key="attr.name">
            <td><span :title="attr.doc">{{ attr.name }}</span></td>
            <td>
              <FancyNumberEdit
                v-if="attr.type=='EInt'"
                v-model="attr.value" 
                @update:value="(val) => { updateAttribute(attr.name, val); }" />
              <FancyNumberEdit
                v-if="attr.type=='EDouble'"
                v-model="attr.value"
                @update:value="(val) => { updateAttribute(attr.name, val); }" />
              <a-input
                v-if="attr.type=='EString'"
                v-model:value="attr.value"
                class="fe_box"
                type="text" 
                @blur="updateAttribute(attr.name, attr.value)" />
              <a-select
                v-if="attr.type=='EEnum' || attr.type=='EBoolean'"
                v-model:value="attr.value"
                @blur="updateAttribute(attr.name, attr.value)">
                <a-select-option
                  v-for="opt in attr.options"
                  :key="opt" :value="opt">
                  {{ opt }}
                </a-select-option>
              </a-select>
              <a-date-picker
                v-if="attr.type == 'EDate'"
                format="YYYY-MM-DD HH:mm:ss"
                :default-value="moment(attr.value, 'YYYY-MM-DD HH:mm:ss')"
                :show-time="{ defaultValue: moment('00:00:00', 'HH:mm:ss') }" 
                @change="updateAttribute(attr.name, attr.value)" />
            </td>
          </tr>
        </table>
      </a-collapse-panel>
      <a-collapse-panel key="Ports" header="Ports">
        <PortsEdit v-model:portList="obj_properties.port_connected_to_info" v-model:objectID="obj_properties.object.id" />
      </a-collapse-panel>
      <a-collapse-panel key="CostInformation" header="Cost information">
        <CostInformationView v-model:costInfo="obj_properties.cost_information" v-model:objectID="obj_properties.object.id" />
      </a-collapse-panel>
    </a-collapse>
  </a-space>
  <a-space>
    <a-button
      type="primary"
      @click="save"
    >
      Save
    </a-button>
    <a-button
      type="primary"
      @click="cancel"
    >
      Cancel
    </a-button>
  </a-space>
</template>

<script>
import moment from 'moment';
import FancyNumberEdit from "../components/forms/FancyNumberEdit"
import ProfileTableEdit from "../components/forms/ProfileTableEdit"
import PortsEdit from "../components/forms/PortsEdit"
import CostInformationView from "../components/forms/CostInformationView"
import { useObject } from '../composables/ObjectID'

const { currentObjectID } = useObject();

export default {
  name: "ObjectProperties",
  components: {
    FancyNumberEdit,
    ProfileTableEdit,
    PortsEdit,
    CostInformationView,
  },
  data() {
    return {
      obj_properties: {},
      activePanels: ['Basic'],
      isLoading: true
    };
  },
  computed: {
  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    moment,
    getDataSocketIO: function() {
      // console.log(currentObjectID.value);
      window.socket.emit('DLA_get_object_properties', {'id': currentObjectID.value}, (res) => {
        console.log(res);
        this.obj_properties = res;
        this.isLoading = false;
      });
    },
    save: function() {
      window.socket.emit('DLA_set_object_properties', {'id': currentObjectID.value}, this.obj_properties);
      window.sidebar.hide();
    },
    cancel: function() {
      // console.log('Pressed cancel');
      window.sidebar.hide();
    },
    updateAttribute(name, new_value) {
      // console.log(new_value);
      // console.log("setting param "+ name +" to value "+new_value);
      window.socket.emit('command', {
        'cmd': 'set_asset_param', 
        'id': currentObjectID.value,
        'param_name': name,
        'param_value': new_value
      });
    },
  }
};
</script>

<style>
  .fe_box {
    border-width: 1px;
  }
</style>

