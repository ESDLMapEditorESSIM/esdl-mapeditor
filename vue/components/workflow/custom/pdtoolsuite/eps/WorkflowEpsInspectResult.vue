<template>
  <p v-if="isLoading">Loading...</p>
  <a-tree
    v-else-if="treeData.length"
    :tree-data="treeData"
    :default-expanded-keys="['0', '1', '2']"
    show-icon
  >
    <template #build>
      <build-outlined />
    </template>
    <template #home>
      <home-outlined />
    </template>
    <template #number>
      <number-outlined />
    </template>
    <template #team>
      <team-outlined />
    </template>
  </a-tree>
  <p v-else>
    Please right-click on a building in a baseline EPS ESDL and select "Show EPS results" to view detailed EPS output information for this building.
  </p>
</template>

<script setup>
import {onUnmounted, ref} from "vue";
// eslint-disable-next-line no-unused-vars
import {BuildOutlined, HomeOutlined, NumberOutlined, TeamOutlined,} from "@ant-design/icons-vue";
import {useWorkflow} from "@/composables/workflow";
import {useEsdlBuildings} from "@/composables/esdlBuildings";
import {workflowGetData} from "../../../utils/api.js";

const { getFromState } = useWorkflow();
const { addBuildingContextMenuItem, removeBuildingContextMenuItem } = useEsdlBuildings();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});
const workflowStep = props.workflowStep;

let treeData = ref([]);
const isLoading = ref(false);

const contextMenuItemText = "Show EPS Results";

// eslint-disable-next-line no-unused-vars
const components = {
  BuildOutlined,
  HomeOutlined,
  NumberOutlined,
  TeamOutlined,
};

onUnmounted(() => {
  removeBuildingContextMenuItem(contextMenuItemText);
});

const getEpsDetails = (asset_id) => {
  window.socket.emit("DLA_get_object_properties", { id: asset_id }, async (res) => {
    isLoading.value = true;
    try {
      const attrs = res.attributes.Advanced;
      let pand_bagid;
      for (const attr of attrs) {
        if (attr.name === "originalIdInSource") {
          pand_bagid = attr.value;
          break;
        }
      }
      const request_params = {};
      request_params["execution_id"] = getFromState("execution.id");
      request_params["pand_bagid"] = pand_bagid;
      const data = await workflowGetData(workflowStep.custom_data.url, request_params)
      generateTreeData(data);
    } finally {
      isLoading.value = false;
    }
  });
};

removeBuildingContextMenuItem(contextMenuItemText);
addBuildingContextMenuItem(contextMenuItemText, "icons/BuildingContents.png", getEpsDetails);

/**
 * An entry in the tree.
 */
class TreeEntryDefinition {
  constructor(name, key, render_func = null) {
    this.name = name;
    this.key = key;
    this.render_func = render_func;
  }

  /** Return the value of the entry. Use the render func if applicable. */
  render(data) {
    let value = undefined;
    if (this.render_func) {
      value = this.render_func(data);
    } else {
      value = data[this.key] || "Onbekend";
      if (value === "Unknown") {
        value = "Onbekend";
      }
    }
    return `${this.name}: ${value}`;
  }
}

const generateTreeData = (data) => {
  if (data) {
    const pandEntry = generatePandEntry(data, "0");
    const bedrijvenEntry = generateBedrijvenEntry(data, "1");
    const vbosEntry = generateVbosEntry(data, "2");

    treeData.value = [pandEntry, bedrijvenEntry, vbosEntry];
  }
};

const generatePandEntry = (data, baseKey) => {
  const pandEntryDefinitions = [
    new TreeEntryDefinition("Pand BAG ID", "pand_bagid"),
    new TreeEntryDefinition("Plaats", "city"),
    new TreeEntryDefinition("Postcode", "postal_code"),
    new TreeEntryDefinition("Adres", null, (data) => {
      return renderAddress(
        data.street_name,
        data.house_number,
        data.house_letter,
        data.house_addition
      );
    }),
    new TreeEntryDefinition("Bouwjaar", "bouwjaar"),
    new TreeEntryDefinition(
      "Type installatie ruimteverwarming",
      "pand_type_installatie_ruimteverwarming"
    ),
  ];
  const pandChildren = generateTreeEntries(data, pandEntryDefinitions, baseKey);

  // Generate the results key value set.
  const pandResultsExcludes = [
    "bedrijventerrein_naam",
    "check_bouwlagen",
    "check_hoogte",
    "check_vbo_compleet",
    "check_pand_compleet",
    "lst_adres_huisletter",
    "lst_adres_huisnummer",
    "lst_adres_plaats",
    "lst_adres_straatnaam",
    "lst_adres_toevoeging",
    "lst_bedrijf_naam",
    "null",
    "pand_bagid",
    "pand_bouwjaar",
    "project_naam",
  ];
  const lastChildKey = pandChildren[pandChildren.length - 1].key;
  const resultsChild = generateResultsEntry(
    data.pand_results,
    pandResultsExcludes,
    [baseKey, lastChildKey].join("-")
  );
  pandChildren.push(resultsChild);

  const pandEntry = {
    title: "Pand",
    key: baseKey,
    slots: {
      icon: "home",
    },
    children: pandChildren,
  };
  return pandEntry;
};

/**
 * Generate a single "Bedrijven" entry, containing all bedrijven as children.
 */
const generateBedrijvenEntry = (data, baseKey) => {
  const bedrijfResultsExcludes = [
    "bedrijf_naam",
    "bedrijf_id",
    "bedrijf_werknemers",
    "lst_adres_huisnummer",
    "lst_adres_plaats",
    "lst_adres_straatnaam",
    "lst_bedrijventerrein_naam",
    "null",
    "pand_bagid",
    "project_naam",
  ];

  const bedrijfEntryDefinitions = [
    new TreeEntryDefinition("Bedrijf ID", "bedrijf_id"),
    new TreeEntryDefinition("Werknemers", "bedrijf_werknemers"),
    new TreeEntryDefinition("SBI", "bedrijf_sbi"),
  ];
  const bedrijfEntries = [];
  for (const [idx, bedrijfData] of data.bedrijven.entries()) {
    const bedrijfKey = [baseKey, idx].join("-");
    const bedrijfChildren = generateTreeEntries(
      bedrijfData,
      bedrijfEntryDefinitions,
      bedrijfKey
    );

    // Generate the results key value set.
    const lastKey = bedrijfChildren[bedrijfChildren.length - 1].key;
    const resultsChild = generateResultsEntry(
      bedrijfData.bedrijf_results,
      bedrijfResultsExcludes,
      [baseKey, lastKey].join("-")
    );
    bedrijfChildren.push(resultsChild);

    const bedrijfEntry = {
      title: bedrijfData.bedrijf_naam,
      key: bedrijfKey,
      children: bedrijfChildren,
    };
    bedrijfEntries.push(bedrijfEntry);
  }

  const rootBedrijvenEntry = {
    title: "Bedrijven",
    key: baseKey,
    slots: {
      icon: "team",
    },
    children: bedrijfEntries,
  };
  return rootBedrijvenEntry;
};

/**
 * Generate a single "VBOs" entry, containing all VBOs as children.
 */
const generateVbosEntry = (data, baseKey) => {
  const vboEntryDefinitions = [
    new TreeEntryDefinition(
      "Ruimteverwarming aandeel",
      "vbo_ruimteverwarming_aandeel"
    ),
    new TreeEntryDefinition(
      "Ruimtekoeling aandeel",
      "vbo_ruimtekoeling_aandeel"
    ),
  ];
  const vboEntries = [];
  for (const [idx, vboData] of data.vbos.entries()) {
    const vboKey = [baseKey, idx].join("-");
    const vboChildren = generateTreeEntries(
      vboData,
      vboEntryDefinitions,
      vboKey
    );

    const vboEntry = {
      title: vboData.vbo_bagid,
      key: vboKey,
      children: vboChildren,
    };
    vboEntries.push(vboEntry);
  }

  const rootVbosEntry = {
    title: "Verblijfsobjecten",
    key: baseKey,
    slots: {
      icon: "build",
    },
    children: vboEntries,
  };
  return rootVbosEntry;
};

/**
 * Generate a list of direct tree children for the data, based on the provided treeEntries.
 */
const generateTreeEntries = (data, treeEntryDefinitions, baseKey) => {
  const children = [];
  for (const [idx, treeEntryDefinition] of treeEntryDefinitions.entries()) {
    children.push({
      title: treeEntryDefinition.render(data),
      key: [baseKey, idx].join("-"),
    });
  }
  return children;
};

const readableKeyMapping = {
  "pv": "PV",
  "co2": "CO2",
  "Lst bedrijf sbi": "Lijst Bedrijf SBI",
  "incl": "incl.",
  "kwh": "kWh",
  "wtw": "WTW",
  "vbo": "VBO",
  "investeringskosten totaal KIA": "Investeringskosten totaal incl. KIA"
}

/**
 * Generate generic key value entries from the results.
 */
const generateResultsEntry = (resultsData, excludeKeys, baseKey) => {
  const resultEntries = [];
  for (const [idx, [key, value]] of Object.entries(
    Object.entries(resultsData)
  )) {
    if (excludeKeys.includes(key)) {
      continue;
    }
    const resultKey = [baseKey, idx].join("-");
    // Uppercase the start of the string and replace the underscore with a space.
    let readableKey = key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ");
    // Check if any term in the readableKeyMapping is in the readableKey. If so, replace that term.
    for (const [term, replacement] of Object.entries(readableKeyMapping)) {
      if (readableKey.includes(term)) {
        readableKey = readableKey.replace(term, replacement);
      }
    }

    let readableValue = value || "Onbekend";
    // The value is a string here. Check if it is a number and then format it as such.
    if (!isNaN(readableValue)) {
      readableValue = parseFloat(readableValue).toLocaleString("nl-NL");
    }
    const resultEntry = {
      title: `${readableKey}: ${readableValue}`,
      key: resultKey,
    };
    resultEntries.push(resultEntry);
  }

  const rootResultsEntry = {
    title: "Resultaten",
    key: baseKey,
    slots: {
      icon: "number",
    },
    children: resultEntries,
  };
  return rootResultsEntry;
};

const renderAddress = (
  street_name,
  house_number,
  house_letter,
  house_addition
) => {
  if (!street_name || !house_number) {
    return "Onbekend";
  }
  let address = `${street_name} ${house_number}`;
  if (house_letter) {
    address += ` ${house_letter}`;
  }
  if (house_addition) {
    address += ` ${house_addition}`;
  }
  return address;
};
</script>
