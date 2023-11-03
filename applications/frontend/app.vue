<template>
  <button @click="getNews">
    Get News
  </button>
  <div>
    {{ news }}
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'App',
  data() {
    return {
      news: []
    }
  },
  methods: {
    getNews() {
      axios.get('http://localhost:8000/api/news/')
        .then((response) => {
          this.news = response.data;
          console.log(this.news);
        })
        .catch((error) => {
          console.error(error)
        })
    }
  }
}
</script>
