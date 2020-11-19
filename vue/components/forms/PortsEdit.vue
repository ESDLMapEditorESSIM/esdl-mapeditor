<template>
  <a-table :columns="portColumns" :data-source="ports" :rowKey="(record, index) => {return record.pid;}" size="middle">
    <template #expandedRowRender="{ record }">
      <p>Connected To:</p>
      <a-table :columns="connectedToColumns" :data-source="record.ct_list" :rowKey="(record, index) => {return record.pid;}" size="middle">
        <template #operation="{ record }">
          <div class="editable-row-operations">
            <span>
              <a @click="deleteConnection(record.opid+'&&'+record.pid)">
                <i class="fa fa-trash"/>
              </a>
            </span>
          </div>
        </template>  
      </a-table>
    </template>
    <template #operation="{ record }">
      <div class="editable-row-operations">
        <span>
          <a @click="deletePort(record.pid)">
            <i class="fa fa-trash"/>
          </a>
        </span>
      </div>      
    </template>
  </a-table>
  <div>
    <a-button type="primary" @click="showModal">
      Add port
    </a-button>
    <a-modal v-model:visible="visible" title="Add port" @ok="handleOk">
      <table>
        <tr>
          <td>Port type</td>
          <td>
            <a-select v-model:value="portType" style="width: 120px">
              <a-select-option key="InPort" value="InPort">InPort</a-select-option>
              <a-select-option key="OutPort" value="OutPort">OutPort</a-select-option>
            </a-select>
          </td>
        </tr>
        <tr>
          <td>Port name</td><td><a-input v-model:value="portName" /></td>
        </tr>
      </table>
    </a-modal>
  </div>
</template>

<script>
import { v4 as uuidv4 } from 'uuid';

const portColumns = [
  { title: 'Id', dataIndex: 'pid', key: 'pid' },
  { title: 'Name', dataIndex: 'pname', key: 'pname' },
  { title: 'Type', dataIndex: 'ptype', key: 'ptype' },
  { title: 'Carrier', dataIndex: 'pcarr', key: 'pcarr' },
  { title: '', slots: { customRender: 'operation' }},
];

const connectedToColumns = [
  { title: 'Id', dataIndex: 'pid', key: 'pid' },
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
    },
    objectID: String
  },
  data() {
    return {
      objectIdentifier: this.objectID,
      ports: this.portList,
      portColumns,
      connectedToColumns,
      portType: 'InPort',
      portName: 'Port',
      visible: false
    }
  },
  mounted() {
    // console.log(this.ports);
  },
  computed: {

  },
  methods: {
    deletePort(port_id) {
      // console.log(port_id);
      window.socket.emit('command', {
        'cmd': 'remove_port',
        'port_id': port_id
      });
      const port_list = [...this.ports];
      this.ports = port_list.filter(item => item.pid !== port_id);
    },
    deleteConnection(port_ids) {
      // console.log(port_ids);
      let components = port_ids.split("&&");
      let port_id = components[0];
      let connected_to_port_id = components[1];

      window.socket.emit('command', {
        'cmd': 'remove_connection_portids',
        'from_port_id': port_id,
        'to_port_id': connected_to_port_id
      });

      // remove connection from table
      for (let i=0; i<this.ports.length; i++) {
        if (this.ports[i].pid == port_id) {
          const ct_list = [...this.ports[i].ct_list];
          this.ports[i].ct_list = ct_list.filter(item => item.pid !== connected_to_port_id);
        }
      }
    },
    showModal() {
      this.visible = true;
    },
    handleOk() {
      let pid = uuidv4();
      let newPort = {
        pid: pid,
        ptype: this.portType,
        pname: this.portName,
        pcarr: null,
        ct_list: []
      }
      this.ports.push(newPort);
      window.socket.emit('command', {
        'cmd': 'add_port_with_id',
        'asset_id': this.objectIdentifier,
        'ptype': this.portType,
        'pname': this.portName,
        'pid': pid,
      });

      this.portName = 'Port';
      this.portType = 'InPort';
      this.visible = false;
    }
  }
}
</script>
