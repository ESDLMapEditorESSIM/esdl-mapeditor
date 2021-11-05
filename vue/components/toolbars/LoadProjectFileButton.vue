<template>
  <a class="dropdown-item" href="#">
    <div id="menu_import" class="menu-icon" />
    <input id="upload-file" type="file" name="upload-file" hidden @change="onChange" @input="onInput">
    <label for="upload-file" refs="upload-file" class="file-btn">
      Load project...
    </label>
  </a>
</template>

<script setup>

function onChange(event) {
  console.log("onchange");
  console.log(event);
  const files = event.target.files;
  console.log(files);
  getVariants(files[0]);

}

function getVariants(file) {
  console.log(file);

  const file_reader = new FileReader();
  const file_name = file.name;

  // This function will do the actual uploading. It is triggered when
  // calling readAsDataURL on the file_reader.
  const load = async () => {
    window.show_loader();
    try {
      const base64_file = file_reader.result;
      console.log(base64_file);

      window.socket.emit('load_energy_project', {base64_file: base64_file, filename: file_name}, (res) => {
        alert(res);
      });
    } finally {
      window.hide_loader();
    }
  }

  file_reader.onload = load
  // Trigger the onload.
  file_reader.readAsDataURL(file);
}

</script>
