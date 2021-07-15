<template>
  <a class="dropdown-item" href="#" @click="showAboutBox">
    <div id="menu_doc" class="menu-icon" style="margin-top:0px"><i class="fa fa-info-circle" aria-hidden="true" /></div>
    About...
  </a>
  <a-modal v-model:visible="visible" title="About" width="750px">
    <template #footer>
      <a-button key="ok" type="primary" @click="handleOk">
        Ok
      </a-button>
    </template>
    <a-row>
      <a-col :span="8">
        <img src="images/esdl_logo_small.png">
      </a-col>
      <a-col :span="16">
        <p>
          This is the ESDL MapEditor version: {{ version }}
        </p>
        <p>
          The ESDL MapEditor is developed by TNO and available as open source software under the Apache 2.0 license.
        </p>
        <p>
          For installing the ESDL MapEditor together with the other open source software components around it,
          click <a href="https://github.com/ESDLMapEditorESSIM/docker-toolsuite" target="#">here</a>.
        </p>
        <p>
          To go to the git repository of the ESDL MapEditor codebase,
          click <a href="https://github.com/ESDLMapEditorESSIM/esdl-mapeditor" target="#">here</a>.
        </p>
      </a-col>
    </a-row>
  </a-modal>
</template>

<script>

export default {
  name: "AboutBox",
  data() {
    return {
      visible: false,
      version: '',
    };
  },
  methods: {
    showAboutBox() {
      this.version = window.version;
      this.visible = true;
    },
    handleOk() {
      this.visible = false;
    },
  },
};

</script>