<template>
  <h1>
    Sectors
  </h1>
  <a-space
    v-if="!isLoading"
    id="spc-sectors"
    direction="vertical"
    style="width: 100%"
  >
    <a-table
      :columns="sectorColumns"
      :data-source="sector_list"
      :row-key="(record, index) => {return record.id;}"
      size="middle"
      :pagination="paginationConfig"
      style="width: 100%"
    >
      <template #operation="{ record }">
        <div class="editable-row-operations">
          <a-space>
            <a @click="deleteSector(record.id)">
              <i class="fa fa-trash" />
            </a>
            <a @click="editSector(record.id)">
              <i class="fa fa-edit" />
            </a>
          </a-space>
        </div>
      </template>
    </a-table>
    <a-card style="width: 100%">
      <a-space
        direction="vertical"
        style="width: 100%"
      >
        <!------------------------------------>
        <!-- Sector name                   -->
        <!------------------------------------>
        <a-row :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Name</span>
          </a-col>
          <a-col :span="15">
            <a-input
              v-model:value="edit_sector.name"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Sector code                    -->
        <!------------------------------------>
        <a-row :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Code</span>
          </a-col>
          <a-col :span="15">
            <a-input
              v-model:value="edit_sector.code"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <!------------------------------------>
        <!-- Sector description             -->
        <!------------------------------------>
        <a-row :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>Description</span>
          </a-col>
          <a-col :span="15">
            <a-input
              v-model:value="edit_sector.description"
              size="small"
              @update:value="value_changed"
            />
          </a-col>
        </a-row>

        <a-space>
          <a-button
            :disabled="!edit_sector_changed"
            @click="addSector"
          >
            Add
          </a-button>
          <a-button
            :disabled="!(edit_sector_changed && edit_sector.id != '')"
            @click="saveSector"
          >
            Save
          </a-button>
          <a-button
            :disabled="edit_sector.id == ''"
            @click="cancelEditSector"
          >
            Cancel
          </a-button>
        </a-space>
      </a-space>
    </a-card>

    <a-card
      v-if="edr_sectors_list"
      style="width: 100%"
    >
      <a-space
        direction="vertical"
        style="width: 100%"
      >
        <a-row :gutter="[0, 4]" type="flex" align="middle">
          <a-col :span="9">
            <span>EDR Sectors</span>
          </a-col>
          <a-col :span="15">
            <a-select
              v-model:value="edr_sectors"
              style="width: 100%"
              :options="edr_sectors_list"
            />
          </a-col>
        </a-row>
        <a-space>
          <a-button
            :disabled="edr_sectors == undefined"
            @click="addEDRSectors"
          >
            Add
          </a-button>
        </a-space>
      </a-space>
    </a-card>
  </a-space>
</template>

<script>
import axios from 'axios'
import { v4 as uuidv4 } from 'uuid';

const sectorColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Code', dataIndex: 'code', key: 'code' },
  { title: '', slots: { customRender: 'operation' }},
];

const paginationConfig = { hideOnSinglePage: true };

export default {
  components: {},
  data() {
    return {
      isLoading: true,
      sector_list: [],
      sectorColumns,
      paginationConfig,

      clear_inputs: false,
      edit_sector_changed: false,
      edit_sector: {
        id: '',
        name: '',
        code: '',
        description: '',
      },

      edr_sectors_list: undefined,
      edr_sectors: undefined,
    }
  },
  mounted() {
    this.getData();
    this.getEDRSectorsList();
  },
  methods: {
    getData: function() {
      this.sector_list = window.get_sector_list(window.active_layer_id);
      this.isLoading = false;
    },
    addSector: function () {
      this.edit_sector.id = uuidv4();
      this.saveSector();
    },
    saveSector: function () {
      window.socket.emit('DLA_update_sector_info', {'id': this.edit_sector.id, 'sector_info': this.edit_sector},
        (res) => {
          window.set_sector_list(window.active_layer_id, res);
          this.getData();
        });
      this.clearInput();
    },
    cancelEditSector: function () {
      this.clearInput();
    },
    deleteSector: function(id) {
      let i=0;
      while (this.sector_list[i]['id'] != id) i++;
      this.sector_list.splice(i, 1);
      window.socket.emit('command', {cmd: 'remove_sector', sector_id: id});
    },
    editSector: function(id) {
      console.log(id);
      window.socket.emit('DLA_get_sector_info', {'id': id}, (res) => {
        this.edit_sector = res;
        console.log(res);
      });
    },
    value_changed: function(val) {
      if (!this.clear_inputs) {
        this.edit_sector_changed = true;
      }
    },
    clearInput: function() {
      this.clear_inputs = true;

      this.edit_sector.id = '';
      this.edit_sector.name = '';
      this.edit_sector.code = '';
      this.edit_sector.description = '';

      this.edit_sector_changed = false;
      this.clear_inputs = false;
    },
    getEDRSectorsList() {
      const path = '/edr_sectors';
      axios.get(path)
        .then((res) => {
          console.log(res);
          let result = res['data'];
          let sector_list = result['item_list'];
          this.edr_sectors_list = sector_list;
        });
    },
    addEDRSectors() {
      console.log('add EDR Sectors', this.edr_sectors);
      window.socket.emit('DLA_add_EDR_sectors', {'id': this.edr_sectors},
        (res) => {
          window.set_sector_list(window.active_layer_id, res);
          this.getData();
        });
    },
  }
}

</script>

