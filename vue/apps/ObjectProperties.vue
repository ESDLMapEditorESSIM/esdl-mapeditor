<template>
  <h1 v-if="!isLoading">
    <span
      v-if="!obj_properties.multi_select_info"
      :title="obj_properties.object.doc"
    >
      {{ obj_properties.object.name }}
    </span>
    <span
      v-if="obj_properties.multi_select_info"
    >
      {{ obj_properties.multi_select_info.num_assets_selected }} assets selected of type:
      {{ obj_properties.multi_select_info.selected_asset_type }}
    </span>
  </h1>
  <div v-if="!isLoading" id="object-properties">
    <a-row :gutter="[0, 24]">
      <a-col :span="24">
        <a-collapse v-model:activeKey="activePanels" defaultActiveKey="Basic">
          <a-collapse-panel
            v-for="(cat, key) in obj_properties.attributes"
            :key="key"
            :header="key + ' attributes'"
          >
            <div>
              <a-row :gutter="[0, 4]" type="flex" align="middle" v-for="attr in cat" :key="attr.name">
              <!-- attributes -->
                <a-col :span="9"  v-if="isAttribute(attr)">
                  <span :title="attr.doc">{{ camelCase(attr.name) }}</span>
                </a-col>
                <a-col :span="15" v-if="isAttribute(attr)">
                  <FancyNumberEdit 
                    v-if="attr.type == 'EInt'" 
                    v-model:value="attr.value" 
                    size="small" 
                    v-model:unit="attr.unit"
                    @update:value="(val) => { updateAttribute(attr.name, val);}"/>
                  <FancyNumberEdit
                    v-if="attr.type == 'EDouble'"
                    v-model:value="attr.value"
                    size="small"
                    v-model:unit="attr.unit"
                    @update:value="(val) => { updateAttribute(attr.name, val); }"
                  />
                  <a-input
                    v-if="attr.type == 'EString' && attr.name !== 'description'"
                    v-model:value="attr.value"
                    class="fe_box"
                    size="small"
                    type="text"
                    @blur="updateAttribute(attr.name, attr.value)"
                  />
                  <a-textarea
                    v-if="attr.type == 'EString' && attr.name === 'description'"
                    v-model:value="attr.value"
                    size="small"
                    auto-size
                    @blur="updateAttribute(attr.name, attr.value)"
                  />
                  <a-select
                    v-if="attr.type == 'EEnum' || attr.type == 'EBoolean'"
                    v-model:value="attr.value" size="small" style="width: 100%"
                    @change="updateAttribute(attr.name, attr.value)"
                  >
                    <!-- mode werkt nog niet op deze manier: :mode="multiSelect(attr)"-->    
                    <a-select-option
                      v-for="opt in attr.options"
                      :key="opt"
                      :value="opt"
                    >
                      {{ opt }}
                    </a-select-option>
                  </a-select>
                  <a-date-picker
                    v-if="attr.type == 'EDate'"
                    format="YYYY-MM-DD HH:mm:ss"
                    size="small"
                    style="width: 100%"
                    :default-value="get_default_date(attr.value)"
                    :show-time="{ defaultValue: moment('00:00:00', 'HH:mm:ss') }"
                    @change="(date, dateString) => { updateDateAttribute(date, dateString, attr.name); }"
                  />
                </a-col>
              <!-- references -->

                <a-col :span="24" v-if="!isAttribute(attr) && !ignoredRefs.includes(attr.name)">
                    <a-row :gutter="[0, 0]" type="flex" align="middle">
                    <ReferenceViewer :parentObjectID="obj_properties.object.id" :reference="attr" @update="updateRef($event, attr)"/>
                    </a-row>
                </a-col>
              </a-row>
            </div>
          </a-collapse-panel>          
          <a-collapse-panel v-if="obj_properties.port_connected_to_info" key="Ports" header="Ports">
            <PortsEdit
              v-model:portList="obj_properties.port_connected_to_info"
              v-model:objectID="obj_properties.object.id"
            />
          </a-collapse-panel>
          <a-collapse-panel key="CostInformation" header="Cost information">
            <CostInformationView
              v-model:costInfo="obj_properties.cost_information"
              v-model:objectID="obj_properties.object.id"
            />
          </a-collapse-panel>
        </a-collapse>
      </a-col>
    </a-row>
    <a-row>
      <!-- these buttons are not necessary I think... -->
      <a-col :span="24">
        <a-space>
          <a-button type="primary" @click="save">Save</a-button>
          <a-button type="primary" @click="cancel">Cancel</a-button>
        </a-space>
      </a-col>
    </a-row>
  </div>
</template>

<script>
const moment = () => import("moment");
import FancyNumberEdit from "../components/forms/FancyNumberEdit";
import ProfileTableEdit from "../components/forms/ProfileTableEdit";
import PortsEdit from "../components/forms/PortsEdit";
import CostInformationView from "../components/forms/CostInformationView";
import ReferenceViewer from "../components/forms/ReferenceViewer";
import { useObject } from "../composables/ObjectID";
// import { camelCaseToWords } from "../../static/utils/utils"

const { currentObjectID } = useObject();
const ignoredRefs = ['port', 'costInformation', 'geometry'];

export default {
  name: "ObjectProperties",
  components: {
    FancyNumberEdit,
    ProfileTableEdit,
    PortsEdit,
    CostInformationView,
    ReferenceViewer,
  },
  data() {
    return {
      obj_properties: {},
      activePanels: ["Basic"],
      isLoading: true,
      ignoredRefs
    };
  },
  computed: {
    filteredReferences: function() {
      return this.obj_properties.references.filter(ref => !ignoredRefs.includes(ref.name));
    },
    multiSelect: function(attr) {
      return (attr.many ? 'multiple' : 'default');
    }
  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    moment,
    camelCase: function(str) {
      // TODO: import this function from utils.js and let utils.js export functions
      return window.camelCaseToWords(str);
    },
    getDataSocketIO: function () {
      // console.log(currentObjectID.value);
      window.socket.emit(
        "DLA_get_object_properties",
        { id: currentObjectID.value },
        (res) => {
          console.log(res);
          this.obj_properties = res;
          this.isLoading = false;
        }
      );
    },
    save: function () {
      window.socket.emit(
        "DLA_set_object_properties",
        { id: currentObjectID.value },
        this.obj_properties
      );
      window.sidebar.hide();
    },
    cancel: function () {
      // console.log('Pressed cancel');
      window.sidebar.hide();
    },
    updateAttribute(name, new_value) {
      // console.log(new_value);
      // console.log("setting param "+ name +" to value "+new_value);
      window.socket.emit("command", {
        cmd: "set_asset_param",
        id: currentObjectID.value,
        param_name: name,
        param_value: new_value,
      });
      window.PubSubManager.broadcast('ASSET_PROPERTIES', { id: currentObjectID.value, name: name, value: new_value });
    },
    updateDateAttribute(date, dateString, name) {
      let new_value;
      if (date) {
        new_value = date.format('YYYY-MM-DDTHH:mm:ss.SSSSSSZZ');
      } else {
        new_value = '';
      }
      window.socket.emit('command', {
        'cmd': 'set_asset_param',
        'id': currentObjectID.value,
        'param_name': name,
        'param_value': new_value
      });
    },
    get_default_date(value) {
      //console.log(value);
      if (value)
        return moment(value, 'YYYY-MM-DDTHH:mm:ss.SSSSSSZZ')
      else
        return null;
    },
    isAttribute: function(feature) {
        // in the combined features list (attributes and references) one can check if it is an attibute or not.
        return !('containment' in feature);
    },
    updateRef: function(event, reference) {
      console.log('OP ref updated: ', event, reference)
      reference.value.type = event.value.type;
      reference.value.repr = event.value.repr;
    }
  }
};
</script>

<style>
.fe_box {
  border-width: 1px;
}
</style>

