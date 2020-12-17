<template>
  <a-modal
    :destroy-on-close="true"
    :title="title"
    :visible="computedVisible"
    width="750px"
    @ok="handleOk"
    @cancel="handleCancel"   
  >
    <p v-if="loading">Loading...</p>
    <div v-else>
      <p>{{ table.name }}</p>
      <a-table :columns="table.header" :data-source="table.rows" size="small">
        <template v-for="col in colList" #[col]="{ text, record, index }" :key="col">
          <a-input
            style="margin: -5px 0"
            size="small"
            :value="text"
            @change="
              (e) => handleChange(e.target.value, record.key, col, index)
            " 
          />
        </template>
        <template #operation="{ record }">
          <div v-if="record.value != ''">
            <a @click="deleteRow(record.key)">
              <i class="fa fa-trash" />
            </a>
          </div>
        </template>
      </a-table>
    </div>
    <div>
      <a-button size="small" type="primary" @click="addRow">
        <i class="fa fa-plus small-icon" /><span>&nbsp;Add row</span>
      </a-button>
    </div>
    <p v-if="error">
      {{ error.message }}
    </p>
  </a-modal>
</template>

<script>
export default {
  name: "TableEditor",
  props: {
    reference: {
      type: Object,
      default: function () {
        return {};
      },
    },
    parentObjectID: {
      type: String,
      default: "",
    },
    visible: Boolean,
    title: {
      type: String,
      default: "Table editor",
    },
    ready: {
      type: Function,
      required: true
    }
  },
  emits: ['update'],
  data() {
    return {
      loading: true,
      error: false,
      table: {},
      colList: [],
      backendData: {},
      nextRowId: 1
    };
  },
  computed: {
    computedVisible: function() {
      if (this.visible == true) {
        // fetch data
        this.fetchTableData();
        console.log("Table data refreshed");
      } 
      return this.visible;
    }
  },
  mounted() {
  },
  methods: {
    fetchTableData: function () {
      this.loading = true;
      // let self=this;
      window.socket.emit(
        "DLA_get_table_data",
        {
          parent_id: { id: this.parentObjectID },
          ref_name: this.reference.name,
          ref_type: this.reference.type,
        },
        (res) => {
          console.log(res);
          this.backendData = res;
          if (res === undefined) {
            this.error.message = "Failed loading table data";
          } else {
            this.convertData(this.backendData)
          }
          this.loading = false;
        }
      );
    },
    convertData: function(res) {
      // convert data to vue a-table data
      let header = [];
      for (let j = 0; j < res.header.length; j++) {
        header.push({
          title: res.header[j].title,
          id:  res.header[j].id,
          dataIndex: "c" + j,
          key: j.toString(),
          slots: { customRender: "c" + j },
        });
        this.colList.push("c" + j);
      }
      // add operation column
      header.push({
        title: "",          
        slots: { customRender: "operation" },
      });

      let rows = [];
      for (let row = 0; row < res.rows.length; row++) {
        let rowValue = { key: row.toString() };
        for (let i = 0; i < res.rows[row].length; i++) {
          rowValue["c" + i] = res.rows[row][i];
        }
        rows.push(rowValue);
      }
      this.table.header = header;
      this.table.rows = rows;
      this.table.name = res.name;
      this.table.description = res.description;
      this.nextRowId = this.table.rows.length;
      // todo: data source
      console.log('TE table data', this.table);
      console.log('TE colList', this.colList);
    },
    handleChange: function (new_value, key, col, row_nr) {
      console.log(new_value, key, col, row_nr);
      //this.table.rows[key][col] = new_value;
      const target = this.table.rows.find(item => item.key === key);
      if (target) {
        target[col] = new_value;
      }
    },
    handleOk: function() {
        // update data
        let data = [...Array(this.table.rows.length)].map(() => Array(this.colList.length).fill(0));
        for (let i = 0; i<this.table.rows.length; i++) {
          for (let j = 0; j < this.colList.length; j++) {
            let value = this.table.rows[i][this.colList[j]];
            if (value == '') value = 0.0;
            data[i][j] = value;
          }
        }
        let header = this.table.header.filter((x) => x.id != undefined).map((x) => { return {title: x.title, id: x.id} });
        let response = {
          parent_id: { id: this.parentObjectID },
          ref_name: this.reference.name,
          ref_type: this.reference.type,
          rows: data,
          header: header,
          name: this.table.name,
          description: this.table.description
        };
        window.socket.emit("DLA_set_table_data", response);
        console.log('TE update msg', response);
        this.$emit('update', response);
        //this.reference.value.repr = header.length + 'x' + rows.length + " " + this.reference.value.type;
        this.ready(); // close modal
    },
    handleCancel: function() {
      // reset data to original fetched data
      // not needed anymore? this.convertData(this.backendData);
      this.ready(); // close modal
    },
    deleteRow: function(key) {
      console.log(key);
      //this.table.rows.splice(key, 1);
      this.table.rows = this.table.rows.filter(item => item.key !== key);
    },
    addRow: function() {
      let rowValue = { key: this.nextRowId.toString() };
      for (let i = 0; i < this.colList.length; i++) {
          rowValue["c" + i] = 0.0;
      }
      this.nextRowId++;
      this.table.rows.push(rowValue);
    }
  },
};
</script>

<style>
</style>