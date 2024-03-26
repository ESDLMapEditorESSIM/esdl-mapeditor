<template>
  <div
    v-show="kpis_present"
    class="my-control leaflet-announce-kpis-toolbar"
  >
    <a-space>
      <span>KPIs are present in ESDL:</span>
      <a-button size="small" type="primary" @click="handleShowDashboard">Show dashboard</a-button>
      <a-button size="small" type="default" @click="handleDismiss">Dismiss</a-button>
    </a-space>
  </div>
</template>

<script>
import { ref } from 'vue';

const kpis_present = ref(false);
const visible = ref(true);

export default {
  name: "AnnounceKPIsToolbar",
  setup() {
    return {
      kpis_present,
      visible,
    };
  },
  mounted() {
    window.addEventListener('load', () => {
      // run after everything is in-place
      window.socket.on('kpis_present', function(res) {
        console.log(res);
        kpis_present.value = res;
      });
    });
  },
  methods: {
    handleShowDashboard: function() {
      kpis_present.value = false;
      window.kpi_dashboard.open();
    },
    handleDismiss: function() {
      kpis_present.value = false;
    }
  },
};
</script>

<style>
.leaflet-announce-kpis-toolbar {
    padding: 5px;
    z-index: 2000;
    background: white;

    box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
    border-radius: 5px;
}

.leaflet-announce-kpis-toolbar p {
  margin-bottom: 0;
}

</style>
