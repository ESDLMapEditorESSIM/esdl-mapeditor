class ESDLAnalytics extends MapEditorDialog {

  open() {
    let jqueryNode = $('<div>').attr('id', 'esdl_analytics_window');
    this.setContent(jqueryNode.get(0));
    this.setTitle("ESDL Analytics");
    activate_esdl_analytics_window();

    return super.open();
  }
}