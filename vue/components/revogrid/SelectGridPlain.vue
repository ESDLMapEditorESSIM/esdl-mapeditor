<template>
  <!--
    Span here is necessary because revogrid seems to set some props on the root
    element. And that breaks when it is set on a select.
  -->
  <span>
    <select
      ref="select"
      v-model="result"
      style="width: 120px"
      @change="handleChange"
    >
      <option value="jack">Jack</option>
      <option value="lucy">Lucy</option>
      <option value="disabled" disabled>Disabled</option>
      <option value="Yiminghe">yiminghe</option>
    </select>
  </span>
</template>

<script>
export default {
  // Model contains all data from the row (every column value)
  // Prop contains the prop name that we are concerned with.
  props: ["rowIndex", "prop", "model", "data", "close", "save"],
  name: "SelectGridPlain",
  data() {
    console.log("select grid plain");
    console.log(this);
    return {
      count: 0,
      result: this.model[this.prop],
    };
  },
  methods: {
    handleChange(e) {
      console.log("change:", e);
      this.save(this.result);
    },
  },
};
</script>
