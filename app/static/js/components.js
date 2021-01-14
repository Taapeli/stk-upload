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

