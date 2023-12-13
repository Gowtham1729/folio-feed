<template>
  <div>
    <h1>Welcome to the Folio Feed web application</h1>
    <h3>This nuxt js website is hosted on Google Cloud Platform</h3>
    <button @click="showNews()">Test</button>
    <div v-for="item in news" :key="item.id">
      <h3>{{ item.symbol }}</h3>
      <p>{{item.headline }}</p>
      <div v-html="item.summary"></div>
      <input type="checkbox" checked="checked" v-if="item.need_attention"> <span>Need attention</span>
      </div>

  </div>
</template>

<script>
export default {
  data() {
    return {
      news: []
    }
  },
  methods: {
    showNews() {
      fetch('/api/news/news/?format=json')
  .then(response => response.json())
          .then(data => this.news = data)
  .catch(error => console.error('Error:', error));
    }
  }
}

</script>


<style>
</style>
