Vue.component('editable', {
    props: ["value"],
    data: function () {
        return {
            current_value: "",
            editing: false,
            saved_value: undefined,
        }
    },
    template: `
    <span>
        <span v-show="!editing">
            {{ current_value }}
        </span>
        <span v-show="editing">
            <input v-model="current_value">
        </span>
    </span>
    `,
    created: function() {
        this.reset();
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

