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

class KPIDashboard extends MapEditorDialog {

  open() {
    let jqueryNode = $('<div>').attr('id', 'kpi_dashboard_window');
    this.setContent(jqueryNode.get(0));
    this.setTitle("KPI dashboard");
    activate_kpi_dashboard_window();

    return super.open();
  }

}