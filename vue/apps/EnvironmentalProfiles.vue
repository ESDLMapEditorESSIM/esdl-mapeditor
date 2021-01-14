<template>
  <h1>
    Enivromental Profiles
  </h1>
  <a-space
    v-if="!isLoading"
    id="env-profiles"
    direction="vertical"
    style="width: 100%"
  >
    <a-card style="width: 100%">
      <a-row :gutter="[0, 24]">
        <a-col :span="24">
          <a-table :columns="envProfilesColumns" :data-source="env_profiles" size="middle" :pagination="paginationConfig" style="width: 100%">
            <template #operation="{ record }">
              <div class="editable-row-operations">
                <div v-if="record.type == 'InfluxDBProfile'">
                  <a-button size="small" @click="editProfile(record.key)">
                    <i class="fa fa-database small-icon" />
                  </a-button>
                </div>
                <div v-if="record.type == 'DatetimeProfile'">
                  <a-button size="small" @click="editProfile(record.key)">
                    <i class="fa fa-table small-icon" />
                  </a-button>
                </div>
                <div v-if="record.type == 'SingleValue'">
                  <a-button size="small" @click="editProfile(record.key)">
                    123
                  </a-button>
                </div>
                <div v-if="record.type != 'Unset'">
                  <a-button size="small" @click="deleteProfile(record.key)">
                    <i class="fa fa-trash small-icon" />
                  </a-button>
                </div>
                <div v-if="record.type == 'Unset'">
                  <a-button size="small" @click="addProfile(record.key)">
                    <i class="fa fa-plus small-icon" />
                  </a-button>
                </div>
              </div>
            </template>
          </a-table>
        </a-col>
      </a-row>

      <a-row v-if="action == 'add_profile'" :gutter="[0, 24]">
        <a-col :span="24">
          <!------------------------------------>
          <!-- Profiles                       -->
          <!------------------------------------>
          How do you want to define the profile?
          <a-radio-group v-model:value="profile_type_radio">
            <a-radio
              v-for="dbpo in profileTypeOptions"
              :key="dbpo.id"
              :value="dbpo.id"
              class="radiostyle"
            >
              {{ dbpo.name }}
            </a-radio>
          </a-radio-group>
        </a-col>
      </a-row>

      <a-row v-if="action == 'edit_profile' || (action == 'add_profile' && profile_type_radio !== '')" :gutter="[0, 24]">
        <a-col :span="24">
          <a-space direction="vertical">
            <!------------------------------------>
            <!-- Profile from database          -->
            <!------------------------------------>
            <template
              v-if="profile_type_radio=='PfDb'"
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
            </template>
            <!------------------------------------>
            <!-- Profile table editor           -->
            <!------------------------------------>
            <template v-if="profile_type_radio=='PTE'">
              <ProfileTableEdit
                v-model:tableData="profile_table_data"
              />
            </template>
            <!------------------------------------>
            <!-- Single value profile           -->
            <!------------------------------------>
            <template v-if="profile_type_radio=='PSV'">
              <a-row :gutter="[0, 4]" type="flex" align="middle">
                <a-col :span="9">
                  <span title="">Value</span>
                </a-col>
                <a-col :span="15">
                  <FancyNumberEdit
                    v-model:value="sv_value"
                    size="small"
                  />
                </a-col>
              </a-row>
            </template>

            <a-row :gutter="[0, 24]">
              <a-col :span="24">
                <a-space>
                  <a-button type="primary" @click="save">Save</a-button>
                  <a-button type="primary" @click="cancel">Cancel</a-button>
                </a-space>
              </a-col>
            </a-row>
          </a-space>
        </a-col>
      </a-row>
    </a-card>
  </a-space>
</template>

<script>
import FancyNumberEdit from "../components/forms/FancyNumberEdit"
import ProfileTableEdit from "../components/forms/ProfileTableEdit"
import { v4 as uuidv4 } from 'uuid';

const defaultProfileTypeOptions = [
  {id: "PfDb", name: "Standard profile"},
  {id: "PTE",  name: "Profile table editor"},
  {id: "PSV",  name: "Single value"},
];

const envProfilesColumns = [
  { title: 'Profile type', dataIndex: 'uiname', key: 'epname' },
  { title: '', width: '30%', slots: { customRender: 'operation' }},
];

const paginationConfig = { hideOnSinglePage: true};

export default {
  components: {
    FancyNumberEdit,
    ProfileTableEdit
  },
  data() {
    return {
      env_profiles: [],
      envProfilesColumns,
      paginationConfig,
      profileTypeOptions: defaultProfileTypeOptions,
      profile_type_radio: '',
      db_profile: "",
      db_profiles: [],
      profile_table_data: [
        {
          key: uuidv4(),
          datetime: "2020-01-01 00:00:00",
          profilevalue: 0.0
        }
      ],
      sv_value: undefined,
      isLoading: true,
      action: '',
      current_profile_key: '',
    }
  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    camelCase: function(str) {
      // TODO: import this function from utils.js and let utils.js export functions
      return window.camelCaseToWords(str);
    },
    getDataSocketIO: function() {
      window.socket.emit('DLA_get_environmental_profiles_info', (res) => {
        console.log(res);
        this.env_profiles = res['env_profiles'];
        this.db_profiles = res['standard_profiles_list'];
        this.isLoading = false;
      });
    },
    deleteProfile: function(key) {
      for (let i=0; i<this.env_profiles.length; i++) {
        if (this.env_profiles[i]["key"] == key) {
          this.env_profiles[i]["type"] = "Unset";
          this.env_profiles[i]["value"] = "";
        }
      }
      this.current_profile_key = ''
      this.action = '';
    },
    editProfile: function(key) {
      this.current_profile_key = key;
      for (let i=0; i<this.env_profiles.length; i++) {
        if (this.env_profiles[i]["key"] == key) {
          if (this.env_profiles[i]["type"] == "SingleValue") {
            this.sv_value = parseFloat(this.env_profiles[i]["value"]);
            this.profile_type_radio = 'PSV';
          } else if (this.env_profiles[i]["type"] == "InfluxDBProfile") {
            this.db_profile = this.env_profiles[i]["profile_id"];
            this.profile_type_radio = 'PfDb';
          } else if (this.env_profiles[i]["type"] == "DatetimeProfile") {
            this.profile_table_data = this.env_profiles[i]["data"];
            this.profile_type_radio = 'PTE';
          }
        }
      }
      this.action = 'edit_profile';
    },
    addProfile: function(key) {
      this.profile_type_radio = '';
      this.sv_value = undefined;
      this.db_profile = '';
      this.profile_table_data = [];
      this.current_profile_key = key;
      this.action = 'add_profile';
    },
    save: function() {
      for (let i=0; i<this.env_profiles.length; i++) {
        if (this.env_profiles[i]["key"] == this.current_profile_key) {
          if (this.profile_type_radio == 'PSV') {
            this.env_profiles[i]["value"] = this.sv_value.toString();
            this.env_profiles[i]["type"] = "SingleValue";
          } else if (this.profile_type_radio == 'PfDb') {
            this.env_profiles[i]["profile_id"] = this.db_profile;
            this.env_profiles[i]["type"] = "InfluxDBProfile";
          } else if (this.profile_type_radio == 'PTE') {
            this.env_profiles[i]["data"] = this.profile_table_data;
            this.env_profiles[i]["type"] = "DatetimeProfile";
          }
        }
      }
      this.current_profile_key = ''
      this.action = '';
    },
    cancel: function() {
      this.current_profile_key = ''
      this.action = '';
    }
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

  .editable-row-operations {
    overflow: hidden;
  }
  .editable-row-operations div {
    float: left;
  }
</style>