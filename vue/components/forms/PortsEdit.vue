<template>
  <a-table :columns="portColumns" :data-source="ports" size="middle">
    <template #expandedRowRender="{ record }">
      <p>Connected To:</p>
      <p>{{ record }}</p>
      <!--
      <a-table :columns="connectedToColumns" :data-source="" size="middle">
        <template #operation="{ record }">
          <div class="editable-row-operations">
            <span>
              <a @click="deleteConnection(record.key)">
                <i class="fa fa-trash"/>
              </a>
            </span>
          </div>
        </template>  
      </a-table>
      -->
    </template>
    <template #operation="{ record }">
      <div class="editable-row-operations">
        <span>
          <a @click="deletePort(record.key)">
            <i class="fa fa-trash"/>
          </a>
        </span>
      </div>      
    </template>
  </a-table>
</template>

<script>

const portColumns = [
  { title: 'Name', dataIndex: 'pname', key: 'pname' },
  { title: 'Type', dataIndex: 'ptype', key: 'ptype' },
  { title: 'Carrier', dataIndex: 'pcarr', key: 'pcarr' },
  { title: '', slots: { customRender: 'operation' }},
];

const connectedToColumns = [
  { title: 'Name', dataIndex: 'aname', key: 'aname' },
  { title: 'Type', dataIndex: 'atype', key: 'atype' },
  { title: '', slots: { customRender: 'operation' }},
];

export default {
  name: "PortsEdit",
  props: {
    portList: {
      type: Array,
      default: function() {
        return [
        ];
      }
    }
  },
  data() {
    return {
       ports: this.portList,
       portColumns,
       connectedToColumns
    }
  },
  mounted() {
    console.log(this.ports);
  },
  computed: {

  },
  methods: {
    deletePort(key) {
      console.log(key);
    },
    deleteConnection(key) {
      console.log(key);
    }
  }
}
</script>
