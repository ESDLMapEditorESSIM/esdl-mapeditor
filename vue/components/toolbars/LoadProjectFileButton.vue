<template>
  <a class="dropdown-item" href="#">
    <div class="menu-icon fas fa-project-diagram" />
    <input id="upload-file" type="file" name="upload-file" hidden @change="onChange" @input="onInput">
    <label for="upload-file" refs="upload-file" class="file-btn">
      Load project...
    </label>
  </a>
</template>

<script setup>

import {useEnergyProjects} from "../../composables/energyProjects";
import {MessageNames, PubSubManager as PubsubManager} from "../../bridge";

console.log("Yellow");

function onChange(event) {
  const files = event.target.files;
  loadProjectFile(files[0]);
}

function loadProjectFile(file) {
  const file_reader = new FileReader();
  const file_name = file.name;

  // This function will do the actual uploading. It is triggered when
  // calling readAsDataURL on the file_reader.
  file_reader.onload = async () => {
    window.show_loader();
    try {
      const base64_file = file_reader.result;

      window.socket.emit('load_energy_project', {base64_file: base64_file, filename: file_name}, (responseProject) => {
        const {energyProject} = useEnergyProjects();
        console.log(responseProject);
        if (responseProject) {
          energyProject.value = responseProject;
        } else {
          alert("Failed loading energy project file.");
        }
      });
    } finally {
      window.hide_loader();
    }
  }
  // Trigger the onload.
  file_reader.readAsDataURL(file);
}

</script>
