import ControlStrategy from './apps/ControlStrategy';
import ObjectProperties from './apps/ObjectProperties'
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