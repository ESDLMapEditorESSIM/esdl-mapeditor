<template>
  <div>
    <a-button type="primary" @click="showModal">
      Save dashboard
    </a-button>
    <a-modal v-model:visible="visible" title="Load dashboard" width="750px" @ok="handleOk">
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
    </a-modal>
  </div>
</template>

<script>

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
    },
    dashboardData: {
      type: Object,
      default: function() {
        return {};
      }
    }
  },
  data() {
    return {
        visible: false,
        dashboard_id: '',
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
      this.visible = false;
      // this.$emit('save', this.dashboard_id);
    },
    filter_dashboards: function(input, option) {
      return option.props.title.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    },
  }
}

</script>