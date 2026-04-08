<script setup>
    import { onBeforeMount, onMounted, ref, getCurrentInstance } from 'vue';
    import bus from '../utils/EventBus.js';
    import { useStore } from '../store/index.js';
    import { storeToRefs } from 'pinia';

    const { showView, tableShow } = storeToRefs(useStore())
    bus.on('showView', data => {
        tableShow.value = false;
        showView.value = true;
    });
</script>
<template>
    <div class="viewPanel" v-if="showView">
        <img src="../assets/img/processview.jpg" class="viewImg"></img>
    </div>
</template>
<style scoped>
.viewPanel {
    width: 100%;
    height: 100%;
}

.viewImg {
    background-size: 100% 100%;
    width: 100%;
    height: 100%;
}
</style>