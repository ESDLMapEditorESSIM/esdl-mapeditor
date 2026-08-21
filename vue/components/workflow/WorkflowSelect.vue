<template>
  <p v-if="isLoading">Loading...</p>
  <a-form v-else layout="vertical" :model="form" :label-col="{ span: 0 }">
    <a-form-item :label="stepParams.config.label">
      <a-select
        v-model:value="form[stepParams.data.output_wrapper_variable]"
        :options="options"
        :placeholder="placeholder"
        :status="selectStatus"
        :mode="mode"
        :allow-clear="allowClear"
        @change="onSelectValue"
      />
    </a-form-item>
    <a-form-item v-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK">
      <a-button
        type="primary"
        :disabled="!isAllInputValid()"
        @click="onSubmit"
      >
        {{ stepParams.buttonText || "Submit" }}
      </a-button>
    </a-form-item>
  </a-form>
</template>

<script setup="props">
import {onMounted, onUnmounted, ref, watch} from "vue";
import {useWorkflow, WorkflowNextStepTriggerOptions} from "@/composables/workflow";
import {MessageNames, PubSubManager} from "@/bridge";
import {getattrd} from "@/utils/utils";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

/** @type {import('vue').Ref<StepParameters|null>} */
const stepParams = ref({});

const isLoading = ref(true);
const options = ref([]);
const placeholder = ref("Select");
const form = ref([]);
const mode = ref("");
const allowClear = ref(false);
let subscriptionId = null;

const selectStatus = ref("error");

const {
  getWorkflowStepParameters,
  goToStep,
  setWorkflowStepInputValid,
  getInputData,
  sendOutputData,
  isAllInputValid,
  getState,
} = useWorkflow();

// Variable for indexing all choices by the value (which is rendered in HTML).
let choicesByValue;

const insertedPreviousValues = ref(false);

onMounted(() => {
  init();
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
  if (stepParams.value.reloadOnEsdlActivation) {
    subscriptionId = PubSubManager.subscribe(MessageNames.SELECT_ACTIVE_LAYER, () => {
      init();
    });
  }
});

onUnmounted(() => {
  if (subscriptionId !== null) {
    PubSubManager.unsubscribe(subscriptionId);
  }
});

const onSubmit = async () => {
  const value = form.value[stepParams.value.data.output_wrapper_variable];
  if (isRequired() && !value) {
    alert("Please select a valid option.");
    return;
  }

  const output = !value ? null : mode.value === "multiple" ? value.map(item => choicesByValue.get(item)) : choicesByValue.get(value);
  await sendOutputData(
      stepParams.value.data, output, () => goToStep(stepParams.value.nextStep)
  );
};

const onSelectValue = (value) => {
  form.value[stepParams.value.data.output_wrapper_variable] = value;
  updateInputState();
  if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.INPUT_CHANGE) {
    onSubmit();
  }
};

const isRequired = () => {
  return stepParams.value.config.required !== false;
};

const updateInputState = () => {
  const isValid = mode.value === "multiple" || !isRequired() || form.value[stepParams.value.data.output_wrapper_variable] !== "";
  selectStatus.value = isValid ? "" : "error";
  setWorkflowStepInputValid(stepParams.value.id, isValid);
};

const updateData = async (data) => {
  // console.debug("Updating data", data)
  if (data && stepParams.value.config.data_from_variable){
      data = data[stepParams.value.config.data_from_variable];
  }
  if (data) {
    let choices;
    // Choices data can be found as an attribute in a dict or is directly returned as a list
    if (stepParams.value.config.choices_attr) {
      choices = data[stepParams.value.config.choices_attr];
    } else {
      choices = data;
    }
    if (choices == null) {
      return;
    }
    if (!Array.isArray(choices)) {
      choices = Object.values(choices);
    }

    choicesByValue = new Map();
    options.value = choices.map((choice) => {
      let label;
      let value;
      if (stepParams.value.config.label_fields && stepParams.value.config.value_field){
        const label_list = stepParams.value.config.label_fields
            .map((label_field) => {
              if (typeof label_field === "string") {
                return getattrd(choice, label_field);
              } else {
                const label = label_field.label;
                const default_value = label_field.default;
                const value = choice[label];
                const value_map = label_field.map;
                if (value_map && value in value_map) {
                  return value_map[value];
                } else if (default_value) {
                  return default_value;
                } else {
                  console.warn("Value not found in value_map: ", value, value_map);
                  return value;
                }
              }
            }).filter((value) => value);
        label = label_list.join(" - ");
        value = choice[stepParams.value.config.value_field];
      } else{
        label = choice;
        value = choice
      }
      choicesByValue.set(value, choice);
      return {
        label: label,
        value: value,
      };
    });
  }

  if (!(stepParams.value.data.output_wrapper_variable in form.value)) {
    if (mode.value === "multiple") {
      form.value = [];
    } else {
      form.value = {};
      form.value[stepParams.value.data.output_wrapper_variable] = "";
    }
  }

  if (!insertedPreviousValues.value) {
    // overwrite default values with last submitted values if present in state
    const state = getState();
    if (stepParams.value.data.output_wrapper_variable in state) {
      form.value[stepParams.value.data.output_wrapper_variable] =
          state[stepParams.value.data.output_wrapper_variable][stepParams.value.config.value_field]
    }
    insertedPreviousValues.value = true;
  }

  updateInputState();
  isLoading.value = false;
};

const init = async () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  if (!stepParams.value.data.output_wrapper_variable) {
    console.error("Mandatory parameter 'data.output_wrapper_variable' not set for 'select' workflow step:", stepParams.value.id);
  }

  if ("placeholder" in stepParams.value.config) {
    placeholder.value = stepParams.value.config.placeholder;
  }
  if ("multiple" in stepParams.value.config) {
    mode.value = stepParams.value.config.multiple ? "multiple" : "";
  }
  allowClear.value = stepParams.value.config.required === false;

  await getInputData(stepParams.value.data, updateData);
};
</script>
