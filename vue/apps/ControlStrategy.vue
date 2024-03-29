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
      :options="control_strategies"
      style="width: 100%"
      :disabled="selected != 'None'"
    />

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
          Select an existing profile from the profile database
          <a-select
            v-model:value="db_profile"
            :options="db_profiles"
            placeholder="Select a profile"
            style="width: 100%"
            @popupScroll="hide_jquery_ui_popup()"
          />
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
          :options="pid_sensor_list"
          placeholder="Select the sensor"
          style="width: 100%"
        />
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
        :disabled="selected === 'None'"
        @click="remove"
      >
        Remove strategy
      </a-button>
      <a-button
        type="primary"
        :disabled="!valid_input"
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
import { useObject } from '../composables/ObjectID'
import { v4 as uuidv4 } from 'uuid';

const defaultDbPoptions = [
  {id: "PfDb", name: "Profile from database"},
  {id: "PTE",  name: "Profile table editor"},
];

const portTypeForCS = {
  DrivenByDemand: 'OutPort',
  DrivenBySupply: 'InPort'
}

const { currentObjectID } = useObject();

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
      control_strategies: [
        {label: 'No Control Strategy selected', value: 'None'},
        {label: 'Driven by demand on OutPort', value: 'DrivenByDemand'},
        {label: 'Driven by supply on InPort', value: 'DrivenBySupply'},
        {label: 'Storage strategy', value: 'StorageStrategy'},
        {label: 'Curtailment strategy', value: 'CurtailmentStrategy'},
        {label: 'Driven by profile', value: 'DrivenByProfile'},
        {label: 'PID Controller', value: 'PIDController'},
      ],
      ports: [
      ],
      selected_port: "",
      max_power: 0,
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
      marginal_charge_costs: 0.0,
      marginal_discharge_costs: 0.0,
      pid_kp: 0,
      pid_ki: 0,
      pid_kd: 0,
      pid_sensor: 'Select sensor...',
      pid_sensor_list: [
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
    },
    valid_input: function() {
      // true == valid input
      // false == invalid input
      if (this.selected==='DrivenByDemand' || this.selected==='DrivenBySupply' || this.selected==='DrivenByProfile') {
          if (this.selected ==='DrivenByProfile') {
            return (this.selected_port !== '' && this.dbp_radio !== '');
          } else {
            return (this.selected_port !== '');
          }
      }
      return true; // default: user can save
    }

  },
  mounted() {
    this.getDataSocketIO();
  },
  methods: {
    handleUpdate: function(field, message) {
      // console.log(message);
      this[field] = message;
    },
    getDataSocketIO: function() {
      // console.log(currentObjectID.value);
      window.socket.emit('DLA_get_cs_info', {'id': currentObjectID.value}, (res) => {
        // console.log(res);

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
            if (this.pid_sensor == null) this.pid_sensor = 'Select sensor...';
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
        this.pid_sensor_list = res['sensor_list'].map((sensor) => {
          return {
            label: sensor.name,
            value: sensor.id,
          }
        });
        this.db_profiles = res['profile_list']

        this.isLoading = false
      });
    },
    remove: function() {
      // console.log('Pressed remove strategy')
      window.socket.emit('DLA_remove_cs', {'id': currentObjectID.value});
      this.selected = 'None';
      this.selected_port = '';
      this.dbp_radio = '';
    },
    save: function() {
      // console.log('Pressed save');
      const result = this.buildResultInfo();
      // console.log(result);
      window.socket.emit('DLA_set_cs', {'id': currentObjectID.value}, result);
      window.sidebar.hide();
    },
    cancel: function() {
      // console.log('Pressed cancel');
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
    hide_jquery_ui_popup: function() {
      window.jquery(".ui-tooltip-content").parents('div').remove();
    },
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