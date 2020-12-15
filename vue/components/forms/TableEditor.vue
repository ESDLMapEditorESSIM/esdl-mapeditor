<template>
  <a-modal
    :destroy-on-close="true"
    :title="title"
    :visible="visible"
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
            :value="text"
            @change="
              (e) => handleChange(e.target.value, record.key, col, index)
            "
          />
        </template>
      </a-table>
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

  data() {
    return {
      loading: true,
      error: false,
      table: {},
      colList: [],
    };
  },
  computed: {
  },
  mounted() {
    this.fetchTableData();
    console.log("Table editor mounted");
    
  },
  methods: {
    fetchTableData: function () {
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
          if (res === undefined) {
            this.error.message = "Failed loading table data";
          } else {
            // convert data to vue a-table data
            let header = [];
            for (let j = 0; j < res.header.length; j++) {
              header.push({
                title: res.header[j],
                dataIndex: "c" + j,
                key: j.toString(),
                slots: { customRender: "c" + j },
              });
              this.colList.push("c" + j);
            }
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
            console.log(this.table);
            console.log(this.colList);
          }
          this.loading = false;
        }
      );
    },
    handleChange: function (new_value, key, col, row_nr) {
      console.log("update table", new_value, key, col, row_nr);
      this.table.rows[row_nr][col] = new_value;
      console.log("new table data", this.table);
    },
    handleOk: function() {
        // update data
        let data = [...Array(this.table.rows.length)].map(() => Array(this.colList.length).fill(0));
        for (let i = 0; i<this.table.rows.length; i++) {
          for (let j = 0; j < this.colList.length; j++) {
            let value = parseFloat(this.table.rows[i][this.colList[j]]);
            data[i][j] = value;
          }
        }
        let header = this.table.map((x) => x.title);
        /*
        window.socket.emit("DLA_set_table_data",
        {
          parent_id: { id: this.parentObjectID },
          ref_name: this.reference.name,
          ref_type: this.reference.type,
          rows: data,
          header: header
        });
        */
        console.log(data);
        this.ready(); // close modal
    },
    handleCancel: function() {
        this.ready(); // close modal
    },
  },
};
</script>

<style>
</style>