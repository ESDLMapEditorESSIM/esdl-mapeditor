<!--
  - This work is based on original code developed and copyrighted by TNO 2026.
  - Subsequent contributions are licensed to you by the developers of such code and are
  - made available to the Project under one or several contributor license agreements.
  -
  - This work is licensed to you under the Apache License, Version 2.0.
  - You may obtain a copy of the license at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Contributors:
  -     TNO         - Initial implementation
  - Manager:
  -     TNO
  -->

<template>
  <h1>Filter assets</h1>
  <a-card style="width: 100%">
    <p>
      You can filter assets based on properties.
    </p>
  </a-card>
  <a-space direction="vertical">
    <a-radio-group v-model:value="radioSelection">
      <a-radio class="radioStyle" value="uncports">Show assets with unconnected ports</a-radio>
      <a-radio class="radioStyle" value="nocost">Show assets with no carrier assigned</a-radio>
    </a-radio-group>

    <a-button type="primary" @click="filter_assets">Filter assets</a-button>
  </a-space>
</template>

<script setup>
import { ref, computed } from 'vue'

const radioSelection = ref("")

function filter_assets() {
  let active_es_id = window.active_layer_id;

  let asset_feedback_dict = {}
  if (radioSelection.value === "uncports") {
    asset_feedback_dict = find_assets_with_unconnected_ports(active_es_id);
  } else if (radioSelection.value === "nocost") {
    asset_feedback_dict = find_assets_without_carrier_assignment(active_es_id);
  }

  window.show_asset_feedback(active_es_id, asset_feedback_dict);
}

function find_assets_with_unconnected_ports(es_id) {
  let active_es_asset_info = window.get_layers(es_id, 'esdl_layer');
  let active_es_asset_layers = active_es_asset_info.getLayers();
  let asset_feedback_dict = {};

  for (let i=0; i < active_es_asset_layers.length; i++) {
    const asset = active_es_asset_layers[i];
    const assetId = asset.id;
    const assetName = asset.name;
    const assetPorts = asset.ports;

    if (!assetPorts) {
      // the polygon part of a PVPark or WindPark don't have ports, only the marker part has
      continue;
    }

    let asset_has_unconnected_ports = false;
    let list_with_port_messages = [];
    let message = null;

    for (let p of assetPorts) {
      if (p["conn_to"].length == 0) {
        if (!asset_has_unconnected_ports) {
          asset_has_unconnected_ports = true;

          message = {
            severity: 'WARNING',
            validation_message: "Asset with name '" + assetName + "' has unconnected ports:",
            check_result_messages: null,
          };
        }

        list_with_port_messages.push(
            "Port '" + p['name'] + "' from asset with name '" + assetName + "' is unconnected"
        );
      }
    }

    if (message !== null) {
      message['check_result_messages'] = list_with_port_messages;
      if (assetId in asset_feedback_dict) {
        asset_feedback_dict[assetId].push(message);
      } else {
        asset_feedback_dict[assetId] = [message];
      }
    }
  }
  return asset_feedback_dict;
}

function find_assets_without_carrier_assignment(es_id) {
  let active_es_asset_info = window.get_layers(es_id, 'esdl_layer');
  let active_es_asset_layers = active_es_asset_info.getLayers();
  let asset_feedback_dict = {};

  for (let i=0; i < active_es_asset_layers.length; i++) {
    const asset = active_es_asset_layers[i];
    const assetId = asset.id;
    const assetName = asset.name;
    const assetPorts = asset.ports;

    if (!assetPorts) {
      // the polygon part of a PVPark or WindPark don't have ports, only the marker part has
      continue;
    }

    let asset_has_port_with_unassigned_carrier = false;
    let list_with_port_messages = [];
    let message = null;

    for (let p of assetPorts) {
      if (p["carrier"] === null) {
        if (!asset_has_port_with_unassigned_carrier) {
          asset_has_port_with_unassigned_carrier = true;

          message = {
              severity: 'WARNING',
              validation_message: "Asset with name '" + assetName + "' has ports without carriers assigned:",
              check_result_messages: null,
          };
        }

        list_with_port_messages.push(
          "Port '" + p['name'] + "' from asset with name '" + assetName + "' has no carrier assigned."
        );
      }
    }

    if (message !== null) {
      message['check_result_messages'] = list_with_port_messages;
      if (assetId in asset_feedback_dict) {
        asset_feedback_dict[assetId].push(message);
      } else {
        asset_feedback_dict[assetId] = [message];
      }
    }
  }
  return asset_feedback_dict;
}

</script>

<style>

.radioStyle {
  display: flex;
  height: 30px;
  line-height: 30px;
}

</style>