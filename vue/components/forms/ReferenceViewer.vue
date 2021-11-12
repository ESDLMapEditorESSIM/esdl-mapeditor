<!-- todo: deal with ref.many: how to display multiple references -->
<template>
  <!-- This template assumes that it is part of a <a-row> -->
  <a-col :span="9">
    <span :title="ref.doc">{{ camelCase(ref.name) }}</span>
  </a-col>
  <a-col :span="15 - nrButtons*2">        
    <span> {{ ref.value.repr }}</span>
  </a-col>
  <a-col v-if="ref.value.repr !== null && !ref.eopposite" :span="2">
    <a-button size="small" class="align-right" @click="editRef(ref)">
      <!-- <a-icon type="edit" /> -->
      <i class="fa fa-edit small-icon" />
    </a-button>
  </a-col>   
  <a-col v-if="(ref.value.repr == null || ref.many) && !ref.eopposite" :span="2">
    <a-button size="small" class="align-right" @click="addRef(ref)">
      <!-- <a-icon type="plus-square" /> -->
      <i class="fa fa-plus small-icon" />
    </a-button>
  </a-col>
  <a-col v-if="ref.value.repr !== null && !ref.eopposite" :span="2">
    <a-button size="small" class="align-right" @click="deleteRef(ref)">
      <!-- <a-icon type="delete" /> -->
      <i class="fa fa-trash small-icon" />
    </a-button>
  </a-col>
  <!-- <a-modal v-model:visible="visible" :title="modalTitle" @ok="handleOk" width="750px"> -->
  <TableEditor v-if="ref.type == 'Table'" :parentObjectID="parentObjectIdentifier" :visible="visible" :title="modalTitle" :reference="ref" :ready="tableReady" @update="tableUpdate(ref, $event)" />
  <!-- <span v-else>Other editor</span> -->
  <!-- </a-modal> -->
</template>

<script>
import TableEditor from './TableEditor'
import { Modal } from 'ant-design-vue';
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
  emits: ['update'],
  data() {
    return {
      parentObjectIdentifier: this.parentObjectID,
      ref: this.reference,
      visible: false,
      type: 'Add'
    };
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
  mounted() {
    //console.log(this.reference);
    this.visible = false;
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
      Modal.confirm({
        title: 'Delete value of ' + ref.type,
        content: 'Are you sure you want to delete the data of ' + ref.name + ' with value \'' + ref.value.repr + '\'?',
        okText: 'Yes',
        okType: 'danger',
        cancelText: 'No',
        onOk() {
          self.visible = false;
          const delete_ref = {
            parent: {id: self.parentObjectID},
            ref_name: self.reference.name            
          }
          window.socket.emit("DLA_delete_ref", delete_ref, (res) => {
            const updateData = {
              value: {
                repr: res.repr,
                type: res.type
              }
            }
            self.$emit('update', updateData);
          });
          console.log('delete', ref);
        },
        onCancel() {
          console.log('Cancelled');
          self.visible = false;
        },
      });
    },    
    tableReady: function() {
      // called when closing the TableEditor
      this.visible = false;
    },
    tableUpdate: function(ref, data) {
      //console.log('RV table update data', ref, data);
      // forward event to ObjectProperties, where the ref data original comes from

      // TODO: this needs to move to the Table editor: as this is table specific for now
      const updateData = {
        value: {
          type: ref.type,
          repr: data.header.length + 'x' + data.rows.length + " " + ref.type
        }
      }
      this.$emit('update', updateData);
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