<template>
  <div>
    <h1>Welcome to the Folio Feed web application</h1>
    <h3>This nuxt js website is hosted on Google Cloud Platform</h3>

    <div>
      <input v-model="userInput" placeholder="Type something..."/>

      <button @click="addInputToList">OK</button>
    </div>

    <p><b>Echo: </b></p>
    <ul>
      <li v-for="(input, index) in inputsList" :key="index">
        {{ input }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  data() {
    return {
      userInput: '',
      inputsList: [],
    };
  },
  methods: {
    addInputToList() {
      if (this.userInput.trim()) {
        this.inputsList.push(this.userInput);
        this.userInput = '';
      }
    }
  }
};
</script>


<style>
button {
  margin-left: 8px;
}


input {
  margin-right: 8px;
}
</style>
