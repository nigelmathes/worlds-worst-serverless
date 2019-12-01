<template>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <strong>You are TruckThunders, a Photonic. You can enhance attacks
                        of the type disrupt and area.<br></strong>
                    <weak>Enhanced Disrupt = Conveyor: Target is Prone. Next turn, block
                        loses to area<br></weak>
                    <weak>Enhanced Area = Distort Earth: Target is Disoriented. Next
                        turn, dodge loses to attack<br><br></weak>
                    <weak>Input any of the following commands below, and you may
                        choose to enhance them:<br></weak>
                    <strong>attack, block, dodge, disrupt, area<br><br></strong>
                    <div class="card-body">
                        <form @submit="formSubmit">
                        <strong>Attack Type:</strong>
                        <input type="text" class="form-control"
                               v-model="action">
                        <input type="checkbox" name="enhanced"
                               v-model="enhanced" true-value=true
                               false-value=false>Enhanced?<br>
                        <button class="btn btn-success">Submit</button>
                        </form>
                        <strong>
                            <br>Your HP: {{result.hit_points}}<br>
                            Your EX: {{result.ex}}<br>
                            Your Status Effects: {{result.status_effects}}<br>
                        </strong>
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
              action: '',
              enhanced: false,
              action_log: '',
              result: {
                  'hit_points': 500,
                  'ex': 0,
                  'status_effects': []
              }
            };
        },
        methods: {
            formSubmit(e) {
                e.preventDefault();
                let currentObj = this;
                let inputs = {
                  playerId: 'player_hash',
                  action: this.action,
                  enhanced: this.enhanced
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