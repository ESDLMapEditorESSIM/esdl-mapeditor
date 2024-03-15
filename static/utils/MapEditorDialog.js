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


class MapEditorDialog extends window.L.Control.Dialog {
  initialize(options) {
    if (options) {
      this.onClose = options.onClose;
    }
    super.initialize(options);

    if (!options.allowable_states) {
      this.allowable_states = ['custom', 'maximized', 'minimized'];
    } else {
      this.allowable_states = options.allowable_states;
    }

    this.state = options.state;
    if (!options.state) {
      this.state = 'custom';   /* alternatives: maximized, minimized */
    }
  }

  _initLayout() {
    super._initLayout();

    if (this.state == 'minimized') {
      this._handleMinimize();
    }
    if (this.state == 'maximized') {
      this._handleMaximize();
    }

    let innerContainer = this._innerContainer;

    var className = "leaflet-control-dialog";

    if (this.allowable_states.includes('minimized')) {
      var minimizeNode = (this._minimizeNode = window.L.DomUtil.create(
        "div",
        className + "-minimize"
      ));
      var minimizeIcon = window.L.DomUtil.create("i", "fa fa-window-minimize");
      minimizeNode.appendChild(minimizeIcon);
      window.L.DomEvent.on(minimizeNode, "click", this._handleMinimize, this);
      innerContainer.appendChild(minimizeNode);
    }

    if (this.allowable_states.includes('maximized')) {
      var maximizeNode = (this._maximizeNode = window.L.DomUtil.create(
        "div",
        className + "-maximize"
      ));
      var maximizeIcon = window.L.DomUtil.create("i", "fa fa-window-maximize");
      maximizeNode.appendChild(maximizeIcon);
      window.L.DomEvent.on(maximizeNode, "click", this._handleMaximize, this);
      innerContainer.appendChild(maximizeNode);
    }

    this._map.on('resize', () => {
      this._handleMapResize();
    });
  }

  close() {
    this._map.off('resize', () => {
      this._handleMapResize();
    });
    if (this.onClose) {
      this.onClose();
    }

    return super.close()
  }
  
  _handleMinimize() {
    const map_size = window.map.getContainer().getBoundingClientRect();
    let height = 600;
    if (map_size.height < 1000) {
      height = map_size.height - 200;
      if (height < 0) height = 100;
    }
    let width = 300;

    super.setLocation([ map_size.height - height - 20, map_size.width - width - 20 ]);
    super.setSize([ width, height ]);

    this.state = 'minimized';
  }

  _handleMaximize() {
    const map_size = window.map.getContainer().getBoundingClientRect();
    super.setLocation([ 10, 50 ]);
    // NOTE: Make sure to set the maxSize option large enough.
    super.setSize([ map_size.width - 300, map_size.height - 120 ]);

    this.state = 'maximized';
  }

  _handleMapResize() {
    if (this.state === 'minimized') this._handleMinimize();
    if (this.state === 'maximized') this._handleMaximize();
  }
}

export default MapEditorDialog;
