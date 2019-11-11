<template>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">Welcome to the world's worst combat
                        system!</div>
                    <div class="card-body">
                        <form @submit="formSubmit">
                        <strong>Attack Type:</strong>
                        <input type="text" class="form-control"
                               v-model="attack">
                        <input type="checkbox" name="enhanced"
                               v-model="enhanced" true-value=true
                               false-value=false>Enhanced?<br>
                        <button class="btn btn-success">Submit</button>
                        </form>
                        <strong>{{result}}</strong>
                        <ul>
                            <li v-for="item in action_log" v-bind:key="item.id">
                                {{ item }}
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        data() {
            return {
              attack: '',
              enhanced: '',
              action_log: '',
              result: ''
            };
        },
        methods: {
            formSubmit(e) {
                e.preventDefault();
                let currentObj = this;
                let inputs = {
                  playerId: 'player_hash',
                  action: this.attack
                };
                this.axios.post('https://aiexd2xz1m.execute-api.us-east-1.amazonaws.com/dev/route', inputs)
                .then(function (response) {
                    let output = response.data;
                    currentObj.action_log = output['message'];
                    currentObj.result = output['Player'];
                })
                .catch(function (error) {
                    currentObj.action_log = '';
                    currentObj.result = error;
                });
            }
        }
    }
</script>