<template>
  <div style="height: 100%">
    <h1>External Service Settings</h1>
    <a-layout style="height: calc(100% - 26px);">
      <a-layout-sider :style="siderStyle">
        <a-menu
          id="external_service_settings_menu"
          v-model:selectedKeys="selectedKeys"
          mode="inline"
          :items="items"
          @click="handle_click"
        ></a-menu>
      </a-layout-sider>
      <a-layout>
        <a-layout-content>
          <a-space direction="vertical" style="width: 100%;">
            <a-space direction="horizontal">
              <a-button @click="handle_save">Save</a-button>
              <a-button @click="handle_delete">Delete</a-button>
              <a-button @click="handle_add">Add</a-button>
            </a-space>
            <CodeEditor
                ref="editor"
                v-model="selected_service_config"
                :language="language"
                :rows="35"
                :update-on-input="true"
                :format-on-blur="true"
                @validate="onValidate"
            />
          </a-space>
        </a-layout-content>
      </a-layout>
    </a-layout>
  </div>
</template>

<script setup>
import { ref } from "vue";
import CodeEditor from "@/components/forms/CodeEditor.vue";

let service_settings = ref([]);
const selected_service_config = ref("");
const language = ref("json");

const default_service_config = {
  "id": "",
  "name": "New service",
  "explanation": "This is a newly added service",
  "type": "json",
  "http_method": "post",
  "url": "http://localhost:8080/api/send_esdl",
  "headers": {
      "Content-Type": "application/json"
  },
  "query_parameters": [],
  "body": "",
  "body_config": {
      "type": "json",
      "parameters": [
          {
              "type": "esdl",
              "encoding": "base64_encoded",
              "parameter": "energysystem"
          }
      ]
  },
  "result": [
      {
          "code": 200,
          "action": "esdl"
      }
  ]
}

const selectedKeys = ref([]);
const items = ref([]);

const update_menu_based_on_services_list = (services_list) => {
  items.value = [];
  for (let i = 0; i < services_list.length; i++) {
    let service_config = services_list[i];
    items.value.push({
      key: service_config["id"],       // key
      icon: null,                      // icon
      label: service_config["name"],   // label
      service_list_index: i            // index in the services list (not used by the menu)
    });
  }
}

window.socket.emit('get_esdl_services_list', function(res) {
    service_settings.value = res
    update_menu_based_on_services_list(service_settings.value);

    if (res.length > 0) {
      selected_service_config.value = JSON.stringify(service_settings.value[0], null, 4);
      selectedKeys.value = [items.value[0].key];
    }
});

const handle_click = (e) => {
  for (let i = 0; i < service_settings.value.length; i++) {
    if (service_settings.value[i].id === e.key) {
      selected_service_config.value = JSON.stringify(service_settings.value[i], null, 4);
    }
  }
};

const onValidate = (validation) => {
}

const handle_save = (e) => {
  try {
    let service_config = JSON.parse(selected_service_config.value);
    let service_id = service_config.id;
    let service_name = service_config.name;

    let service_found = false;
    for (let i = 0; i < service_settings.value.length; i++) {
      if (service_settings.value[i].id === service_id) {
        service_settings.value[i] = service_config;
        service_found = true;
      }
    }
    // If it was not found, the ID must have been changed. Then check for the same name.
    if (!service_found) {
      for (let i = 0; i < service_settings.value.length; i++) {
        if (service_settings.value[i].name === service_name) {
          service_settings.value[i] = service_config;
          service_found = true;
        }
      }
    }
    // If it was still not found, the ID and name must have been changed. For now simply add it to the list.
    if (!service_found) {
       service_settings.value.push(service_config);
       selectedKeys.value = [service_id];
    }
    // update menu (because of changed IDs, names, new service configs)
    update_menu_based_on_services_list(service_settings.value);

    window.socket.emit('store_esdl_services_list', service_settings.value);
    set_esdl_services_information(service_settings.value);
    alert("Successfully saved ESDL services!");
  } catch (e) {
    alert("Failed setting ESDL services! Error: " + e)
  }
}

const handle_delete = (e) => {
  try {
    let service_config = JSON.parse(selected_service_config.value);
    let service_id = service_config.id;
    let service_name = service_config.name;

    let service_index = null;
    for (let i = 0; i < service_settings.value.length; i++) {
      if (service_settings.value[i].id === service_id) {
        service_index = i;
      }
    }
    // If it was not found, the ID must have been changed. Then check for the same name.
    if (service_index == null) {
      for (let i = 0; i < service_settings.value.length; i++) {
        if (service_settings.value[i].name === service_name) {
          service_index = i;
        }
      }
    }
    // If it was still not found, the ID and name must have been changed.
    if (service_index == null) {
      alert("Something went wrong! Service cannot be deleted.");
    } else {
      service_settings.value.splice(service_index, 1);
      // update menu because of deleted service configs
      update_menu_based_on_services_list(service_settings.value);
      window.socket.emit('store_esdl_services_list', service_settings.value);
      set_esdl_services_information(service_settings.value);
      if (service_settings.value.length > 0) {
        selectedKeys.value = [service_settings.value[0].id];
        handle_click({key: service_settings.value[0].id});
      }
      alert("Successfully deleted the service!");
    }
  } catch (e) {
    alert("Failed setting ESDL services! Error: " + e)
  }
}

const handle_add = (e) => {
  let service_config = default_service_config;
  service_config.id = uuidv4();

  service_settings.value.push(service_config);    // add config to services confif list
  update_menu_based_on_services_list(service_settings.value);     // update the menu
  selectedKeys.value = [service_config.id];     // update the selected key
  handle_click({key: service_config.id});    // load the service config in the editor box
}

const contentStyle = {
  textAlign: 'center',
  height: '100%',
  color: '#fff',
  overflow: 'auto',
};
const siderStyle = {
  textAlign: 'left',
  height: '100%',
  color: '#fff',
  overflow: 'auto',
};

</script>

<style>

</style>