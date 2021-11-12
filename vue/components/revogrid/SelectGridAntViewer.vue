<template>
  {{ label }}
</template>

<script>
export default {
  // access any cell properties here
  props: ["rowIndex", "prop", "model", "data", "column"],
  name: "SelectGridAntViewer",
  // data() {
  //   return {
  //     cell_data: this.model[this.prop],
  //   };
  // },
  computed: {
    cell_data() {
      return this.model[this.prop];
    },
    label() {
      const selected_option_value = this.cell_data;
      let selected_option_obj = null;
      for (const opt of this.column.options) {
        if (opt.value == selected_option_value) {
          selected_option_obj = opt;
          break;
        }
      }
      return selected_option_obj
        ? selected_option_obj.label
        : selected_option_value;
    },
  },
};
</script>
