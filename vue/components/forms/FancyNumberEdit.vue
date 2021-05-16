<template>
  <div id="fancy_number_edit">
    <a-input
      v-model:value="fancy_number"
      v-model:size="text_box_size"
      v-model:addon-after="unit_of_measure"
      class="fe_box"
      size="small"
      type="text"
      @blur="onLoseFocus"
    />
    <!-- TODO use addon-after="W" to add the unit to the input box, if the unit is available -->
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
};

const multipliers = [
  1e24, 1e21, 1e18, 1e15, 1e12, 1e9, 1e6, 1e3, 1, 1e-3, 1e-6, 1e-9, 1e-12, 1e-15, 1e-18, 1e-21, 1e-24,
];
const NO_MULTIPLIER = 8;   // index in multipliers array

export default {
  name: "FancyNumberEdit",
  props: {
    'value': {
      type: Number,
      default: 0
    },
    'size': {
      type: String,
      default: "default"
    },
    'unit': {
      type: String,
      default: ""
    }
  },
  emits: ['update:value'],
  data() {
      return {
          fancy_number: this.parseNumber(this.value),
      }
  },
  computed: {
      number: function() {
        return this.parseFancyNumber(this.fancy_number);
      },
      text_box_size: function() {
        // make props.size available as variable in the template
        return this.size;
      },
      unit_of_measure: function() {
        return this.unit;
      }
  },
  methods: {
      parseFancyNumber: function(fn) {
        // This function will take a fancy number fn (of type string)
        // and returns the floating point value of it.
        if (fn.slice(-1) in factors) {
          let n = fn.substring(0, fn.length - 1);
          let f = fn.slice(-1);
          return parseFloat(n) * factors[f];
        } else {
          return parseFloat(fn);
        }
      },
      parseNumber: function(nr) {
        // This function will take a floating point number (nr)
        // and returns the fancy number (of type string)
        let nr_str = nr.toString();
        let fn = this.processFancyNumber(nr_str)
        return fn
      },
      processFancyNumber: function(fn) {
        if (fn == "" || fn == "0") return fn;
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
        // (here we have the real number in the string, without the 'multiplier')

        // then calculate the precision, so we can use it for the end result
        // Note: scientific notation fails
        let precision = fn.length;
        for (let i=0; i<fn.length; i++) {
          if (fn[i] == '0' || fn[i] == '.')
            precision -= 1;
          else
            break;
        }

        // Then correct for leading zeros (multiples of 0.001)
        let multiplier = NO_MULTIPLIER;
        zeros = fn.substring(0,4);
        while (zeros == '0.00') {
          multiplier += 1;
          fn = (parseFloat(fn) * 1000).toString();
          zeros = fn.substring(0,4);
        }

        // Then correct for trailing zeros (multiples of 1000)
        let zeros = fn.slice(-3);
        while (zeros == '000') {
          multiplier -= 1;
          fn = fn.substring(0, fn.length - 3);
          zeros = fn.slice(-3);
        }

        fn = parseFloat(fn).toPrecision(precision);  // use same precision as for input
        multiplier = multipliers[multiplier];  // now go from index to real multiplier
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
        this.fancy_number = this.processFancyNumber(this.fancy_number);
        this.$emit('update:value', this.number);
      }
  }
}
</script>

<style>
  .fe_box {
    border-width: 1px;
  }
</style>
