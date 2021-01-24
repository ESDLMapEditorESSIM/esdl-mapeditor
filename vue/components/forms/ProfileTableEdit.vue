<template>
  <a-space
    direction="vertical"
  >
    <a-table
      :columns="columns"
      :data-source="data"
      bordered
      size="middle"
    >
      <template
        #datetime="{ record }"
      >
        <a-date-picker
          format="YYYY-MM-DD HH:mm:ss"
          :default-value="moment(record.datetime, 'YYYY-MM-DD HH:mm:ss')"
          :show-time="{ defaultValue: moment('00:00:00', 'HH:mm:ss') }"
          @change="(date, dateString) => dateChange(date, dateString, record.key)"
        />
      </template>
      <template
        v-for="col in ['profilevalue']"
        #[col]="{ text, record }"
        :key="col"
      >
        <div :key="col">
          <a-input
            style="margin: -5px 0"
            :value="text"
            @change="e => handleChange(e.target.value, record.key, col)"
          />
        </div>
      </template>
      <template
        #operation="{ record }"
      >
        <div class="editable-row-operations">
          <span>
            <a
              @click="deleteRow(record.key)"
            >
              <i class="fa fa-trash" />
            </a>
          </span>
        </div>
      </template>
    </a-table>
    <a-button @click="addRow">
      Add
    </a-button>
  </a-space>
</template>

<script>
import moment from 'moment';
import { v4 as uuidv4 } from 'uuid';

const columns = [
  {
    title: 'Datetime',
    dataIndex: 'datetime',
    width: '70%',
    slots: { customRender: 'datetime' },
  },
  {
    title: 'Value',
    dataIndex: 'profilevalue',
    width: '20%',
    slots: { customRender: 'profilevalue' },
  },
  {
    title: '',
    width: '10%',
    slots: { customRender: 'operation' },
  },
];

export default {
  props: {
    tableData: {
      type: Array,
      default: function() {
        return [
          {
            key: uuidv4(),
            datetime: "2020-01-01 00:00:00",
            profilevalue: 0
          }
        ];
      }
    }
  },
  emits: ['update:tableData'],
  data() {
    return {
      data: this.tableData,
      columns,
      editingKey: '',
    };
  },
  methods: {
    moment,
    handleChange(value, key, column) {
      // console.log(value);
      const newData = [...this.data];
      const target = newData.filter(item => key === item.key)[0];
      if (target) {
        target[column] = value;
        this.data = newData;
        this.$emit('update:tableData', this.data);
      }
    },
    deleteRow(key) {
      const data = [...this.data]
      this.data = data.filter(item => item.key !== key)
      this.$emit('update:tableData', this.data);
    },
    addRow() {
      const newData = [...this.data];
      const addedRow = this.generateNewRow();
      this.data = [...newData, addedRow];
      // console.log(this.data);
      this.$emit('update:tableData', this.data);
    },
    generateNewRow() {
      return {
        key: uuidv4(),
        datetime: "2020-01-01 00:00:00",
        profilevalue: 0
      }
    },
    dateChange(date, dateString, rec_key) {
      // console.log(rec_key);
      // console.log(dateString);
      
      const newData = [...this.data];
      const target = newData.filter(item => rec_key === item.key)[0];
      if (target) {
        target['datetime'] = dateString;
        this.data = newData;
        this.$emit('update:tableData', this.data);
      }    
    },
  },
};
</script>
<style scoped>
.editable-row-operations a {
  margin-right: 8px;
}
</style>
