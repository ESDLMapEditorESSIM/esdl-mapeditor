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

class MapEditorDialog extends L.Control.Dialog {

  initialize(options) {
    this.options = JSON.parse(JSON.stringify(this.options));
    L.setOptions(this, options);

    if (!this.options.allowable_states) {
      this.options.allowable_states = ['custom', 'maximized', 'minimized'];
    }

    if (!this.options.state) {
      this.options.state = 'custom';   /* alternatives: maximized, minimized */
    }
  }

  _initLayout() {
    super._initLayout();

    if (this.options.state == 'minimized') {
      this._handleMinimize();
    }
    if (this.options.state == 'maximized') {
      this._handleMaximize();
    }

    let innerContainer = this._innerContainer;

    var className = "leaflet-control-dialog";

    if (this.options.allowable_states.includes('minimized')) {
      var minimizeNode = (this._minimizeNode = L.DomUtil.create(
        "div",
        className + "-minimize"
      ));
      var minimizeIcon = L.DomUtil.create("i", "fa fa-window-minimize");
      minimizeNode.appendChild(minimizeIcon);
      L.DomEvent.on(minimizeNode, "click", this._handleMinimize, this);
      innerContainer.appendChild(minimizeNode);
    }

    if (this.options.allowable_states.includes('maximized')) {
      var maximizeNode = (this._maximizeNode = L.DomUtil.create(
        "div",
        className + "-maximize"
      ));
      var maximizeIcon = L.DomUtil.create("i", "fa fa-window-maximize");
      maximizeNode.appendChild(maximizeIcon);
      L.DomEvent.on(maximizeNode, "click", this._handleMaximize, this);
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

    return super.close()
  }
  
  _handleMinimize() {
    let map_size = map.getSize();
    let height = 600;
    if (map_size.y < 1000) {
      height = map_size.y - 200;
      if (height < 0) height = 100;
    }
    let width = 300;

    super.setLocation([ map_size.y - height - 20, map_size.x - width - 20 ]);
    super.setSize([ width, height ]);

    this.options.state = 'minimized';
  }

  _handleMaximize() {
    let map_size = this._map.getSize();
    super.setLocation([ 10, 50 ]);
    super.setSize([ map_size.x - 300, map_size.y - 120 ]);

    this.options.state = 'maximized';
  }

  _handleMapResize() {
    if (this.options.state == 'minimized') this._handleMinimize();
    if (this.options.state == 'maximized') this._handleMaximize();
  }
};
