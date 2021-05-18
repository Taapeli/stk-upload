/*  Isotammi Genealogical Service for combining multiple researchers' results.
    Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
                             Timo Nallikari, Pekka Valta
    See the LICENSE file.
*/
Vue.component('editable', {
    props: ["value","name"],
    data: function () {
        return {
            current_value: "",
            editing: false,
            saved_value: "",
        }
    },
    template: `
    <span>
        <span v-show="!editing">
            {{ current_value }}
        </span>
        <span v-show="editing">
            <input v-model="current_value" :placeholder="name">
            <br>
        </span>
    </span>
    `,
    created: function() {
        this.reset();
        this.$root.editables.push(this);
    },
    methods: {
        reset: function() {
            Vue.nextTick(() => {
                this.current_value = this.value;
                this.saved_value = this.current_value;
            });
            this.editing = false;
        },
        edit: function() {
            this.saved_value = this.current_value;
            this.editing = true;
        },
        save: function() {
            this.editing = false;
        },
        cancel: function() {
            this.current_value = this.saved_value;
            this.editing = false;
        }
  }
});

