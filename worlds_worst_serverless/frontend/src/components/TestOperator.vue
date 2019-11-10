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
                        <pre>
                        {{output}}
                        </pre>
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
              output: ''
            };
        },
        methods: {
            formSubmit(e) {
                e.preventDefault();
                let currentObj = this;
                let inputs = {
                  Player: {
                    name: 'TruckThunders',
                    character_class: 'Photonic',
                    max_hit_points: 500,
                    max_ex: 1000,
                    hit_points: 500,
                    ex: 100,
                    status_effects: [],
                    attack: this.attack,
                    enhanced: this.enhanced === 'true'
                  },
                  playerId: 'player_hash',
                  action: this.attack
                };
                this.axios.post('https://aiexd2xz1m.execute-api.us-east-1.amazonaws.com/dev/route', inputs)
                .then(function (response) {
                    currentObj.output = response.data;
                })
                .catch(function (error) {
                    currentObj.output = error;
                });
            }
        }
    }
</script>