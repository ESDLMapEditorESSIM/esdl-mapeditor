<!-- todo: deal with ref.many: how to display multiple references -->
<template>
    <!-- This template assumes that it is part of a <a-row> -->
    <a-col :span="9">
        <span :title="ref.doc">{{ camelCase(ref.name) }}</span>
    </a-col>
    <a-col :span="15 - nrButtons*2">        
        <span> {{ ref.value.repr }}</span>
    </a-col>
    <a-col :span="2"  v-if="ref.value.repr !== null && !ref.eopposite">
        <a-button size="small" @click="editRef(ref)" class="align-right">
            <!-- <a-icon type="edit" /> -->
            <i class="fa fa-edit small-icon" />
        </a-button>
    </a-col>   
    <a-col :span="2" v-if="(ref.value.repr == null || ref.many) && !ref.eopposite">
        <a-button size="small" @click="addRef(ref)" class="align-right">
            <!-- <a-icon type="plus-square" /> -->
            <i class="fa fa-plus small-icon" />
        </a-button>
    </a-col>
     <a-col :span="2" v-if="ref.value.repr !== null && !ref.eopposite">
        <a-button size="small" @click="deleteRef(ref)" class="align-right">
            <!-- <a-icon type="delete" /> -->
            <i class="fa fa-trash small-icon" />
        </a-button>
    </a-col>
    <a-modal v-model:visible="visible" :title="modalTitle" @ok="handleOk" width="750px">
        <TableEditor :parentObjectID="parentObjectIdentifier" :reference="ref" v-if="ref.type == 'Table'"/>
        <span v-else>Other editor</span>
    </a-modal>
</template>

<script>
import TableEditor from './TableEditor'
export default {
  name: "ReferenceViewer",
  components: {
      TableEditor
  },
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
      },
      nrButtons: function() {
          let canEdit = this.ref.value.repr !== null && !this.ref.eopposite;
          let canAdd = (this.ref.value.repr == null || this.ref.many) && !this.ref.eopposite;
          let canDelete = this.ref.value.repr !== null && !this.ref.eopposite;
          let buttons = 0;
          if (canEdit) buttons++;
          if (canAdd) buttons++;
          if (canDelete) buttons++;
          return buttons;
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
    // deleteRef: function(ref) {
    //     // edit this ref
    //     this.type = 'Delete';
    //     console.log('delete', ref);
    //     this.visible = true;
    // },
    deleteRef: function(ref) {
      let self=this;
      this.$confirm({
        title: 'Delete value of ' + ref.type,
        content: 'Are you sure you want to delete the data of ' + ref.name + ' with value \'' + ref.value.repr + '\'?',
        okText: 'Yes',
        okType: 'danger',
        cancelText: 'No',
        onOk() {
          self.visible = false;
          console.log('delete', ref);
        },
        onCancel() {
          console.log('Cancelled');
          self.visible = false;
        },
      });
    },
    handleOk: function(ref) {
        console.log(ref);
        this.visible = false;
    }
  },
};
</script>

<style scoped>
    .small-icon {
        font-size: 11px;
    }
    .align-right {
        margin-left: auto;
        margin-right: 0;
        display: block;
    }
</style>