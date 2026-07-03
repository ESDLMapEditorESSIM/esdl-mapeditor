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
        <a-layout-content :style="contentStyle">
          <a-space direction="vertical" style="width: 100%;">
            <a-button click="handle_save">Save</a-button>
            <CodeEditor
                ref="editor"
                v-model:value="selected_service_config"
                :language="language"
                :rows="25"
                :update-on-input="true"
                :format-on-blur="true"
                @validate="onValidate"
            />
            <a-textarea
                v-model:value="selected_service_config"
                :rows="30"
                :cols="100"
                style="width: 100%; height: 100%;"
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
const selected_service_config = ref('{"test": "test"}');
// const selected_service_config = ref({"test": "test"});
const language = ref("json");

const selectedKeys = ref([]);
const items = ref([]);

window.socket.emit('get_esdl_services_list', function(res) {
    service_settings.value = res
    // service_settings_text.value = JSON.stringify(res, null, 4);

    items.value = [];
    for (let i = 0; i < res.length; i++) {
      let service_config = res[i];
      items.value.push({
        key: service_config["id"],       // key
        icon: null,                      // icon
        label: service_config["name"],   // label
      });
    }
});

const handle_click = (e) => {
  for (let i = 0; i < service_settings.value.length; i++) {
    if (service_settings.value[i].id === e.key) {
      selected_service_config.value = JSON.stringify(service_settings.value[i], null, 4);
      // selected_service_config.value = service_settings.value[i];
    }
  }
  console.log(selected_service_config.value);
};

const onValidate = (validation) => {
  console.log(validation);
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
      }

      window.socket.emit('store_esdl_services_list', service_settings);
      set_esdl_services_information(service_settings);
      alert("Successfully saved ESDL services!");
  } catch (e) {
    alert("Failed setting ESDL services! Error: " + e)
  }
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