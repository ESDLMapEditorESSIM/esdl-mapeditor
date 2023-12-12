<template>
  <a-row>
    <a-col :span="24" class="width:100%">
      <b>{{ tooltipTitle }}</b>
    </a-col>
  </a-row>
  <template
    v-if="has_info"
  >
    <a-row>
      <a-col :span="24">
<!--        <button @click="showCostInformation()">-->
        <span>
          <i
            :class="'fa fa-eur small-icon' + (tooltip_info.costInformation?' icon-info-present':' icon-info-not-present')"
            style="padding-left: 4px; padding-right: 8px;"
            :title="(tooltip_info.costInformation?'costInformation is present':'No costInformation available')"
          />
        </span>
<!--        </button>-->
        <button
          v-for="port_profile_info in tooltip_info.profiles"
          :key="port_profile_info.port_id"
          @click="showProfileInformation(port_profile_info.port_id)"
        >
          <i :class="'fa fa-line-chart small-icon' + ((port_profile_info.profs_info.length > 0)?' icon-info-present':' icon-info-not-present')" />
        </button>
      </a-col>
    </a-row>
    <a-row
      v-if="profile_info_visible"
    >
      <a-col :span="24">
        Profile info:
        <table>
          <tr
            v-for="prof in tooltip_info.profiles[current_port_id].profs_info"
            :key="prof.profile_id"
          >
            <td>
              <span :for="prof.profile_id" :title="prof.name">
                {{ prof.attr_name }}:
              </span>
            </td>
            <td>
              <input
                :id="prof.profile_id"
                :key="prof.profile_id"
                :value="prof.value"
                style="width: 50px"
                @blur="e => changeProfileValue(prof.profile_id, prof.attr_name, e.target.value)"
                @change="e => changeProfileValue(prof.profile_id, prof.attr_name, e.target.value)"
              >
            </td>
            <td>
              <button @click="editProfile(current_port_id)">
                <i class="fa fa-edit small-icon" />
              </button>
            </td>
          </tr>
        </table>
      </a-col>
    </a-row>
  </template>
  <template v-else>
    <spinner />
  </template>
</template>

<script setup>
import { ref } from "vue";
import { useTooltipInfo } from "../composables/TooltipInfo";
import axios from 'axios';
// eslint-disable-next-line no-unused-vars
import spinner from "../components/Spinner";

// eslint-disable-next-line no-unused-vars
const { tooltipObjectID, tooltipTitle  } = useTooltipInfo();

const has_info = ref(false);
const tooltip_info = ref({});
const profile_info_visible = ref(false);
const current_port_id = ref(false);

axios.get("/tooltip_info/"+ tooltipObjectID.value)
  .then((res) => {
    tooltip_info.value = res.data;
    has_info.value = true;

    console.log(tooltip_info.value);
  });

// eslint-disable-next-line no-unused-vars
function showCostInformation() {
  console.log('test');
}

// eslint-disable-next-line no-unused-vars
function showProfileInformation(port_id) {
  console.log(profile_info_visible.value);
  console.log(port_id);
  console.log(current_port_id.value);
  if (profile_info_visible.value && port_id == current_port_id.value) {
    profile_info_visible.value = false;
  } else {
    if (tooltip_info.value.profiles[port_id].profs_info.length > 0) {
      current_port_id.value = port_id;
      profile_info_visible.value = true;
    } else {
      window.set_port_profile(null, tooltipObjectID.value, port_id);
    }
  }
}

// eslint-disable-next-line no-unused-vars
function changeProfileValue(profile_id, attr_name, value) {
  window.socket.emit('command', {
    cmd: 'set_asset_param',
    id: profile_id,
    param_name: attr_name,
    param_value: value
  });
}

// eslint-disable-next-line no-unused-vars
function editProfile(port_id) {
  window.set_port_profile(null, tooltipObjectID.value, port_id)
}

</script>