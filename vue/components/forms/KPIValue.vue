<template>
  <span v-if="numberParts" class="kpi-number" :title="fullValue">
    <span class="whole">{{ numberParts.whole }}</span>
    <span class="fraction">{{ numberParts.fraction }}</span>
    <span><template v-if="numberParts.truncated">…</template></span>
    <span class="exponent">{{ numberParts.exponent }}</span>
  </span>
  <a-typography-text v-else :ellipsis="true" :title="fullValue" :content="fullValue" />
</template>

<script>
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
      return String(this.value);
    },
    numberParts() {
      if (typeof this.value !== 'number' || !Number.isFinite(this.value)) {
        return null;
      }

      let text = this.fullValue;
      const magnitude = Math.abs(this.value);
      if ((magnitude > 0 && magnitude < 1e-8) || magnitude >= 1e4) {
        text = this.value.toExponential();
      }
      const [mantissa, exponent] = text.split('e');
      const [whole, fraction = ''] = mantissa.split('.');
      const parts = { whole, fraction: '', truncated: fraction.length > 8, exponent: '' };
      // Slice the decimal string instead of scaling the float, to avoid rounding.
      if (fraction) {
        parts.fraction = '.' + fraction.slice(0, 8);
      }
      if (exponent) {
        parts.exponent = 'e' + exponent;
      }
      return parts;
    },
  },
};
</script>

<style scoped>
.kpi-number {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 8.5ch 1em var(--kpi-exponent-width, auto);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.whole {
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
}

.fraction,
.exponent {
  text-align: left;
}
</style>
