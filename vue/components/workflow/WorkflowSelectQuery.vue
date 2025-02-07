<template>
  <p v-if="isLoading">Loading...</p>
  <a-form v-else layout="vertical" :model="form" :label-col="{ span: 0 }">
    <a-form-item :label="workflowStep.label">
      <a-select
        v-model:value="form[workflowStep.target_variable]"
        :options="options"
        :placeholder="placeholder"
        :status="selectStatus"
        :mode="mode"
        @change="onSelectValue"
      />
    </a-form-item>
    <a-form-item v-if="!autoNextStep">
      <a-button type="primary" @click="onSubmit"> Select</a-button>
    </a-form-item>
  </a-form>
</template>

<script setup="props">
import {onMounted, ref} from "vue";
import {useWorkflow} from "@/composables/workflow";
import {workflowGetData} from "./utils/api";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;

const isLoading = ref(true);
const options = ref([]);
const placeholder = ref("Select");
const form = ref([]);
const autoNextStep = ref(false);
const mode = ref("");

const selectStatus = ref("error");

const {getParamsFromState, goToNextStep, getState, setWorkflowStepInputValid} = useWorkflow();
const state = getState();

// Variable for indexing all choices by the value (which is rendered in HTML).
let choicesByValue;

onMounted(() => {
  init();
});

const onSubmit = () => {
  const value = form.value[workflowStep.target_variable];
  if (!value) {
    alert("Please select a valid option.");
    return;
  }
  state[workflowStep.target_variable] = choicesByValue.get(value);
  goToNextStep();
};

const onSelectValue = (value) => {
  form.value[workflowStep.target_variable] = value;
  updateInputState();
  if (autoNextStep.value) {
    onSubmit();
  }
};

const updateInputState = () => {
  const isValid = mode.value === "multiple" || form.value[workflowStep.target_variable] !== "";
  selectStatus.value = isValid ? "" : "error";
  setWorkflowStepInputValid(workflowStep.id, isValid);
};

const doGetData = async () => {
  let data;
  if ("url" in workflowStep.source) {
    const request_params = getParamsFromState(workflowStep.source.request_params);
    data = await workflowGetData(workflowStep.source.url, request_params);
  } else if ("data" in workflowStep.source) {
    data = workflowStep.source.data;
  }

  if (data != null) {
    const source = workflowStep.source;
    let choices;
    // Choices data can be found as an attribute in a dict or is directly returned as a list
    if ("choices_attr" in source) {
      choices = data[source.choices_attr];
    } else {
      choices = data;
    }

    // Convert the choices to a list of options.
    options.value = choices.map((choice) => {
      const label_list = source.label_fields.map((label_field) => choice[label_field]).filter((value) => value);
      const label = label_list.join(" - ");
      return {
        label: label,
        value: choice[source.value_field],
      };
    });
    // Index all choices by value, so we can store them in the state entirely.
    choicesByValue = new Map(
        choices.map((choice) => [choice[source.value_field], choice])
    );
  }

  if ("placeholder" in workflowStep) {
    placeholder.value = workflowStep.placeholder;
  }

  if ("multiple" in workflowStep) {
    mode.value = workflowStep.multiple ? "multiple" : "";
  }
  if (!(workflowStep.target_variable in form.value)) {
    if (mode.value === "multiple") {
      form.value = [];
    } else {
      form.value = {};
      form.value[workflowStep.target_variable] = "";
    }
  }
  updateInputState();
  isLoading.value = false;
};

const init = () => {
  if ("auto_next_step" in workflowStep) {
    autoNextStep.value = workflowStep.auto_next_step;
  }
  doGetData();
};
</script>
