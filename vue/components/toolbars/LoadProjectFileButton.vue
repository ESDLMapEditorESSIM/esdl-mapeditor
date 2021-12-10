<template>
  <a class="dropdown-item" href="#">
    <div class="menu-icon fas fa-project-diagram" />
    <input id="upload-file" type="file" name="upload-file" hidden @change="onLoadProject">
    <label for="upload-file" refs="upload-file" class="file-btn">
      Load project...
    </label>
  </a>
  <a class="dropdown-item" href="#">
    <div class="menu-icon fas fa-project-diagram" />
    <input id="upload-file" type="file" name="upload-file" hidden @change="onSaveProject">
    <label for="upload-file" refs="upload-file" class="file-btn">
      Save project..
    </label>
  </a>
</template>

<script setup>
import {useESDLProjects} from "../../composables/esdlProjects";

function onSaveProject(event) {
  console.log(event);
  // const files = event.target.files;
  // loadProjectFile(files[0]);
}

function onLoadProject(event) {
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
        const {esdlProject} = useESDLProjects();
        console.log(responseProject);
        if (responseProject) {
          esdlProject.value = responseProject;
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
