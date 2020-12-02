import ControlStrategy from './apps/ControlStrategy';
import ObjectProperties from './apps/ObjectProperties';
import EDRAssets from './apps/EDRAssets';
import { mountSidebarComponent } from "./mounts";
import { useObject } from './composables/ObjectID';


window.control_strategy_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ControlStrategy);
}

window.object_properties_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ObjectProperties);
}

window.edr_asset_window = () => {
    mountSidebarComponent(EDRAssets);
}