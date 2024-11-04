<!-- TODO: component refinement needed -->
<template>
  <div v-show="trace.length > 0" class="plotly-plot">
    <div id="plot" ref="plot" />
  </div>
  <div v-show="trace.length === 0" class="no-data">Not configured</div>
</template>

<script>
import Plotly from "plotly.js-dist";

export default {
    props: {
        trace: Array,
        layout: Object
    },
    data() {
        return {
            config: { 
                responsive: true, 
                maintainAspectRatio: true,
                automargin: true,
                toImageButtonOptions: {
                    format: 'svg', // one of png, svg, jpeg, webp
                    height: 500,
                    width: 900,
                    scale: 1 // Multiply title/legend/axis/canvas sizes by this factor
                }
            }
        };
    },

    mounted() {
        Plotly.newPlot(this.$refs.plot, this.trace, this.layout, this.config);
    },

    updated() {
        Plotly.react(this.$refs.plot, this.trace, this.layout, this.config);
        console.log('Updating plot');
    }
};
</script>

<style>
.plotly-plot {
/*    min-width: 40rem;
    min-height: 30rem;*/
}


/* #plot {
    width: 100%;
    height: 100%; 
} */

.no-data {
     /* width: 40rem;  */
    height: 100%;
    display: flex;
    flex-grow: auto;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-size: 20pt;
    color: grey;
    font-style: italic;
    border: solid 3px lightgrey;
    border-radius: .5rem;
    margin: 1rem;
}
</style>