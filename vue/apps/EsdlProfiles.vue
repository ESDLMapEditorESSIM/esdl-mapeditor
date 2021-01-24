<template>
  <h1>ESDL Profiles</h1>
  <p v-if="isLoading">Loading...</p>
  <div v-else>
    <p>The following profiles are present in the currently active ESDL.</p>
    <ul>
      <li v-for="esdlProfile in esdlProfiles" :key="esdlProfile.name">
        {{ esdlProfile.name }}
        <span v-if="esdlProfile.uploaded">(uploaded)</span>
      </li>
    </ul>
    <a-button @click="downloadCSVProfileTemplate">
      Download profile template
    </a-button>
  </div>
</template>

<script setup="props">
import { ref } from "vue";

let isLoading = ref(true);
let esdlProfiles = ref([]);

window.socket.emit("DLA_get_profile_names_list", {}, (result) => {
  // Build a list of all ESDL profile names.
  for (const esdl_profile_name of result.esdl_profile_names) {
    esdlProfiles.value.push({ name: esdl_profile_name, uploaded: false });
  }

  window.socket.emit("get_profiles_list", function (profiles_list) {
    // Create a list of uploaded profile names.
    let uploadedProfileNames = ref([]);
    for (const profile of Object.values(profiles_list.profiles)) {
      uploadedProfileNames.value.push(profile.profile_uiname);
    }
    uploadedProfileNames.value.push(
      "Biezenstraat14_SCEN{nr}_Nietproces_Elektra"
    );
    for (const esdlProfile of esdlProfiles.value) {
      if (uploadedProfileNames.value.includes(esdlProfile.name)) {
        esdlProfile.uploaded = true;
      }
    }
    isLoading.value = false;
  });
});

// eslint-disable-next-line no-unused-vars
const downloadCSVProfileTemplate = () => {
  let csv = "datetime_UTC";
  let header_length = 0;
  for (const esdlProfile of esdlProfiles.value) {
    if (!esdlProfile.uploaded) {
      csv += "," + esdlProfile.name;
      header_length += 1;
    }
  }
  csv += "\n";

  const startOfYear = new Date(new Date().getFullYear() - 1, 0, 1);
  const endOfYear = new Date(new Date().getFullYear(), 0, 1);
  let currentDate = startOfYear;
  const csvData = [];
  while (currentDate < endOfYear) {
    const formattedDateTime = formatDateTime(currentDate);
    csvData.push([formattedDateTime]);
    currentDate = new Date(currentDate.getTime() + 60 * 60000);
  }
  csvData.forEach((row) => {
    csv += row.join(",");
    for (let i = 0; i < header_length; i++) {
      csv += ",";
    }
    csv += "\n";
  });

  const anchor = document.createElement("a");
  anchor.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
  anchor.target = "_blank";
  anchor.download = "esdlProfileTemplate.csv";
  anchor.click();
};

function formatDateTime(date) {
  let month = "" + (date.getUTCMonth() + 1);
  let day = "" + date.getUTCDate();
  let year = date.getUTCFullYear();

  if (month.length < 2) month = "0" + month;
  if (day.length < 2) day = "0" + day;

  let hour = "" + date.getUTCHours();
  let minutes = "" + date.getUTCMinutes();

  if (hour.length < 2) hour = "0" + hour;
  if (minutes.length < 2) minutes = "0" + minutes;

  const date_part = [day, month, year].join("-");
  const time = [hour, minutes].join(":");
  return date_part + " " + time;
}
</script>

