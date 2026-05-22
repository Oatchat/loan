<script setup>
import { RouterView } from 'vue-router'
import AppNavbar from '../components/layout/AppNavbar.vue'
</script>

<template>
  <div class="min-h-screen bg-ink-50">
    <AppNavbar />
    <main class="max-w-[1400px] mx-auto px-6 lg:px-12 py-8 lg:py-10">
      <RouterView v-slot="{ Component }">
        <Transition name="route" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>
