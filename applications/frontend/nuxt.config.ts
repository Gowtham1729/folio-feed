// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: false },
  modules: ["nuxt-security"],
  security: {
    headers: {
      crossOriginResourcePolicy: 'cross-origin',
    },
  }
})
