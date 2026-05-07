<script setup lang="ts">
/**
 * LineChart - Balance trend line chart for the dashboard.
 *
 * Renders a smooth (curved) line chart showing account balance over time,
 * with a semi-transparent fill beneath the line. Colours and styling are
 * derived from the shared `chartTheme` module so that they adapt to the
 * current dark/light theme.
 *
 * @slot default - (none; self-contained chart)
 *
 * @example
 * ```vue
 * <LineChart :data="balancePoints" />
 * ```
 */
import type { BalancePoint } from '@/types'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { computed } from 'vue'
import { getChartDefaults, getCommonOptions } from '@/utils/chartTheme'

// Register only the Chart.js modules required for a line chart.
// This keeps the bundle size minimal by excluding unused elements.
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

/**
 * Props accepted by the LineChart component.
 * @property {BalancePoint[]} data - Array of balance data points, each containing
 *   a `date` (ISO string) and a `balance` (numeric value in euros).
 */
const props = defineProps<{ data: BalancePoint[] }>()

/**
 * Computed chart dataset bound to the Chart.js line renderer.
 *
 * Maps each `BalancePoint` to a label (date truncated to YYYY-MM-DD) and
 * a balance value. Uses `chart1` from the theme defaults for the line
 * colour and a 20% opacity variant (`chart1 + '20'`) for the fill area.
 * `tension: 0.3` creates a smooth bezier curve; `pointRadius: 0` hides
 * individual data markers for a cleaner appearance.
 */
const chartData = computed(() => {
  const defaults = getChartDefaults()
  return {
    labels: props.data.map((d) => d.date.slice(0, 10)),
    datasets: [
      {
        label: 'Saldo',
        data: props.data.map((d) => d.balance),
        borderColor: defaults.chart1,
        backgroundColor: `${defaults.chart1}20`,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
      },
    ],
  }
})

/**
 * Computed chart options, extending the shared common options.
 *
 * Inherits responsive sizing, legend/tooltip styling, and axis
 * configuration from `getCommonOptions()`, then overrides:
 * - Disables the legend (single-dataset chart, no need for a key)
 * - Appends a euro sign (`€`) to y-axis tick labels
 */
const options = computed(() => {
  const common = getCommonOptions()
  return {
    ...common,
    plugins: {
      ...common.plugins,
      legend: {
        display: false,
      },
    },
    scales: {
      ...common.scales,
      y: {
        ...common.scales.y,
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
    <Line :data="chartData" :options="options" />
  </div>
</template>