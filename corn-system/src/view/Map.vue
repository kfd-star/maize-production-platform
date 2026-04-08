<script setup>
import {
  onBeforeMount,
  onMounted,
  ref,
  getCurrentInstance,
  nextTick,
} from 'vue'
import { useRouter } from 'vue-router'
import { CirclePlus } from '@element-plus/icons-vue'
import bus from '../utils/EventBus.js'
import { useStore } from '@/store/index.js'
import * as maptalks from 'maptalks'
import { storeToRefs } from 'pinia'
const userstore = useStore()
const mapShow = userstore.mapShow
const mapUrl =
  import.meta.env.VITE_APP_ARCGIS_WMS_URL ||
  '/arcgis/services/corn/MapServer/WmsServer'
const tiandituToken = import.meta.env.VITE_APP_TIANDITU_TOKEN || ''

const createTiandituLayer = (id, layerName, subdomains) => {
  if (!tiandituToken) return null

  return new maptalks.TileLayer(id, {
    tileSystem: [1, -1, -180, 90],
    urlTemplate: `https://t{s}.tianditu.gov.cn/${layerName}_c/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${layerName}&STYLE=default&TILEMATRIXSET=c&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${tiandituToken}`,
    subdomains,
  })
}
bus.on('showMapData', (data) => {
  const layer = map.getLayer('vec')
  if (layer) {
    maptalks.GeoJSON.toGeometry(data, (geometry) => {
      geometry.updateSymbol({
        polygonFill: '#4f718a',
        polygonOpacity: 0.5,
        lineColor: '#62d409',
        lineWidth: 1,
      })
      geometry.addTo(layer)
      geometry.on('mouseover mouseout', (e) => {
        if (e.type === 'mouseover') {
          e.target.updateSymbol({
            polygonOpacity: 0.8,
            polygonFill: '#ad4455',
          })
        } else {
          e.target.updateSymbol({
            polygonOpacity: 0.5,
            polygonFill: '#4f718a',
          })
        }
      })
      // {"IDNEW":3,"FIELDNAME":"9-1(4-7)","AREADATA":33.9,"JMZ":"第七作业站","GLQ":"第四作业区","ZW":"有机大豆","ZW_1":"","PlotID":"23118150300002"}}
      const properties = geometry.getProperties()
      let content = ''
      for (const p in properties) {
        content += `${p}: ${properties[p]}</br>`
      }
      geometry.setInfoWindow({
        title: '地块属性',
        content: content,
        autoPan: true,
        autoOpenOn: 'click',
        autoCloseOn: 'click',
      })
    })
    const extent = layer.getExtent()
    map.fitExtent(extent)
  }
})

bus.on('showImageLayer', (data) => {
  const map = window.map
  const layer = map.getLayer(data.title)
  if (layer) {
    layer.show()
  } else {
    new maptalks.WMSTileLayer(data.title, {
      tileSystem: [1, -1, -180, 90],
      urlTemplate: mapUrl,
      crs: 'EPSG:4326',
      layers: data.name,
      styles: '',
      version: '1.3.0',
      format: 'image/png',
      transparent: true,
      uppercase: true,
    })
      .addTo(map)
      .bringToFront()
  }
  map.panTo(new maptalks.Coordinate([127, 48.2]))
})
onMounted(() => {
  const baseLayer = createTiandituLayer('tile', 'img', ['0', '1', '2', '3', '4', '5', '6', '7'])
  window.map = new maptalks.Map('map-container', {
    center: [127.0229786729472, 48.13774884311031],
    zoom: 12,
    minZoom: 1,
    maxZoom: 22,
    attribution: false,
    zoomControl: {
      position: 'top-right',
      zoomLevel: true,
    },
    scaleControl: {
      position: 'bottom-left',
      maxWidth: 100,
      metric: true,
      imperial: true,
    },
    spatialReference: {
      projection: 'EPSG:4326',
    },
    renderer: 'canvas',
    ...(baseLayer ? { baseLayer } : {}),
  })
  const annotationLayer = createTiandituLayer('zhuji', 'cia', ['1', '2', '3', '4', '5'])
  if (annotationLayer) {
    annotationLayer.addTo(window.map)
  } else {
    console.warn('VITE_APP_TIANDITU_TOKEN 未配置，地图标注图层已跳过。')
  }
  new maptalks.VectorLayer('vec').addTo(window.map)
})
</script>
<template>
  <div class="map-container" id="map-container"></div>
</template>
<style scoped>
.map-container {
  text-align: center;
  background: white;
  height: 100%;
  width: 100%;
}
</style>
