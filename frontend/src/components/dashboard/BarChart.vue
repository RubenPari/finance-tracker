<script setup lang="ts">
/**
 * BarChart - Monthly income vs. expense comparison bar chart.
 *
 * Renders a grouped bar chart with two datasets per month: expenses
 * (red) and income (green). Colours and styling are derived from the
 * shared `chartTheme` module so that they adapt to the current
 * dark/light theme. The y-axis starts at zero for an accurate visual
 * comparison of absolute values.
 *
 * @slot default - (none; self-contained chart)
 *
 * @example
 * ```vue
 * <BarChart :data="monthlyTrends" />
 * ```
 */
import type { MonthlyTrend } from '@/types'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js'
import { computed } from 'vue'
import { getChartDefaults, getCommonOptions } from '@/utils/chartTheme'

// Register only the Chart.js modules required for a bar chart.
ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

/**
 * Props accepted by the BarChart component.
 * @property {MonthlyTrend[]} data - Array of monthly trend data, each containing
 *   a `month_label` string, and numeric `expenses` and `income` values.
 */
const props = defineProps<{ data: MonthlyTrend[] }>()

/**
 * Computed chart datasets bound to the Chart.js bar renderer.
 *
 * Maps each `MonthlyTrend` entry into two datasets:
 * - Expenses: rendered with the semantic `expense` colour (red)
 * - Income: rendered with the semantic `income` colour (green)
 * Both use a `borderRadius: 2` for slightly rounded bar corners.
 */
const chartData = computed(() => {
  const defaults = getChartDefaults()
  return {
    labels: props.data.map((d) => d.month_label),
    datasets: [
      {
        label: 'Spese',
        data: props.data.map((d) => d.expenses),
        backgroundColor: defaults.expense,
        borderRadius: 2,
      },
      {
        label: 'Entrate',
        data: props.data.map((d) => d.income),
        backgroundColor: defaults.income,
        borderRadius: 2,
      },
    ],
  }
})

/**
 * Computed chart options, extending the shared common options.
 *
 * Inherits responsive sizing, legend/tooltip styling, and axis
 * configuration from `getCommonOptions()`, then overrides:
 * - Positions the legend at the top of the chart (multi-dataset display)
 * - Sets `beginAtZero: true` on the y-axis so bars scale from zero
 * - Appends a euro sign (`€`) to y-axis tick labels
 */
const options = computed(() => {
  const common = getCommonOptions()
  return {
    ...common,
    plugins: {
      ...common.plugins,
      legend: {
        ...common.plugins.legend,
        position: 'top' as const,
      },
    },
    scales: {
      ...common.scales,
      y: {
        ...common.scales.y,
        beginAtZero: true,
        ticks: {
          ...common.scales.y.ticks,
          callback: (v: unknown) => `${v}€`,
        },
      },
    },
  }
})
</script>

<template>
  <div class="h-64">
    <Bar :data="chartData" :options="options" />
  </div>
</template>