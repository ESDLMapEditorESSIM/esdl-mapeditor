<template>
  <div>
    <a-button type="primary" @click="showModal">
      <i :class="load_dashboard_icon" />
    </a-button>
    <a-modal v-model:visible="visible" :title="loadDashboardTitle" width="750px" @ok="handleOk">
      <a-card>
        <span>
          {{ loadDashboardText }}
        </span>
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
              :key="db.id"
            >
              {{ db.name }}
            </a-select-option>
          </a-select-opt-group>
        </a-select>
      </a-card>
    </a-modal>
  </div>
</template>

<script>

export default {
  name: "LoadDashboard",
  components: {
  },
  props: {
    dashboardsInfo: {
      type: Object,
      default: function() {
        return {};
      }
    },
    dashboardId: {
      type: String,
      default: ""
    },
    loadDashboardIcon: {
      type: String,
      default: "fas fa-folder-open"
    },
    loadDashboardTitle: {
      type: String,
      default: "Load Dashboard"
    },
    loadDashboardText: {
      type: String,
      default: "Select the existing dashboard configuration to overwrite from the list below"
    }
  },
  emits: ['update:dashboardId'],
  data() {
    return {
        visible: false,
        dashboard_id: this.dashboardId,
        load_dashboard_icon: this.loadDashboardIcon,
    }
  },
  watch: {
    dashboardId: function(new_value) {
      this.dashboard_id = this.dashboardId;
    }
  },
  computed: {
    dashboardList() {
      // console.log(this.dashboardsInfo);
      let db_list = [];
      if (this.dashboardsInfo.length == 0)
        return [];
      for (let g=0; g<this.dashboardsInfo.groups.length; g++) {
        // console.log(this.dashboardsInfo.groups[g]);
        let group = {
          name: this.dashboardsInfo.groups[g].name,
          dashboards: [],
        };
        for (const [db_id, db_info] of Object.entries(this.dashboardsInfo.dashboards)) {
          // console.log(db_info);
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
      // console.log(db_list);
      return db_list;
    }
  },
  methods: {
    showModal() {
      this.visible = true;
    },
    handleOk() {
      this.visible = false;
      this.$emit('update:dashboardId', this.dashboard_id);
    },
    filter_dashboards: function(input, option) {
      return option.props.title.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    },
  }
}

</script>