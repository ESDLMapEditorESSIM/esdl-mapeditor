<template>
  <div>
    <a-button type="primary" @click="showModal">
      Save dashboard
    </a-button>
    <a-modal v-model:visible="visible" title="Save dashboard" width="750px" @ok="handleOk">
      <a-card style="width: 100%">
        <a-radio-group v-model:value="save_as_new_or_existing">
          <a-radio key="new" value="new" class="radiostyle">
            Save as a new dashboard
          </a-radio>
          <a-radio key="existing" value="existing" class="radiostyle">
            Save as an existing dashboard
          </a-radio>
        </a-radio-group>
      </a-card>

      <template v-if="save_as_new_or_existing == 'existing'">
        <a-card>
          <span>
            Select the existing dashboard configuration to overwrite from the list below
          </span>
          <a-space
            direction="vertical"
            style="width: 100%"
          >
            <a-select
              v-model:value="dashboard_id"
              show-search
              placeholder="Select dashboard..."
              style="width: 100%"
            >
              <a-select-opt-group
                v-for="db_group in dashboardList"
                :key="db_group.name"
              >
                <template #label>
                  <span>
                    {{ db_group.name }}
                  </span>
                </template>
                <a-select-option
                  v-for="db in db_group.dashboards"
                  :key="db_group.name + '___' + db.id"
                >
                  {{ db.name }}
                </a-select-option>
              </a-select-opt-group>
            </a-select>
          </a-space>
        </a-card>
      </template>

      <template v-if="save_as_new_or_existing == 'new'">
        <a-card>
          <span>
            Enter the new dashboard configuration name
          </span>
          <a-input v-model:value="dashboard_name" />
          <span>
            Select the group to which the dashboard configuration should be saved
          </span>
          <a-select
            v-model:value="dashboard_group"
            show-search
            placeholder="Select dashboard group..."
            style="width: 100%"
          >
            <a-select-option
              v-for="db_group in dashboardList"
              :key="db_group.name"
            >
              {{ db_group.name }}
            </a-select-option>
          </a-select>
        </a-card>
      </template>
      <a-button @click="handleSave">
        Save
      </a-button>
    </a-modal>
  </div>
</template>

<script>
import { v4 as uuidv4 } from 'uuid';

export default {
  name: "SaveDashboard",
  components: {
  },
  props: {
    dashboardsInfo: {
      type: Object,
      default: function() {
        return {};
      }
    }
  },
  emits: ['handle-save'],
  data() {
    return {
        visible: false,
        dashboard_id: '',
        save_as_new_or_existing: '',
        dashboard_name: '',
        dashboard_group: '',
    }
  },
  computed: {
    dashboardList() {
      console.log(this.dashboardsInfo);
      let db_list = [];
      if (this.dashboardsInfo.length == 0)
        return [];
      for (let g=0; g<this.dashboardsInfo.groups.length; g++) {
        let group = {
          name: this.dashboardsInfo.groups[g].name,
          dashboards: [],
        };
        for (const [db_id, db_info] of Object.entries(this.dashboardsInfo.dashboards)) {
          console.log(db_id, db_info);
          if (db_info.setting_type == this.dashboardsInfo.groups[g].setting_type) {
            if (db_info.setting_type == 'project') {
              if (db_info.project_name != this.dashboardsInfo.groups[g].project_name) continue;
            }
            db_info.id = db_id;
            group.dashboards.push(db_info);
          }
        }
        db_list.push(group);
      }
      console.log(db_list);
      return db_list;
    }
  },
  mounted() {
  },
  methods: {
    showModal() {
      this.visible = true;
    },
    handleOk() {
      this.handleSave();
      this.visible = false;
      // this.$emit('save', this.dashboard_id);
    },
    filter_dashboards: function(input, option) {
      return option.props.title.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    },
    handleSave() {
      console.log(this.dashboardData);
      if (this.save_as_new_or_existing == 'new') {
        this.dashboard_id = uuidv4();
      } else {
        let tmp_db_id = this.dashboard_id;   // format is: group_name__db_id
        this.dashboard_group = tmp_db_id.split('__')[0];
        this.dashboard_id = tmp_db_id.split('__')[1];
      }
      this.$emit('handle-save', {
        id: this.dashboard_id,
        name: this.dashboard_name,
        group: this.dashboard_group
      });
    }
  }
}

</script>