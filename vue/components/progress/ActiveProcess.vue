<template>
  <div v-show="showActiveLongProcess" class="my-control leaflet-active-long-process">
    <a-button
      style="float: right"
      type="link"
      @click="toggleShowActiveLongProcess()"
    >
      <i class="fa fa-times small-icon" />
    </a-button>
    <h1>{{ activeLongProcess.name }}</h1>
    <p>Progress: {{ activeLongProcess.progress }}%</p>
    <p v-if="activeLongProcess.message">Status: {{ activeLongProcess.message }}</p>
    <p v-show="activeLongProcess.isDone">
      <span v-if="activeLongProcess.isFailed" style="color: var(--red)">
        Process failed.&nbsp;
      </span>
      <span v-else style="color: var(--green)">
        Process complete!&nbsp;
      </span>
      <a-button
        type="link"
        @click="toggleShowActiveLongProcess()"
      >
        Close
      </a-button>
    </p>
  </div>
</template>

<script>
import { useLongProcessState } from "../../composables/longProcess.js";

export default {
  name: "ActiveLongProcess",
  setup() {
    const { toggleShowActiveLongProcess, activeLongProcess, showActiveLongProcess } = useLongProcessState();
    return {
      activeLongProcess,
      showActiveLongProcess,
      toggleShowActiveLongProcess,
    };
  }
};
</script>

<style>
.leaflet-active-long-process {
    padding: 8px;
    z-index: 2000;
    width: 300px;
    height: 120px;
    background: white;
    overflow: auto;

    box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
    border-radius: 5px;

}

.leaflet-active-long-process p {
  margin-bottom: 0;
}
</style>