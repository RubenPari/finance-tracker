import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import App from '../App.vue'

describe('App', () => {
  it('renders router-view content', () => {
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
