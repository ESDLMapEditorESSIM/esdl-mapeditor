<template>
  <h1>
    Control Strategy
  </h1>
  <a-space
    v-if="!isLoading"
    id="control-strategy"
    direction="vertical"
  >
    <a-select
      v-model:value="selected"
      style="width: 100%"
      :disabled="selected != 'None'"
    >
      <a-select-option
        v-for="cs in controlstrategies"
        :key="cs.value"
        :value="cs.value"
      >
        {{ cs.name }}
      </a-select-option>
    </a-select>

    <!------------------------------------>
    <!-- Driven by Demand/Supply        -->
    <!------------------------------------>
    <a-card
      v-if="selected=='DrivenByDemand' || selected=='DrivenBySupply' || selected=='DrivenByProfile'"
    >
      <a-space direction="vertical">
        <p>Select the port for the {{ selected }} control strategy</p>
        <a-radio-group v-model:value="selected_port">
          <a-radio
            v-for="p in ports_for_selected_strategy"
            :key="p.id"
            :value="p.id"
            class="radiostyle"
          >
            {{ p.repr }}
          </a-radio>
        </a-radio-group>
      </a-space>
    </a-card>

    <!------------------------------------>
    <!-- CurtailmentStrategy            -->
    <!------------------------------------>
    <a-card
      v-if="selected=='CurtailmentStrategy'"
    >
      <a-space
        direction="vertical"
      >
        Maximum power:
        <FancyNumberEdit
          v-model:value="max_power"
        />
        <!-- @update:value="(message) => handleUpdate('max_power', message)" -->
      </a-space>
    </a-card>

    <!------------------------------------>
    <!-- Driven by Profile              -->
    <!------------------------------------>
    <a-card
      v-if="selected=='DrivenByProfile'"
    >
      <a-space
        direction="vertical"
      >
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
        <!------------------------------------>
        <!-- Profile from database          -->
        <!------------------------------------>
        <a-space
          v-if="dbp_radio=='PfDb'"
          direction="vertical"
        >
          Sselect an existing profile from the profile database
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
        <!-- Profile from database          -->
        <!------------------------------------>
        <a-space
          v-if="dbp_radio=='PTE'"
          direction="vertical"
        >
          <ProfileTableEdit
            v-model:tableData="profile_table_data"
            @update="onPTUpdate"
          />
        </a-space>
      </a-space>
    </a-card>

    <!------------------------------------>
    <!-- StorageStrategy                -->
    <!------------------------------------>
    <a-card
      v-if="selected=='StorageStrategy'"
    >
      <a-space
        direction="vertical"
      >
        Set the storage strategy parameters:
        <table>
          <tr><td>Marginal charge costs</td><td><FancyNumberEdit v-model:value="marginal_charge_costs" /></td></tr>
          <tr><td>Marginal discharge costs</td><td><FancyNumberEdit v-model:value="marginal_discharge_costs" /></td></tr>
        </table>
      </a-space>
    </a-card>

    <!------------------------------------>
    <!-- PID Controller                 -->
    <!------------------------------------>
    <a-card
      v-if="selected=='PIDController'"
    >
      <a-space
        direction="vertical"
      >
        Set the PID controller parameters:
        <table>
          <tr><td>Kp:</td><td><FancyNumberEdit v-model:value="pid_kp" /></td></tr>
          <tr><td>Ki:</td><td><FancyNumberEdit v-model:value="pid_ki" /></td></tr>
          <tr><td>Kd:</td><td><FancyNumberEdit v-model:value="pid_kd" /></td></tr>
        </table>
        Select the sensor to use for the PID Controller
        <a-select
          v-model:value="pid_sensor"
          placeholder="Select the sensor"
          style="width: 100%"
        >
          <a-select-option
            v-for="pids in pid_sensor_list"
            :key="pids.id"
            :value="pids.id"
          >
            {{ pids.name }}
          </a-select-option>
        </a-select>
        <a-button
          disabled
        >
          Select sensor on the map
        </a-button>
        Setpoint:
        <FancyNumberEdit
          v-model:value="pid_setpoint"
        />
      </a-space>
    </a-card>

    <a-space>
      <a-button
        type="primary"
        :disabled="selected == 'None'"
        @click="remove"
      >
        Remove strategy
      </a-button>
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

    <!--
    <p>
      <small>
        <h3>Debug info:</h3>
        REST call result: {{ msg }}<br>
        Selected CS: {{ selected }}<br>
        Selected port: {{ selected_port }}<br>
        Max power: {{ max_power }}<br>
        DBprofile radio: {{ dbp_radio }}<br>
        <p
          v-for="p in profile_table_data"
          :key="p.id"
        >
          {{ p.datetime }}
        </p>
        <p>
          {{ JSON.stringify(profile_table_data) }}
        </p>
      </small>
    </p>
    -->
  </a-space>
</template>

<script>
import FancyNumberEdit from "../components/forms/FancyNumberEdit" 
import ProfileTableEdit from "../components/forms/ProfileTableEdit"
import { useObject } from '../composables/control_strategy'
import { v4 as uuidv4 } from 'uuid';

const defaultDbPoptions = [
  {id: "PfDb", name: "Profile from database"},
  {id: "PTE",  name: "Profile table editor"},
];

const portTypeForCS = {
  DrivenByDemand: 'OutPort',
  DrivenBySupply: 'InPort'
}

export const { currentObjectID } = useObject();   // Lars: Dit snap ik niet goed, waarom export?

export default {
  components: {
    FancyNumberEdit,
    ProfileTableEdit
  },
  data() {
    return {
      DbPOptions: defaultDbPoptions,
      dbp_radio: '',
      selected: 'None',
      controlstrategies: [
        {name: 'No Control Strategy selected', value: 'None'},
        {name: 'Driven by demand on OutPort', value: 'DrivenByDemand'},
        {name: 'Driven by supply on InPort', value: 'DrivenBySupply'},
        {name: 'Storage strategy', value: 'StorageStrategy'},
        {name: 'Curtailment strategy', value: 'CurtailmentStrategy'},
        {name: 'Driven by profile', value: 'DrivenByProfile'},
        {name: 'PID Controller', value: 'PIDController'},
      ],
      ports: [
        {id: 'P1', repr: 'Out E', type: 'OutPort'},
        {id: 'P2', repr: 'Out H', type: 'OutPort'},
      ],
      selected_port: "",
      max_power: 0,
      db_profile: "",
      db_profiles: [
        {id: 'P1', name: 'NEDU E1A (Huishoudens)'},
        {id: 'P2', name: 'NEDU E2A (...)'}
      ],
      profile_table_data: [
        {
          key: uuidv4(),
          datetime: "2020-01-01 00:00:00",
          profilevalue: 0.0
        },
        {
          key: uuidv4(),
          datetime: "2020-05-01 00:00:00",
          profilevalue: 1.0
        }
      ],
      marginal_charge_costs: 0.0,
      marginal_discharge_costs: 0.0,
      pid_kp: 0,
      pid_ki: 0,
      pid_kd: 0,
      pid_sensor: 'Select sensor...',
      pid_sensor_list: [
        {id: 'S1', name: 'Temperature Sensor S1'},
        {id: 'S2', name: 'Flow Sensor S1'},
      ], 
      pid_setpoint: 0,
      msg: "",
      isLoading: true
    }
  },
  computed: {
    ports_for_selected_strategy: function() {
      if (this.selected == 'DrivenByDemand' || this.selected == 'DrivenBySupply') {
        return this.ports.filter(p => p.type == portTypeForCS[this.selected]);
      }
      return this.ports;
    }
  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    handleUpdate: function(field, message) {
      console.log(message);
      this[field] = message;
    },
    getDataSocketIO: function() {
      console.log(currentObjectID.value);
      window.socket.emit('DLA_get_cs_info', {'id': currentObjectID.value}, (res) => {
        console.log(res);

        if (Object.keys(res['controlStrategy']).length !== 0) {
          this.selected = res['controlStrategy']['type']
          if ((res['controlStrategy']['type'] == 'DrivenByDemand') ||
              (res['controlStrategy']['type'] == 'DrivenBySupply') ||
              (res['controlStrategy']['type'] == 'DrivenByProfile')) {
            this.selected_port = res['controlStrategy']['port_id'];
          }
          if (res['controlStrategy']['type'] == 'StorageStrategy') {
            this.marginal_charge_costs = res['controlStrategy']['marginal_charge_costs'];
            this.marginal_discharge_costs = res['controlStrategy']['marginal_discharge_costs'];
          }
          if (res['controlStrategy']['type'] == 'CurtailmentStrategy') {
            this.max_power = res['controlStrategy']['max_power'];
          }
          if (res['controlStrategy']['type'] == 'PIDController') {
            this.pid_kp = res['controlStrategy']['kp'];
            this.pid_ki = res['controlStrategy']['ki'];
            this.pid_kd = res['controlStrategy']['kd'];
            this.pid_sensor = res['controlStrategy']['sensor_id'];
            this.pid_setpoint = res['controlStrategy']['pid_setpoint'];
          }
          if (res['controlStrategy']['type'] == 'DrivenByProfile') {
            let profile_info = res['controlStrategy']['profile'];
            if (profile_info.type == 'database') {
              this.dbp_radio = 'PfDb';
              this.db_profile = profile_info.id;
            }
            if (profile_info.type == 'datetime') {
              this.dbp_radio = 'PTE';
              this.profile_table_data = profile_info.list;
            }
          }
        } else {
          this.selected = 'None'
        }

        this.ports = res['ports']
        this.pid_sensor_list = res['sensor_list']
        this.db_profiles = res['profile_list']

        this.isLoading = false
      });
    },
    remove: function() {
      console.log('Pressed remove strategy')
      window.socket.emit('DLA_remove_cs', {'id': currentObjectID.value});
      this.selected = 'None'
    },
    save: function() {
      console.log('Pressed save');
      const result = this.buildResultInfo();
      console.log(result);
      window.socket.emit('DLA_set_cs', {'id': currentObjectID.value}, result);
      window.sidebar.hide();
    },
    cancel: function() {
      console.log('Pressed cancel');
      window.sidebar.hide();
    },
    buildResultInfo: function() {
      let result = {};
      result.type = this.selected;

      if ((result.type == 'DrivenByDemand') ||
          (result.type == 'DrivenBySupply') ||
          (result.type == 'DrivenByProfile')) {
        result.port_id = this.selected_port; 
      }
      if (result.type == 'StorageStrategy') {
        result.marginal_charge_costs = this.marginal_charge_costs;
        result.marginal_discharge_costs = this.marginal_discharge_costs;
      }
      if (result.type == 'CurtailmentStrategy') {
        result.max_power = this.max_power;
      }
      if (result.type == 'PIDController') {
        result.kp = this.pid_kp;
        result.ki = this.pid_ki;
        result.kd = this.pid_kd;
        result.sensor_id = this.pid_sensor;
        result.pid_setpoint = this.pid_setpoint;
      }
      if (result.type == 'DrivenByProfile') {
        result.profile = this.build_profile_info();
      }
      return result;
    },
    build_profile_info: function() {
      let profile_info = {}

      if (this.dbp_radio == 'PfDb') {
        profile_info.type = 'database';
        profile_info.id = this.db_profile;
      }
      if (this.dbp_radio == 'PTE') {
        profile_info.type = 'datetime';
        profile_info.list = this.profile_table_data;
      }
  
      return profile_info;
    },
    onPTUpdate: function(message) {
      console.log(message);
    }
  }
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