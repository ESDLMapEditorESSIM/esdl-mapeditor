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
import { useToast } from "vue-toastification";

/**
 * @typedef {Object} ApplicationContext
 * @property {string} application_id
 * @property {string} name
 * @property {string} [toast_text]
 */


const defaultApplicationContext = {
    application_id: "default",
    name: "Default",
    toast_text: "Welcome to the default application context. This is the default context that is active when no other context is selected.",
};

// The active application context is the context that is currently active in the map.
const activeApplicationContext = ref(defaultApplicationContext);
const toast = useToast();


export function useApplicationContext() {
    /**
     * Activate the given application context.
     * context menus.
     * @param applicationContext
     */
    async function activateApplicationContext(applicationContext) {
        if (activeApplicationContext.value) {
            await clearApplicationContext();
        }
        activeApplicationContext.value = applicationContext;
        if (activeApplicationContext.value.application_id === defaultApplicationContext.application_id) {
            return;
        }

        const response = await fetch(`/context/applications/${applicationContext.application_id}/activate`, {
            method: 'POST'
        })
        if (!response.ok) {
            console.error('Error activating application context', response)
            alert('Error activating application context. Please check the console for more information.')
            await clearApplicationContext();
            return
        }

        if (applicationContext.toast_text) {
            toast.info(applicationContext.toast_text);
        }

    }

    /**
     * Clear the active application context.
     */
    async function clearApplicationContext() {
        if (activeApplicationContext.value.application_id === defaultApplicationContext.application_id) {
            return;
        }
        const response = await fetch(`/context/applications/${activeApplicationContext.value.application_id}/clear`, {
            method: 'POST'
        })
        if (!response.ok) {
            console.error('Error clearing application context', response)
            alert('Error clearing application context. Please check the console for more information.')
        }
        activeApplicationContext.value = defaultApplicationContext;
    }

    /**
     * @typedef {Object} FetchApplicationContextsResponse
     * @property {ApplicationContext[]} application_contexts
     * @property {string} active_context_id
     */

    const fetchApplicationContexts = async () => {
        const response = await fetch('/context/applications')
        const jsonResponse = await response.json()
        const applicationContexts = jsonResponse.application_contexts
        applicationContexts.unshift(defaultApplicationContext)
        const activeContextId = jsonResponse.active_context_id || defaultApplicationContext.application_id
        if (activeContextId) {
            // Find the active context and set it as the active context.
            activeApplicationContext.value = applicationContexts.find(context => context.application_id === activeContextId)
        }
        // Always add the default context to the start.
        return applicationContexts
    }

    return {
        activeApplicationContext,
        activateApplicationContext,
        clearApplicationContext,
        fetchApplicationContexts,
    }
}
