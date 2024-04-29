{{num}}--{{age}}

<script>
export default {
    name: 'tm',
    emits: ['get'],
    data(){
        return{
            num: 0,
        }
    },
    methods: {
        add(){
            this.num++
            $emit("get", this.num);
        }
    }
}
</script>