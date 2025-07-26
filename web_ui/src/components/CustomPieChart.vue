<template>
  <div class="pie-chart-container">
    <svg :width="size" :height="size" viewBox="0 0 100 100">
      <circle
        cx="50"
        cy="50"
        r="40"
        fill="none"
        stroke="#f0f0f0"
        stroke-width="8"
      />
      <circle
        cx="50"
        cy="50"
        r="40"
        fill="none"
        :stroke="getStrokeColor"
        stroke-width="8"
        :stroke-dasharray="dashArray"
        stroke-linecap="round"
        transform="rotate(-90 50 50)"
      />
      <text x="50" y="50" text-anchor="middle" dominant-baseline="middle">
        {{ percent }}%
      </text>
    </svg>
  </div>
</template>

<script>
export default {
  props: {
    percent: {
      type: Number,
      default: 0
    },
    size: {
      type: Number,
      default: 80
    }
  },
  computed: {
    dashArray() {
      const circumference = 2 * Math.PI * 40;
      const progress = (this.percent / 100) * circumference;
      return `${progress} ${circumference}`;
    },
    getStrokeColor() {
      if (this.percent < 20) return '#52c41a';
      if (this.percent < 50) return '#1890ff';
      if (this.percent < 70) return '#faad14';
      return '#f5222d';
    }
  }
};
</script>

<style scoped>
.pie-chart-container {
  display: inline-block;
}
</style>