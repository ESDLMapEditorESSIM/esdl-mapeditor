<template>
  <span>
    <a-select
      ref="select"
      v-model:value="result"
      :options="column.options"
      style="width: 120px"
      @change="handleChange"
    >
    </a-select>
  </span>
</template>

<script>
import {
  Select as ASelect,
} from "ant-design-vue";

export default {
  props: ["rowIndex", "prop", "model", "data", "close", "save", "column"],
  name: "SelectGrid",
  data() {
    return {
      count: 0,
      result: this.model[this.prop],
    };
  },
  mount() {
    console.log("mounted");
  },
  methods: {
    handleChange(e) {
      console.log("change:", e);
      console.log(this);
      this.save(this.result);
    },
  },
  components: {
    ASelect,
  },
};
</script>
