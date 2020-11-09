<template>
  <div id="fancy_number_edit">
    <a-input
      v-model:value="fancy_number"
      class="fe_box"
      type="text"
      @blur="onLoseFocus"
    />
    <!-- <p>
      Number: {{ number }}, fancy_number: {{ fancy_number }}
    </p> -->
  </div>
</template>

<script>
const factors = {
    'Y': 1e24,
    'Z': 1e21,
    'E': 1e18,
    'P': 1e15,
    'T': 1e12,
    'G': 1e9,
    'M': 1e6,
    'k': 1e3,
    'm': 1e-3,
    'u': 1e-6,
    'n': 1e-9,
    'p': 1e-12,
    'f': 1e-15,
    'a': 1e-18,
    'z': 1e-21,
    'y': 1e-24,
}

export default {
  name: "FancyNumberEdit",
  props: {
    'value': {
      type: Number,
      default: 0
    }
  },
  emits: ['update:value'],
  data() {
      return {
          fancy_number: this.parseNumber(this.value)
      }
  },
  computed: {
      number: function() {
        return this.parseFancyNumber(this.fancy_number)
      }
  },
  methods: {
      parseFancyNumber: function(fn) {
        if (fn.slice(-1) in factors) {
          let n = fn.substring(0, fn.length - 1);
          let f = fn.slice(-1);
          return parseFloat(n) * factors[f];
        } else {
          return parseFloat(fn);
        }
      },
      parseNumber: function(nr) {
        let nr_str = nr.toString();
        let fn = this.processFancyNumber(nr_str)
        return fn
      },
      processFancyNumber: function(fn) {
        // This function allows to enter any positive number and any multiplier, the result
        // will be the 'best' human readable number. Examples:
        // - 60000000000 --> 60G 
        // - 0.000001 --> 1u
        // - 0.003G --> 3M
        // Negative numbers won't work yet

        // First check if given string contains a 'multiplier' like G, T or P
        if (fn.slice(-1) in factors) {
          let n = fn.substring(0, fn.length - 1);
          let f = fn.slice(-1);
          fn = (parseFloat(n) * factors[f]).toString();
        }
        // Then correct for trailing zeros (multiples of 1000)
        let zeros = fn.slice(-3);
        let multiplier = 1;
        while (zeros == '000') {
          multiplier = multiplier * 1000;
          fn = fn.substring(0, fn.length - 3);
          zeros = fn.slice(-3);
        }
        // Then correct for leading zeros (multiples of 0.001)
        zeros = fn.substring(0,4);
        while (zeros == '0.00') {
          multiplier = multiplier / 1000;
          fn = (parseFloat(fn) * 1000).toString();
          zeros = fn.substring(0,4);
        }
        // construct the string again
        if (multiplier != 1) {
          for (let f in factors) {
            if (multiplier == factors[f]) {
              fn = fn + f;
            }
          }
        }
        return fn;
      },
      onLoseFocus: function() {
        this.fancy_number = this.processFancyNumber(this.fancy_number)
        this.$emit('update:value', this.number)
      }
  }
}
</script>

<style>
  .fe_box {
    border-width: 1px;
  }
</style>
