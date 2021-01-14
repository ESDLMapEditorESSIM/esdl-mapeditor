<template>
  <h1>
    Enivromental Profiles
  </h1>
  <a-space
    v-if="!isLoading"
    id="env-profiles"
    direction="vertical"
  >
    <a-card>
      <a-row :gutter="[0, 24]">
        <a-col :span="24">
          <a-table :columns="envProfilesColumns" :data-source="env_profiles" size="middle" :pagination="paginationConfig">
            <template #operation="{ record }">
              <div v-if="record.type == 'InfluxDBProfile'" class="editable-row-operations">
                <span>
                  <a @click="editProfile(record.key)">
                    <i class="fa fa-database" />
                  </a>
                </span>
              </div>
              <div v-if="record.type == 'SingleValue'" class="editable-row-operations">
                <span>
                  <a @click="editProfile(record.key)">
                    <span class="fa-stack">
                      <span class="fa fa-circle-o fa-stack-2x"></span>
                      <strong class="fa-stack-1x">123</strong>
                    </span>
                  </a>
                </span>
              </div>
              <div class="editable-row-operations">
                <span>
                  <a @click="deleteProfile(record.key)">
                    <i class="fa fa-trash" />
                  </a>
                </span>
              </div>
            </template>
          </a-table>
        </a-col>
      </a-row>

      <a-row :gutter="[0, 24]">
        <a-col :span="24">
          <!------------------------------------>
          <!-- Profiles                       -->
          <!------------------------------------>
          How do you want to define the profile?
          <a-radio-group v-model:value="dbp_radio">
            <a-radio
              v-for="dbpo in DbPOptions"
              :key="dbpo.id"
              :value="dbpo.id"
              class="radiostyle"
            >
              {{ dbpo.name }}
            </a-radio>
          </a-radio-group>
        </a-col>
      </a-row>

      <a-row>

      </a-row>

      <a-row :gutter="[0, 24]">
        <a-col :span="24">
          <!------------------------------------>
          <!-- Profile from database          -->
          <!------------------------------------>
          <a-space
            v-if="dbp_radio=='PfDb'"
            direction="vertical"
          >
            Select an existing profile from the profile database
            <a-select
              v-model:value="db_profile"
              placeholder="Select a profile"
              style="width: 100%"
            >
              <a-select-option
                v-for="dbp in db_profiles"
                :key="dbp.id"
                :value="dbp.id"
              >
                {{ dbp.name }}
              </a-select-option>
            </a-select>
          </a-space>
          <!------------------------------------>
          <!-- Profile table editor           -->
          <!------------------------------------>
          <a-space
            v-if="dbp_radio=='PTE'"
            direction="vertical"
          >
            <ProfileTableEdit
              v-model:tableData="profile_table_data"
            />
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <a-space>
      <a-button
        type="primary"
        @click="save"
      >
        Save
      </a-button>
      <a-button
        type="primary"
        @click="cancel"
      >
        Cancel
      </a-button>
    </a-space>
  </a-space>
</template>

<script>
import FancyNumberEdit from "../components/forms/FancyNumberEdit"
import ProfileTableEdit from "../components/forms/ProfileTableEdit"
import { v4 as uuidv4 } from 'uuid';

const defaultDbPoptions = [
  {id: "PfDb", name: "Standard profile"},
  {id: "MPf",  name: "Custom database profile"},
  {id: "PTE",  name: "Profile table editor"},
];

const envProfilesColumns = [
  { title: 'Profile type', dataIndex: 'uiname', key: 'epname' },
  { title: '', slots: { customRender: 'operation' }},
];

export default {
  components: {
    FancyNumberEdit,
    ProfileTableEdit
  },
  data() {
    return {
      env_profiles: [],
      envProfilesColumns,
      DbPOptions: defaultDbPoptions,
      dbp_radio: '',
      db_profile: "",
      db_profiles: [
      ],
      profile_table_data: [
        {
          key: uuidv4(),
          datetime: "2020-01-01 00:00:00",
          profilevalue: 0.0
        }
      ],
      isLoading: true
    }
  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    getDataSocketIO: function() {
      window.socket.emit('DLA_get_environmental_profiles_info', (res) => {
        console.log(res);
        this.env_profiles = res['env_profiles'];
        this.isLoading = false;
      });
    },
    deleteProfile: function(key) {
    },
    editProfile: function(key) {
    },
  },
};

</script>

<style scoped>
  .cs_box {
    border-style: solid;
    border-width: 1px;
    padding: 5px;
    margin: 5px 0px;
  }

  .radiostyle {
    display: 'block';
    height: '30px';
  }
</style>