/*
 * This work is based on original code developed and copyrighted by TNO 2020.
 * Subsequent contributions are licensed to you by the developers of such code and are
 * made available to the Project under one or several contributor license agreements.
 *
 * This work is licensed to you under the Apache License, Version 2.0.
 * You may obtain a copy of the license at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Contributors:
 *     TNO         - Initial implementation
 * Manager:
 *     TNO
 */

import {ref} from "vue";
import {displayNotification, NotificationType} from "@/utils/notification";

/**
 * @typedef {Object} LiveModelInterface
 * @property {string} lmi_id - The unique identifier for the live model interface.
 * @property {string} name - The name of the live model interface.
 * @property {string} description - The description of the live model interface.
 * @property {boolean} enabled - If true, the live model interface is enabled.
 * @property {boolean} can_be_disabled - If true, the live model interface can be disabled.
 */

/**
 * @typedef {Object} ApplicationContext
 * @property {string} application_id - The unique identifier for the application context.
 * @property {string} name - The name of the application context.
 * @property {LiveModelInterface[]} live_model_interfaces - The live model interfaces to activate.
 * @property {boolean|null} is_global - If true, the context is shown to all users.
 */

const defaultApplicationContext = {
    application_id: "default",
    name: "Default",
    toast_text: "Welcome to the default application context. This is the default context that is active when no other context is selected.",
};

// The active application context is the context that is currently active in the map.
const activeApplicationContext = ref(defaultApplicationContext);


export function useApplicationContext() {
    /**
     * Activate the given application context.
     * context menus.
     * @param applicationContext
     */
    async function activateApplicationContext(applicationContext) {
        const response = await fetch(`/context/applications/${applicationContext.application_id}/activate`, {
            method: 'POST'
        })
        if (!response.ok) {
            console.error('Error activating application context', response)
            alert('Error activating application context. Please check the console for more information.')
            return
        }
        activeApplicationContext.value = applicationContext;

        if (applicationContext.application_id !== defaultApplicationContext.application_id && applicationContext.toast_text) {
            displayNotification(NotificationType.INFO, applicationContext.toast_text);
        }

    }

    /**
     * Clear the active application context.
     */
    async function clearApplicationContext() {
        await activateApplicationContext(defaultApplicationContext);
    }

    /**
     * @typedef {Object} FetchApplicationContextsResponse
     * @property {ApplicationContext[]} application_contexts
     * @property {string} active_context_id
     * @property {string} selected_context_id
     */

    const fetchApplicationContexts = async () => {
        const response = await fetch('/context/applications')
        const jsonResponse = await response.json()
        const applicationContexts = jsonResponse.application_contexts
        // Always add the default context to the start.
        applicationContexts.unshift(defaultApplicationContext)
        // Find the active context and set it as the active context.
        const activeContext = applicationContexts.find(context => context.application_id === jsonResponse.active_context_id)
        if (activeContext) {
            activeApplicationContext.value = activeContext;
        } else {
            const selectedContext = applicationContexts.find(context => context.application_id === jsonResponse.selected_context_id)
            await activateApplicationContext(selectedContext || defaultApplicationContext);
        }
        return applicationContexts
    }

    return {
        activeApplicationContext,
        activateApplicationContext,
        clearApplicationContext,
        fetchApplicationContexts,
    }
}
