/**
 * An example composable, broadcasting a shared state of a simple reactive counter,
 * and a function to increment this counter.
 * 
 * This can be used to test reactivity between components, but can be removed after
 * we have it up and running.
 */
import { readonly, computed, ref } from "vue";

// const esdl_items = ref({});

class EsdlAsset {
  // id: string
  // type: string
}

class ImplementingEsdlAsset extends EsdlAsset {
  // fields
  // name
  // port s
  constructor(json) {
    super();
    for (const [key, value] in json) {
      this[key] = value;
    }
  }
}

export function useEsdl() {
  const getEsdlAsset = (id) => {
    // if (id in esdl_items) {
    //   return esdl_items.value[id];
    // }
    // fetch from DB
    // fetch ...
    return ImplementingEsdlAsset() //ports: ...)
  }

//   const addEsdlAsset = (obj) {
//     esdl_items.value[obj.id] = id;
//     // POST je naar backend
//     add_object_to_layer(obj);
//   }

//   const updateEsdlAssetAttr = (asset, attr, value) {
//     //  send to backend
//     // POST asset attr value
//     if (id in esdl_items.value) {
//       return getEsdlAsset(id);
//     }
//     // Update in leaflet
//     return null;
//   }

//   const getAttrs = computed((id) => esdl_items[id]);

  return {
    getEsdlAsset,
    // updateEsdlAssetAttr,
    // getAttrs,
  }
}
