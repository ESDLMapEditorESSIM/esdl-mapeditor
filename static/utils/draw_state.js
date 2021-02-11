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


class DrawState {
    constructor() {
        this.handler = null;
        this.drawing = false;
        this.startLayer = null;
        this.endLayer = null;
        this.repeatMode = null;
    }




    startDrawConductor(startLayer, handler) {
        this.drawing = true;
        this.handler = handler;
        this.startLayer = startLayer;
        this.repeatMode = handler.options.repeatMode;
        if (!handler._enabled) // don't change repeatMode when using polyline button, only when clicking a marker port
            handler.options.repeatMode = false; // disable repeat mode
    }

    isDrawing() {
        return this.drawing;
    }

    /*
        returns InPort or OutPort or null
    */
    getStartPortType() {
        return this.startLayer.port_parent.type || null;
    }

    // returns always true if not drawing, otherwise it will return true if the start port is different from this port
    canConnect(port) {
        if (this.isDrawing()) {
            console.log('canConnect', port)
            return this.getStartPortType() !== port.type;
        } else {
            return true; // always return true if not drawing
        }
    }

    stopDrawConductor(endLayer) {
        this.drawing = false;
        this.endLayer = endLayer
    }

    isFinished() {
        return (this.startLayer !== null && this.endLayer !== null);
    }

     reset() {
        console.log('Reset draw state', this);
        this.drawing = false;
        this.startLayer = null;
        this.endLayer = null;
    }

    resetRepeatMode() {
        if (this.handler != null) {
            this.handler.options.repeatMode = this.repeatMode; // reset repeat mode
            this.handler = null;
            this.repeatMode = null;
        }
    }
}

var drawState = new DrawState(); // global draw state

