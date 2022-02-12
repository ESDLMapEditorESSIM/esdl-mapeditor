<template>
  <div
    v-if="!isLoading && serviceList.length > 0"
    v-show="showServicesToolbar"
    class="my-control leaflet-services-toolbar"
  >
    <table>
      <tr v-for="service in serviceList" :key="service.id">
        <td class="service-icon-td">
          <div class="service-icon-div">
            <img
              class="service-icon-img"
              :src="service.icon_url"
              :title="service.name"
              draggable="false"
              @click="startService(service.id)"
            >
          </div>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>
import axios from 'axios';
import { useServicesToolbar } from "../../composables/servicesToolbar.js";

const { showServicesToolbar, toggleShowServicesToolbar } = useServicesToolbar();

export default {
  name: "ServicesToolbar",
  setup() {
    return {
      showServicesToolbar,
      toggleShowServicesToolbar
    }
  },
  data() {
    return {
      servicesList: [],
      isLoading: true
    };
  },
  mounted() {
    this.getServicesList();
  },
  methods: {
    getServicesList: function() {
      // console.log('getServicesList');
      const path = '/get_toolbar_services';
      axios.get(path)
        .then((res) => {
          this.serviceList = res['data']['services_list'];
          this.isLoading = false;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    startService: function(id) {
      window.show_esdl_service_sidebar(id);
    }
  },
};
</script>

<style>
.leaflet-services-toolbar {
    padding: 3px;
    z-index: 2000;
    background: white;

    box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
    border-radius: 5px;
}

.leaflet-services-toolbar p {
  margin-bottom: 0;
}

.service-icon-div {
  font-size: 0px;
}

.service-icon-img {
   cursor: pointer;
   height: 20px;
}

</style>
