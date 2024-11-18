class ESDLAnalytics extends MapEditorDialog {

  open() {
    let jqueryNode = $('<div>')
      .attr('id', 'esdl_analytics_window')
      .css({'display': 'flex', 'flex-direction': 'column', 'height': '100%'});
    this.setContent(jqueryNode.get(0));
    this.setTitle("ESDL Analytics");
    activate_esdl_analytics_window();

    return super.open();
  }

  // Extends _handleClose() method and emits the esdlAnalyticsIsClosed event,
  // which is listened by the AnalyticsPlot.vue component, to ensure the Ploty plot is properly cleaned up
  // after closing the esdl_analytics_window div.
  _handleClose() {
    console.debug("Closing ESDL Analytics");
    $(document).trigger('esdlAnalyticsIsClosed', true);

    return super.close();
  }
}