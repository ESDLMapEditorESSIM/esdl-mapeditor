/**
 *  This work is based on original code developed and copyrighted by TNO 2020.
 *  Subsequent contributions are licensed to you by the developers of such code and are
 *  made available to the Project under one or several contributor license agreements.
 *
 *  This work is licensed to you under the Apache License, Version 2.0.
 *  You may obtain a copy of the license at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Contributors:
 *      TNO         - Initial implementation
 *  Manager:
 *      TNO
 */

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
var ESSIM_sensitivity_analysis_action = L.Toolbar2.Action.extend({
    options: {
        toolbarIcon: {html: '<div class="ui-icon ui-icon-search">&nbsp;</div>', tooltip: 'ESSIM sensitivity analysis'}
    },
    addHooks: function () {
        essim_sensitivity_plugin.show_ESSIM_sensitivity_analysis_window();
    }
});
//var ESSIM_kpi_results_action = L.Toolbar2.Action.extend({
//    options: {
//        toolbarIcon: {html: '<div class="ui-icon ui-icon-lightbulb">&nbsp;</div>', tooltip: 'ESSIM KPI results'}
//    },
//    addHooks: function () {
//        calculate_ESSIM_KPIs();
//    }
//});
//var ESSIM_load_animation_action = L.Toolbar2.Action.extend({
//    options: {
//        toolbarIcon: {html: '<div class="ui-icon ui-icon-video">&nbsp;</div>', tooltip: 'ESSIM animate load'}
//    },
//    addHooks: function () {
//        animate_ESSIM_load();
//    }
//});


L.control.essim_control = new L.Toolbar2.Control({
//L.control.essim_control = function () {
//    return new L.Toolbar2.Control({
        position: 'topleft',
        actions: [
            // ESSIM_table_editor_action,
            ESSIM_validation_action,
            ESSIM_simulation_action,
            ESSIM_sensitivity_analysis_action]
            // , ESSIM_kpi_results_action, ESSIM_load_animation_action]
    });
