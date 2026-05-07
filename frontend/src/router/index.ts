import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes: [
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
			],
		},
	],
});

router.beforeEach(async (to, _from) => {
	const store = useAuthStore();
	const hasToken = !!store.accessToken;

	if (to.meta.requiresAuth && !hasToken) {
		return "/login";
	}
	if (to.meta.guest && hasToken) {
		return "/dashboard";
	}
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
