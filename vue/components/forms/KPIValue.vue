<template>
  <span v-if="formattedNumber" class="kpi-number" :title="fullValue">
    <span class="formatted">{{ formattedNumber.text }}</span>
    <span v-if="formattedNumber.truncated">…</span>
  </span>
  <a-typography-text v-else :ellipsis="true" :title="fullValue" :content="fullValue" />
</template>

<script>
const MAX_FRACTION_DIGITS = 8;
const numberFormatOptions = {
  useGrouping: true,
  maximumFractionDigits: MAX_FRACTION_DIGITS,
  roundingMode: 'trunc',
};
const numberFormat = new Intl.NumberFormat('en-US', numberFormatOptions);
const truncatedNumberFormat = new Intl.NumberFormat('en-US', {
  ...numberFormatOptions,
  minimumFractionDigits: MAX_FRACTION_DIGITS,
});
const fullNumberFormat = new Intl.NumberFormat('en-US', {
  useGrouping: false,
  maximumSignificantDigits: 21,
});

export default {
  name: 'KPIValue',
  props: {
    value: {
      type: [Number, String],
      default: null,
    },
  },
  computed: {
    fullValue() {
      if (this.value === null) {
        return '';
      }
      if (typeof this.value === 'number' && Number.isFinite(this.value)) {
        return fullNumberFormat.format(this.value);
      }
      return String(this.value);
    },
    formattedNumber() {
      if (typeof this.value !== 'number' || !Number.isFinite(this.value)) {
        return null;
      }

      let fractionLength = 0;
      const decimalSeparatorIndex = this.fullValue.indexOf('.');
      if (decimalSeparatorIndex >= 0) {
        fractionLength = this.fullValue.length - decimalSeparatorIndex - 1;
      }
      const truncated = fractionLength > MAX_FRACTION_DIGITS;
      let formatter = numberFormat;
      if (truncated) {
        formatter = truncatedNumberFormat;
      }

      return {
        text: formatter.format(this.value),
        truncated,
      };
    },
  },
};
</script>

<style scoped>
.kpi-number {
  display: flex;
  justify-content: flex-end;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.formatted {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
}
</style>
