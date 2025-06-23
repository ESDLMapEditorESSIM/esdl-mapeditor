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
let subscriptionId = null;

const selectStatus = ref("error");

const {
  getWorkflowStepParameters,
  goToStep,
  setWorkflowStepInputValid,
  getInputData,
  sendOutputData,
  isAllInputValid
} = useWorkflow();

// Variable for indexing all choices by the value (which is rendered in HTML).
let choicesByValue;

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
  if (!value) {
    alert("Please select a valid option.");
    return;
  }
  await sendOutputData(
      stepParams.value.data, choicesByValue.get(value), () => goToStep(stepParams.value.nextStep)
  );
};

const onSelectValue = (value) => {
  form.value[stepParams.value.data.output_wrapper_variable] = value;
  updateInputState();
  if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.INPUT_CHANGE) {
    onSubmit();
  }
};

const updateInputState = () => {
  const isValid = mode.value === "multiple" || form.value[stepParams.value.data.output_wrapper_variable] !== "";
  selectStatus.value = isValid ? "" : "error";
  setWorkflowStepInputValid(stepParams.value.id, isValid);
};

const updateData = async (data) => {
  console.debug("Updating data", data)
  if (data != null) {
    let choices;
    // Choices data can be found as an attribute in a dict or is directly returned as a list
    if ("choices_attr" in stepParams.value.config) {
      choices = data[stepParams.value.config.choices_attr];
    } else {
      choices = data;
    }
    if (!Array.isArray(choices)) {
      choices = Object.values(choices);
    }

    options.value = choices.map((choice) => {
      const label_list = stepParams.value.config.label_fields
          .map((label_field) => {
            if (typeof label_field === "string") {
              return choice[label_field];
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
      const label = label_list.join(" - ");
      return {
        label: label,
        value: choice[stepParams.value.config.value_field],
      };
    });
    // Index all choices by value, so we can store them in the state entirely.
    choicesByValue = new Map(
        choices.map((choice) => [choice[stepParams.value.config.value_field], choice])
    );
  }

  if (!(stepParams.value.data.output_wrapper_variable in form.value)) {
    if (mode.value === "multiple") {
      form.value = [];
    } else {
      form.value = {};
      form.value[stepParams.value.data.output_wrapper_variable] = "";
    }
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

  await getInputData(stepParams.value.data, updateData);
};
</script>
