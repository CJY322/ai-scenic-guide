<script setup lang="ts">
import { computed } from 'vue'
import AdminDashboardView from './views/AdminDashboardView.vue'
import GuideChatView from './views/GuideChatView.vue'

const isAdminRoute = computed(() => window.location.pathname.startsWith('/admin'))
</script>

<template>
  <AdminDashboardView v-if="isAdminRoute" />
  <GuideChatView v-else />
</template>
