<script setup lang="ts">
/**
 * DonutChart - Category spending proportion donut chart.
 *
 * Renders a doughnut (ring) chart where each slice represents the
 * total spending for a category. Colours come from the category
 * data itself (`d.color`), while the border colour, fonts, and
 * legend/tooltip styling are derived from the shared `chartTheme`
 * module for dark/light theme consistency.
 *
 * Unlike the other chart components, this one does **not** use
 * `getCommonOptions()` because the doughnut chart has a different
 * configuration model (no `scales` — only `plugins`).
 *
 * @slot default - (none; self-contained chart)
 *
 * @example
 * ```vue
 * <DonutChart :data="categoryStats" />
 * ```
 */
import type { CategoryStats } from '@/types'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { computed } from 'vue'
import { getChartDefaults } from '@/utils/chartTheme'

// Register only the Chart.js modules required for a doughnut chart.
// ArcElement renders the arc slices; Tooltip and Legend provide interactivity.
ChartJS.register(ArcElement, Tooltip, Legend)

/**
 * Props accepted by the DonutChart component.
 * @property {CategoryStats[]} data - Array of category statistics, each containing
 *   a `category_name` string, a numeric `total` value, and a `color` hex string.
 */
const props = defineProps<{ data: CategoryStats[] }>()

/**
 * Computed chart dataset bound to the Chart.js doughnut renderer.
 *
 * Maps each `CategoryStats` entry to a label (`category_name`) and a
 * data value (`total`). Uses the category's own `color` for each slice
 * fill, and the theme's base `color` (text colour) as the shared border
 * colour to ensure the ring separators match the current theme.
 */
const chartData = computed(() => {
  const defaults = getChartDefaults()
  return {
    labels: props.data.map((d) => d.category_name),
    datasets: [
      {
        data: props.data.map((d) => d.total),
        backgroundColor: props.data.map((d) => d.color),
        borderWidth: 2,
        borderColor: defaults.color,
      },
    ],
  }
})

/**
 * Computed chart options specific to the doughnut chart.
 *
 * Does not use `getCommonOptions()` since doughnut charts have no
 * `scales` configuration. Sets up:
 * - Legend positioned on the right side with point-style markers
 * - Tooltip with a monospace body font for numeric values
 * - All colours and fonts from `getChartDefaults()` for theme awareness
 */
const options = computed(() => {
  const defaults = getChartDefaults()
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: defaults.color,
          font: defaults.font,
          usePointStyle: true,
          padding: 12,
        },
      },
      tooltip: {
        titleFont: defaults.font,
        bodyFont: { ...defaults.font, family: "'JetBrains Mono', monospace" },
        padding: 10,
        cornerRadius: 6,
      },
    },
  }
})
</script>

<template>
  <div class="h-64">
    <Doughnut :data="chartData" :options="options" />
  </div>
</template>