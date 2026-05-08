/**
 * Vue Router configuration with authentication guards.
 *
 * Defines all application routes, separating guest-only pages
 * (login, register) from authenticated pages (dashboard, transactions,
 * import, categories, budgets, suggestions). Authenticated routes
 * are nested under `AppLayout` for a consistent navigation shell.
 *
 * Navigation guards:
 * - Redirect unauthenticated users to `/login` for protected routes.
 * - Redirect authenticated users to `/dashboard` for guest-only routes.
 * - Auto-fetch the user profile on first navigation if tokens exist.
 */
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  // Use HTML5 history mode (clean URLs without hash)
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Guest-only routes (accessible only when NOT authenticated)
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/LoginView.vue"),
      meta: { guest: true },
    },
    {
      path: "/register",
      name: "register",
      component: () => import("@/views/RegisterView.vue"),
      meta: { guest: true },
    },
    // Authenticated routes wrapped in AppLayout
    {
      path: "/",
      component: () => import("@/components/layout/AppLayout.vue"),
      meta: { requiresAuth: true },
      redirect: "/dashboard",
      children: [
        {
          path: "dashboard",
          name: "dashboard",
          component: () => import("@/views/DashboardView.vue"),
        },
        {
          path: "transactions",
          name: "transactions",
          component: () => import("@/views/TransactionsView.vue"),
        },
        {
          path: "import",
          name: "import",
          component: () => import("@/views/ImportView.vue"),
        },
        {
          path: "categories",
          name: "categories",
          component: () => import("@/views/CategoriesView.vue"),
        },
        {
          path: "budgets",
          name: "budgets",
          component: () => import("@/views/BudgetsView.vue"),
        },
        {
          path: "suggestions",
          name: "suggestions",
          component: () => import("@/views/SuggestionsView.vue"),
        },
        {
          path: "subscriptions",
          name: "subscriptions",
          component: () => import("@/views/SubscriptionsView.vue"),
        },
      ],
    },
  ],
});

/**
 * Global navigation guard for authentication checks.
 *
 * On each navigation:
 * 1. Redirect to `/login` if the route requires auth and no token exists.
 * 2. Redirect to `/dashboard` if the route is guest-only and a token exists.
 * 3. Auto-fetch the user profile if a token exists but the user isn't loaded yet.
 *    If the fetch fails (expired token), log out and redirect to `/login`.
 */
router.beforeEach(async (to, _from) => {
  const store = useAuthStore();
  const hasToken = !!store.accessToken;

  // Protect authenticated routes
  if (to.meta.requiresAuth && !hasToken) {
    return "/login";
  }
  // Redirect logged-in users away from guest pages
  if (to.meta.guest && hasToken) {
    return "/dashboard";
  }
  // Hydrate user profile on first visit if not already loaded
  if (hasToken && !store.user) {
    try {
      await store.fetchUser();
    } catch {
      store.logout();
      return "/login";
    }
  }
});

export default router;
