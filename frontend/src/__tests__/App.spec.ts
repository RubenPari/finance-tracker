/**
 * Unit tests for the root App component.
 *
 * Verifies that the App component correctly renders a RouterView
 * for client-side route rendering.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import App from '../App.vue'

describe('App', () => {
  /** Ensures the root component contains a RouterView for route-based rendering. */
  it('renders router-view content', () => {
    // Create a minimal router with no routes (just to provide the plugin context)
    const router = createRouter({
      history: createWebHistory(),
      routes: [],
    })
    const wrapper = mount(App, {
      global: { plugins: [router] },
    })
    expect(wrapper.findComponent({ name: 'RouterView' }).exists()).toBe(true)
  })
})
