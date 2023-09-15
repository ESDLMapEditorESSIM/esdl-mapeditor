<template>
  <h1>
    Marginal Costs
  </h1>
  <a-space
    v-if="!isLoading"
    id="marginal-costs"
    style="width: 100%"
    direction="vertical"
  >
    <a-card>
      <a-space
        direction="vertical"
      >
        Marginal costs:
        <FancyNumberEdit
          v-model:value="marginal_costs"
        />
      </a-space>
    </a-card>

    <a-space>
      <a-button
        type="primary"
        @click="remove"
      >
        Remove costs
      </a-button>
      <a-button
        type="primary"
        @click="save"
      >
        Save costs
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
import { useObject } from '../composables/ObjectID'

const { currentObjectID } = useObject();

export default {
  components: {
    FancyNumberEdit,
  },
  data() {
    return {
      marginal_costs: ''
    }
  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    getDataSocketIO: function() {
      console.log(currentObjectID.value);
      window.socket.emit('DLA_get_marg_costs', {'id': currentObjectID.value}, (res) => {
        console.log(res);

        if (res['marg_costs']) {
          this.marginal_costs = res['marg_costs'];
        }

        this.isLoading = false
      });
    },
    remove: function() {
      // console.log('Pressed remove costs')
      window.socket.emit('command', {cmd: 'remove_marg_costs', asset_id: currentObjectID.value});
      this.marginal_costs = '';
    },
    save: function() {
      // console.log('Pressed save');
      window.socket.emit('command', {cmd: 'set_marg_costs', asset_id: currentObjectID.value, marg_costs: this.marginal_costs});
      window.sidebar.hide();
    },
    cancel: function() {
      // console.log('Pressed cancel');
      window.sidebar.hide();
    },

  }
};

</script>
