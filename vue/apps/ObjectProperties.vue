<template>
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
        :key="basic" header="Basic attributes">
      </a-collapse-panel>
    </a-collapse>
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

  </a-space>
</template>

<script>
import FancyNumberEdit from "../components/forms/FancyNumberEdit"
import ProfileTableEdit from "../components/forms/ProfileTableEdit"
import { useObject } from '../composables/ObjectID'
import { v4 as uuidv4 } from 'uuid';

export const { currentObjectID } = useObject();   // Lars: Dit snap ik niet goed, waarom export?

export default {
  components: {
    FancyNumberEdit,
    ProfileTableEdit
  },
  data() {
    return {
      obj_properties: {},
      activePanels: ['basic'],
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
