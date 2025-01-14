<template>
  <div
    :class="{ 'active-dropzone': active }"
    class="dropzone"
    @dragenter.prevent="toggleActive"
    @dragleave.prevent="toggleActive"
    @dragover.prevent
    @drop.prevent="toggleActive"
  >
    <span>Drag and drop a new image</span>
    <span>OR</span>
    <label for="dropzoneFile">Select image file</label>
    <input id="dropzoneFile" type="file" class="dropzoneFile">
  </div>
</template>

<script setup>
import { ref } from "vue";

const active = ref(false);

const toggleActive = () => {
  active.value = !active.value;
};

</script>

<style scoped lang="scss">
.dropzone {
  width: 400px;
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  row-gap: 16px;
  border: 2px dashed #41b883;
  background-color: #fff;
  transition: 0.3s ease all;

  label {
    padding: 8px 12px;
    color: #fff;
    background-color: #41b883;
    transition: 0.3s ease all;
  }

  input {
    display: none;
  }
}

.active-dropzone {
  color: #fff;
  border-color: #fff;
  background-color: #41b883;

  label {
    background-color: #fff;
    color: #41b883;
  }
}
</style>