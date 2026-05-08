<script setup lang="ts">
/**
 * AppLayout - Main application layout with collapsible sidebar navigation.
 *
 * Wraps the entire authenticated app in a `SidebarProvider`, providing:
 * - A sidebar header with the Finance Tracker branding and logo
 * - A navigation menu (Dashboard, Transactions, Import, Categories, Budgets, Suggestions)
 *   with active-state highlighting based on the current route
 * - A sidebar footer displaying the current user's email and a logout button
 * - A top header bar containing a sidebar toggle and the theme mode switch
 * - The main content area that renders the matched `RouterView`
 *
 * Uses shadcn-vue sidebar primitives for collapsible behaviour,
 * and lucide-vue-next icons for navigation items.
 */
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  LayoutDashboard,
  ArrowLeftRight,
  Upload,
  Tags,
  PiggyBank,
  Lightbulb,
  LogOut,
  BarChart3,
  Repeat,
} from 'lucide-vue-next'
import ModeToggle from '@/components/ModeToggle.vue'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'

// Current route for active-nav highlighting
const route = useRoute()
// Auth store instance for user info and logout
const auth = useAuthStore()

// Sidebar navigation items: each entry maps a route path, display label, and icon component
const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/transactions', label: 'Transazioni', icon: ArrowLeftRight },
  { path: '/import', label: 'Importa', icon: Upload },
  { path: '/categories', label: 'Categorie', icon: Tags },
  { path: '/budgets', label: 'Budget', icon: PiggyBank },
  { path: '/suggestions', label: 'Suggerimenti', icon: Lightbulb },
  { path: '/subscriptions', label: 'Abbonamenti', icon: Repeat },
]
</script>

<template>
  <SidebarProvider>
    <Sidebar collapsible="icon">
      <SidebarHeader class="border-b border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" as-child>
              <RouterLink to="/dashboard" class="flex items-center gap-2">
                <div
                  class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground"
                >
                  <BarChart3 class="size-4" />
                </div>
                <div class="grid flex-1 text-left text-sm leading-tight">
                  <span class="truncate font-semibold">Finance Tracker</span>
                </div>
              </RouterLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem v-for="item in navItems" :key="item.path">
                <SidebarMenuButton as-child :is-active="route.path.startsWith(item.path)">
                  <RouterLink :to="item.path">
                    <component :is="item.icon" />
                    <span>{{ item.label }}</span>
                  </RouterLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" disabled>
              <span class="text-xs text-muted-foreground truncate">
                {{ auth.user?.email }}
              </span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarSeparator />
          <SidebarMenuItem>
            <SidebarMenuButton @click="auth.logout()">
              <LogOut class="size-4" />
              <span>Esci</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>

    <SidebarInset>
      <header class="flex h-12 items-center gap-2 border-b px-4">
        <SidebarTrigger class="-ml-1" />
        <Separator orientation="vertical" class="mr-2 h-4" />
        <div class="flex-1" />
        <ModeToggle />
      </header>

      <div class="flex-1 overflow-y-auto p-6">
        <RouterView />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>
