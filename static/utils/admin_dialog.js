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
import MapEditorDialog from "./MapEditorDialog.js";

class AdminDialog extends MapEditorDialog {

  toggle() {
    let jqueryNode = $('<div>').attr('id', 'admin_dialog_window').css({'height': '100%', 'display': 'flex', 'flex-direction': 'column'});
    const content = this.getContent();
    if (content) {
      return super.close()
    } else {
      this.setContent(jqueryNode.get(0));
      this.setTitle('Admin');
      window.activate_admin_settings();
      return super.open();
    }
  }
}

export default AdminDialog;
