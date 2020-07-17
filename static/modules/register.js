import * as workflow from './workflow.js'

// Register all modules here, namespaced into window.mod.<module_name>.
// This allows them to be used outside a module, in the "plain" javascript code.
// This means that any exported entity can be called with
// modules.<module_name>.<function_name>, for example
// modules.workflow.start_new_workflow.
window.modules = {}
window.modules.workflow = workflow
