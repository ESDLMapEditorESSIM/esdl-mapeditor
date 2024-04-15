<template>
  <a class="dropdown-item" href="#" @click="showModelContexts">
    <div id="menu_doc" class="menu-icon" style="margin-top: 0px;"><i class="fa fa-info-circle" aria-hidden="true" /></div>
    Select model context
  </a>
  <a-modal v-model:open="visibleModelContext" title="Model Context" width="750px">
    <template #footer>
      <a-button
        key="ok"
        type="primary"
        @click="hideModelContexts"
      >
        OK
      </a-button>
    </template>
  </a-modal>
</template>

<script setup>
import { useModelContext } from "@/composables/modelContext";
import {MessageNames, PubSubManager} from "@/bridge";

const { visibleModelContext, modelContexts, fetchModelContexts, showModelContexts, hideModelContexts } = useModelContext()

PubSubManager.subscribe(MessageNames.SOCKET_CONNECTED, () => {
  fetchModelContexts();
})

</script>
