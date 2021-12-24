<template>
  <a class="dropdown-item" href="#" @click="onNewProject">
    <span class="menu-icon ui-icon ui-icon-document" />
    New Project...
  </a>
  <a class="dropdown-item" href="#">
    <div class="menu-icon fas fa-project-diagram" />
    <input id="upload-project-file" type="file" name="upload-file" hidden @change="onLoadProject">
    <label for="upload-project-file">
      Load project...
    </label>
  </a>
  <a class="dropdown-item" href="#">
    <div class="menu-icon fas fa-project-diagram" />
    <input id="download-project-file" name="download-file" hidden @click="onSaveProject">
    <label for="download-project-file">
      Save project..
    </label>
  </a>
</template>

<script setup>
import {useESDLProjects} from "../../composables/esdlProjects";
import {download_binary_file_from_base64_str_with_type} from "../../utils/files";
import {useSocketIO} from "../../composables/socketio";

const {esdlProject} = useESDLProjects();

const {socket} = useSocketIO();

async function loadProjectFile(file) {
  const file_reader = new FileReader();
  const file_name = file.name;

  // This function will do the actual uploading. It is triggered when
  // calling readAsDataURL on the file_reader.
  file_reader.onload = async () => {
    window.show_loader();
    try {
      const base64_file = file_reader.result;
      const params = {base64_file: base64_file, filename: file_name};

      const response = await fetch("projects/load_esdl_project", {
        method: "POST",
        body: JSON.stringify(params),
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (response.ok) {
        const responseProject = await response.json()
        if (responseProject) {
          window.clear_esdl_layer_list();
          esdlProject.value = responseProject;
          // This triggers all work necessary to update the frontend.
          // socket.value.emit("set_active_variant", {id: responseProject.active_variant_id});
        }
      } else {
        alert("Failed loading energy project file.");
      }
    } finally {
      window.hide_loader();
    }
  }
  // Trigger the onload.
  file_reader.readAsDataURL(file);
}

// eslint-disable-next-line no-unused-vars
function onLoadProject(event) {
  const files = event.target.files;
  loadProjectFile(files[0]);
}

// eslint-disable-next-line no-unused-vars
async function onSaveProject() {
  window.show_loader();
  try {
    const response = await fetch("projects/save_esdl_project", {
      method: "GET",
    });
    if (response.ok) {
      const data = await response.json()
      download_binary_file_from_base64_str_with_type(
          data["base64file"],
          data["filename"],
          'application/xml',
      );
    } else {
      alert("Failed downloading energy project file.");
    }
  } finally {
    window.hide_loader();
  }
}


// eslint-disable-next-line no-unused-vars
async function onNewProject() {
  const answer = confirm("This creates a new project. Any unsaved changes will be overwritten.");
  if (answer) {
    window.show_loader();
    try {
      socket.value.emit("new_esdl_project", {}, (responseProject) => {
        if (responseProject) {
          window.clear_esdl_layer_list();
          esdlProject.value = responseProject;
        }
      })
    } finally {
      window.hide_loader();
    }
  }
}
</script>

<style scoped lang="scss">
label {
  margin-bottom: 0;
}
.dropdown-item {
  input, label {
    cursor: pointer;
  }
}
</style>
