<template>
  <a-layout>
    <a-layout-content>
      <h1>
        Properties
      </h1>
      <a-space
        v-if="!isLoading"
        id="object-properties"
        direction="vertical"
      >
        <a-collapse v-model:activeKey="activePanels">
          <a-collapse-panel
            v-for="(cat, key) in obj_properties.attributes"
            :key="key" :header="key + ' attributes'">
            <table>
              <tr v-for="attr in cat" :key="attr.value">
                <td><span :title="attr.doc">{{ attr.name }}</span></td>
                <td>
                  <FancyNumberEdit
                    v-if="attr.type=='EInt'"
                    v-model="attr.value" />
                  <FancyNumberEdit
                    v-if="attr.type=='EDouble'"
                    v-model="attr.value" />
                  <a-input
                    v-if="attr.type=='EString'"
                    v-model:value="attr.value"
                    class="fe_box"
                    type="text" />
                  <a-select
                    v-if="attr.type=='EEnum' || attr.type=='EBoolean'"
                    v-model:value="attr.value">
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
                  />
                </td>
              </tr>
            </table>
          </a-collapse-panel>
          <a-collapse-panel key="Ports" header="Ports">
            <PortsEdit v-model:portList="obj_properties.port_connected_to_info" />
          </a-collapse-panel>
          <a-collapse-panel key="CostInformation" header="Cost information">
            <CostInformationEdit v-model:costInfo="obj_properties.cost_information" />
          </a-collapse-panel>
        </a-collapse>
      </a-space>
    </a-layout-content>
    <a-layout-footer>
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
    </a-layout-footer>
  </a-layout>
</template>

<script>
import moment from 'moment';
import FancyNumberEdit from "../components/forms/FancyNumberEdit"
import ProfileTableEdit from "../components/forms/ProfileTableEdit"
import PortsEdit from "../components/forms/PortsEdit"
import CostInformationEdit from "../components/forms/CostInformationEdit"
import { useObject } from '../composables/ObjectID'
// import { v4 as uuidv4 } from 'uuid';

const { currentObjectID } = useObject();

export default {
  name: "ObjectProperties",
  components: {
    FancyNumberEdit,
    ProfileTableEdit,
    PortsEdit,
    CostInformationEdit
  },
  data() {
    return {
      obj_properties: {},
      activePanels: ['Basic'],
      isLoading: true
    };
  },
  watch: {
    activePanels(key) {
      console.log(key);
    }
  },
  computed: {
  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    moment,
    handleUpdate: function(field, message) {
      console.log(message);
      this[field] = message;
    },
    getDataSocketIO: function() {
      console.log(currentObjectID.value);
      window.socket.emit('DLA_get_object_properties', {'id': currentObjectID.value}, (res) => {
        console.log(res);
        this.obj_properties = res;
        this.isLoading = false;
      });
    },
    save: function() {
      console.log('Pressed save');
      const result = this.buildResultInfo();
      console.log(result);
      window.socket.emit('DLA_set_object_properties', {'id': currentObjectID.value}, result);
      window.sidebar.hide();
    },
    cancel: function() {
      console.log('Pressed cancel');
      window.sidebar.hide();
    },
    buildResultInfo: function() {
      let result = {};

      return result;
    }
  }
};
</script>

<style>
  .fe_box {
    border-width: 1px;
  }
</style>

