var ESSIM_table_editor_action = L.Toolbar2.Action.extend({
    options: {
        toolbarIcon: {html: '<div class="ui-icon ui-icon-calculator">&nbsp;</div>', tooltip: 'ESDL table editor'}
    },
    addHooks: function () {
        send_table_editor_request();
    }
});
var ESSIM_validation_action = L.Toolbar2.Action.extend({
    options: {
        toolbarIcon: {html: '<div class="ui-icon ui-icon-help">&nbsp;</div>', tooltip: 'ESSIM Validation'}
    },
    addHooks: function () {
        validate_for_ESSIM();
    }
});
var ESSIM_simulation_action = L.Toolbar2.Action.extend({
    options: {
        toolbarIcon: {html: '<div class="ui-icon ui-icon-circle-triangle-e">&nbsp;</div>', tooltip: 'Run ESSIM simulation'}
    },
    addHooks: function () {
        run_ESSIM_simulation_window();
    }
});
var ESSIM_kpi_results_action = L.Toolbar2.Action.extend({
    options: {
        toolbarIcon: {html: '<div class="ui-icon ui-icon-lightbulb">&nbsp;</div>', tooltip: 'ESSIM KPI results'}
    },
    addHooks: function () {
        calculate_ESSIM_KPIs();
    }
});
var ESSIM_load_animation_action = L.Toolbar2.Action.extend({
    options: {
        toolbarIcon: {html: '<div class="ui-icon ui-icon-video">&nbsp;</div>', tooltip: 'ESSIM animate load'}
    },
    addHooks: function () {
        animate_ESSIM_load();
    }
});


L.control.essim_control = function () {
    return new L.Toolbar2.Control({
        position: 'topleft',
        actions: [ESSIM_table_editor_action, ESSIM_validation_action, ESSIM_simulation_action,
//            ESSIM_sensitivity_analysis_action, ESSIM_kpi_results_action,
            ESSIM_load_animation_action]
    });
};