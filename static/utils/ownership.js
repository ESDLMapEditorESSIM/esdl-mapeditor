import MapEditorDialog from "./MapEditorDialog.js";

class OwnershipDialog extends MapEditorDialog {

    open() {
      let jqueryNode = $('<div>')
        .attr('id', 'ownership_window')
        .css({'display': 'flex', 'flex-direction': 'column', 'height': '100%'});
      this.setContent(jqueryNode.get(0));
      this.setTitle("Ownership dialog");
      activate_ownership_window();
  
      return super.open();
    }
  }

export default OwnershipDialog;
