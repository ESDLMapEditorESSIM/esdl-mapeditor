import ControlStrategy from './apps/ControlStrategy';
import { mountSidebarComponent } from "./mounts";
import { useObject } from './composables/control_strategy';


window.control_strategy_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ControlStrategy);
}
