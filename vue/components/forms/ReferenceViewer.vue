<template>
    <!-- This template assumes that it is part of a <a-row> -->
    <a-col :span="9">
        <span :title="ref.doc">{{ camelCase(ref.name) }}</span>
    </a-col>
    <a-col :span="12">        
        <span> {{ ref.value.repr }}</span>
    </a-col>
    <a-col :span="3">
        <span v-if="ref.value.repr !== null && !ref.eopposite">
            <a @click="editRef(ref)">
              <i class="fa fa-edit" />
            </a>
        </span>
        <span v-if="ref.value.repr !== null && !ref.eopposite">
            <a @click="deleteRef(ref)">
              <i class="fa fa-trash" />
            </a>
        </span>
        <span v-if="(ref.value.repr == null || ref.many) && !ref.eopposite">
            <a @click="addRef(ref)">
              <i class="fa fa-plus" />
            </a>
        </span>
    </a-col>
    <a-modal v-model:visible="visible" :title="modalTitle" @ok="handleOk">
        <span v-if="ref.type == 'Table'">TABLE EDITOR</span>
        <span v-else>Other editor</span>
    </a-modal>
</template>

<script>

export default {
  name: "ReferenceViewer",
  props: {
    reference: {
      type: Object,
      default: function () {
        return {};
      },
    },
    parentObjectID: String,
  },
  data() {
    return {
      parentObjectIdentifier: this.parentObjectID,
      ref: this.reference,
      visible: false,
      type: 'Add'
    };
  },
  mounted() {
    //console.log(this.reference);
    this.visible = false;
  },
  computed: {
      modalTitle: function() {
          return this.type + ' ' + this.camelCase(this.ref.name);
      }
  },
  methods: {
    camelCase: function(str) {
      // TODO: import this function from utils.js and let utils.js export functions
      return window.camelCaseToWords(str);
    },
    editRef: function(ref) {
        // edit this ref
        console.log('edit',ref);
        this.type = 'Edit';
        this.visible = true;
    },
    addRef: function(ref) {
        // edit this ref
        console.log('add', ref);
        this.type = 'Add';
        this.visible = true;
    },
    deleteRef: function(ref) {
        // edit this ref
        this.type = 'Delete';
        console.log('delete', ref);
        this.visible = true;
    },
    handleOk: function(ref) {
        console.log(ref);
        this.visible = false;
    }
  },
};
</script>

<style>
</style>