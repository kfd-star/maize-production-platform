<template>
  <div class="geojson-map-container">
    <div ref="mapContainer" class="map-container"></div>
    <div v-if="loading" class="map-loading">
      <i class="el-icon-loading"></i>
      <span>加载地图中...</span>
    </div>
    <div v-if="error" class="map-error">
      <i class="el-icon-warning"></i>
      <span>{{ error }}</span>
    </div>
    <div v-if="legendVisible && yieldRange" class="map-legend">
      <div class="legend-title">产量 (kg/ha)</div>
      <div class="legend-gradient">
        <div 
          v-for="(color, index) in legendColors" 
          :key="index"
          class="legend-item"
          :style="{ backgroundColor: color }"
        >
          <span class="legend-label">{{ legendLabels[index] }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as maptalks from 'maptalks'

const props = defineProps({
  geojson: {
    type: Object,
    default: null
  },
  geojsonUrl: {
    type: String,
    default: ''
  },
  height: {
    type: String,
    default: '500px'
  },
  showLegend: {
    type: Boolean,
    default: true
  }
})

const mapContainer = ref(null)
const loading = ref(false)
const error = ref('')
const map = ref(null)
const vectorLayer = ref(null)
const legendVisible = ref(false)
const yieldRange = ref(null)
const legendColors = ref([])
const legendLabels = ref([])
const tiandituToken = import.meta.env.VITE_APP_TIANDITU_TOKEN || ''

const createTiandituLayer = (id, layerName, subdomains) => {
  if (!tiandituToken) return null

  return new maptalks.TileLayer(id, {
    tileSystem: [1, -1, -180, 90],
    maxAvailableZoom: 18,
    urlTemplate: `https://t{s}.tianditu.gov.cn/${layerName}_c/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${layerName}&STYLE=default&TILEMATRIXSET=c&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${tiandituToken}`,
    subdomains,
  })
}

// 根据产量值计算颜色（从低到高：蓝色->绿色->黄色->红色）
const getColorByYield = (yieldValue, minYield, maxYield) => {
  if (minYield === maxYield) {
    return '#4CAF50' // 绿色
  }
  
  const ratio = (yieldValue - minYield) / (maxYield - minYield)
  
  // 使用渐变色：蓝色(低) -> 青色 -> 绿色 -> 黄色 -> 红色(高)
  if (ratio < 0.25) {
    // 蓝色到青色
    const r = 0
    const g = Math.floor(ratio * 4 * 255)
    const b = 255
    return `rgb(${r}, ${g}, ${b})`
  } else if (ratio < 0.5) {
    // 青色到绿色
    const r = 0
    const g = 255
    const b = Math.floor((1 - (ratio - 0.25) * 4) * 255)
    return `rgb(${r}, ${g}, ${b})`
  } else if (ratio < 0.75) {
    // 绿色到黄色
    const r = Math.floor((ratio - 0.5) * 4 * 255)
    const g = 255
    const b = 0
    return `rgb(${r}, ${g}, ${b})`
  } else {
    // 黄色到红色
    const r = 255
    const g = Math.floor((1 - (ratio - 0.75) * 4) * 255)
    const b = 0
    return `rgb(${r}, ${g}, ${b})`
  }
}

// 初始化地图
const initMap = async () => {
  // 容器不存在或已经有地图实例时，不重复初始化
  if (!mapContainer.value || map.value) return
  
  try {
    loading.value = true
    error.value = ''
    
    await nextTick()
    
    // 创建地图实例
    const baseLayer = createTiandituLayer('base', 'img', ['0', '1', '2', '3', '4', '5', '6', '7'])
    map.value = new maptalks.Map(mapContainer.value, {
      center: [115.127, 33.691], // 默认中心点，后续会根据数据自动调整
      zoom: 13,
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
        imperial: false,
      },
      spatialReference: {
        projection: 'EPSG:4326',
      },
      renderer: 'canvas',
      ...(baseLayer ? { baseLayer } : {}),
    })
    
    // 添加标注层
    const annotationLayer = createTiandituLayer('annotation', 'cia', ['1', '2', '3', '4', '5'])
    if (annotationLayer) {
      annotationLayer.addTo(map.value)
    } else {
      console.warn('VITE_APP_TIANDITU_TOKEN 未配置，GeoJSON 地图标注图层已跳过。')
    }
    
    // 创建矢量图层
    vectorLayer.value = new maptalks.VectorLayer('vector').addTo(map.value)
    
    loading.value = false
  } catch (e) {
    console.error('地图初始化失败:', e)
    error.value = '地图初始化失败: ' + e.message
    loading.value = false
  }
}

// 加载GeoJSON数据
const loadGeoJSON = async (geojsonData) => {
  if (!map.value || !vectorLayer.value || !geojsonData) return
  
  try {
    loading.value = true
    error.value = ''
    
    // 清空现有数据
    vectorLayer.value.clear()
    
    // 解析GeoJSON
    const features = geojsonData.features || []
    if (features.length === 0) {
      error.value = 'GeoJSON数据为空'
      loading.value = false
      return
    }
    
    // 计算产量范围
    const yields = features
      .map(f => f.properties?.Yield || f.properties?.yield || 0)
      .filter(y => typeof y === 'number' && !isNaN(y))
    
    if (yields.length === 0) {
      error.value = '未找到有效的产量数据'
      loading.value = false
      return
    }
    
    const minYield = Math.min(...yields)
    const maxYield = Math.max(...yields)
    yieldRange.value = { min: minYield, max: maxYield }
    
    // 生成图例（根据实际地块数和产量分布自适应分级）
    if (props.showLegend) {
      generateLegend(minYield, maxYield, yields, features.length)
      legendVisible.value = true
    }
    
    // 首先从GeoJSON直接计算边界框（最可靠的方法）
    const allLons = []
    const allLats = []
    
    // 递归提取所有坐标点
    const extractCoords = (arr) => {
      if (!Array.isArray(arr)) return
      
      if (arr.length >= 2 && typeof arr[0] === 'number' && typeof arr[1] === 'number') {
        // 这是一个坐标点 [lon, lat]
        allLons.push(arr[0])
        allLats.push(arr[1])
      } else {
        // 这是嵌套数组，递归处理
        arr.forEach(item => {
          if (Array.isArray(item)) {
            extractCoords(item)
          }
        })
      }
    }
    
    // 从所有要素中提取坐标
    features.forEach(feature => {
      if (feature.geometry && feature.geometry.coordinates) {
        extractCoords(feature.geometry.coordinates)
      }
    })
    
    // 计算边界框
    let extent = null
    let center = null
    let zoom = 13
    
    if (allLons.length > 0 && allLats.length > 0) {
      const minLon = Math.min(...allLons)
      const maxLon = Math.max(...allLons)
      const minLat = Math.min(...allLats)
      const maxLat = Math.max(...allLats)
      
      // 计算中心点
      const centerLon = (minLon + maxLon) / 2
      const centerLat = (minLat + maxLat) / 2
      center = new maptalks.Coordinate(centerLon, centerLat)
      
      // 创建边界框
      extent = new maptalks.Extent(
        new maptalks.Coordinate(minLon, minLat),
        new maptalks.Coordinate(maxLon, maxLat)
      )
      
      // 根据范围大小估算合适的缩放级别
      const width = maxLon - minLon
      const height = maxLat - minLat
      const maxDim = Math.max(width, height)
      
      if (maxDim > 1) zoom = 9
      else if (maxDim > 0.1) zoom = 11
      else if (maxDim > 0.01) zoom = 13
      else if (maxDim > 0.001) zoom = 15
      else if (maxDim > 0.0001) zoom = 17
      else zoom = 18
      
      console.log('计算得到的边界:', { minLon, maxLon, minLat, maxLat, centerLon, centerLat, zoom })
    } else {
      console.warn('未能从GeoJSON中提取到有效坐标，无法计算边界（将尝试从图层获取extent）')
    }
    
    // 转换并添加GeoJSON要素
    maptalks.GeoJSON.toGeometry(geojsonData, (geometry) => {
      const properties = geometry.getProperties()
      const yieldValue = properties.Yield || properties.yield || 0
      const color = getColorByYield(yieldValue, minYield, maxYield)
      
      // 设置样式
      geometry.updateSymbol({
        polygonFill: color,
        polygonOpacity: 0.7,
        lineColor: '#ffffff',
        lineWidth: 1,
        lineOpacity: 0.8,
      })
      
      // 添加鼠标悬停效果
      geometry.on('mouseover', (e) => {
        e.target.updateSymbol({
          polygonOpacity: 0.9,
          lineWidth: 2,
        })
      })
      
      geometry.on('mouseout', (e) => {
        e.target.updateSymbol({
          polygonOpacity: 0.7,
          lineWidth: 1,
        })
      })
      
      // 添加点击信息窗口
      const infoContent = Object.keys(properties)
        .map(key => `<strong>${key}:</strong> ${properties[key]}`)
        .join('<br/>')
      
      geometry.setInfoWindow({
        title: '地块信息',
        content: infoContent,
        autoPan: true,
        autoOpenOn: 'click',
        autoCloseOn: 'click',
      })
      
      geometry.addTo(vectorLayer.value)
    })
    
    // 等待几何体添加完成，然后调整视野
    await nextTick()
    
    // 调整地图视野：优先使用图层 extent（参考 Map.vue 的做法，更稳定）
    let targetExtent = null
    try {
      const layerExtent = vectorLayer.value?.getExtent?.()
      if (layerExtent) {
        targetExtent = layerExtent
      } else if (extent) {
        targetExtent = extent
      }
    } catch (e) {
      console.warn('获取图层extent失败:', e)
    }

    if (targetExtent && map.value) {
      try {
        // 先自适应范围
        map.value.fitExtent(targetExtent, {
          padding: [50, 50, 50, 50],
          animation: true,
          duration: 1000,
        })

        // 动画结束后，微调中心并固定到一个合适的缩放级别（约 15）
        setTimeout(() => {
          if (!map.value) return
          try {
            const c = targetExtent.getCenter ? targetExtent.getCenter() : null
            if (c) {
              map.value.setCenter(c)
            }
            map.value.setZoom(15)
          } catch (e) {
            console.warn('设置中心或缩放失败:', e)
          }
        }, 1100)
      } catch (e) {
        console.warn('fitExtent 失败，尝试直接设置中心和缩放:', e)
        try {
          const c = targetExtent.getCenter ? targetExtent.getCenter() : null
          if (c && map.value) {
            map.value.setCenter(c)
            map.value.setZoom(15)
          }
        } catch (err) {
          console.error('直接设置地图视野失败:', err)
        }
      }
    } else {
      console.warn('无法计算/获取边界框，使用默认中心点')
    }
    
    loading.value = false
  } catch (e) {
    console.error('加载GeoJSON失败:', e)
    error.value = '加载GeoJSON失败: ' + e.message
    loading.value = false
  }
}

// 生成图例：根据实际地块数量和产量分布自适应分级（使用分位数分级）
const generateLegend = (minYield, maxYield, yieldsArray, featureCount) => {
  const totalParcels = featureCount || (yieldsArray?.length ?? 0) || 1
  const uniqueYields = Array.isArray(yieldsArray)
    ? Array.from(new Set(yieldsArray)).sort((a, b) => a - b)
    : []
  const uniqueCount = uniqueYields.length || 1

  // 颜色档位数量：不超过 8 档，且不超过地块数和不同产量数
  let classCount = Math.min(8, totalParcels, uniqueCount)
  if (classCount < 1) classCount = 1

  legendColors.value = []
  legendLabels.value = []
  
  // 特殊情况：只有一档
  if (classCount === 1) {
    const color = getColorByYield(minYield, minYield, maxYield)
    legendColors.value.push(color)
    legendLabels.value.push(minYield.toFixed(0))
    return
  }

  // 分位数分级：根据实际数据分布划分 classCount 档
  // 获取所有产量值并排序（用于计算分位数）
  const allYields = Array.isArray(yieldsArray) && yieldsArray.length > 0
    ? yieldsArray.filter(y => typeof y === 'number' && !isNaN(y)).sort((a, b) => a - b)
    : []
  
  if (allYields.length === 0) {
    // 如果没有有效数据，回退到等距分级
    for (let i = 0; i < classCount; i++) {
      const ratio = i / (classCount - 1)
      const yieldValue = minYield + (maxYield - minYield) * ratio
      const color = getColorByYield(yieldValue, minYield, maxYield)
      legendColors.value.push(color)
      legendLabels.value.push(yieldValue.toFixed(0))
    }
    return
  }

  // 计算分位数点：将数据分成 classCount 个区间，每个区间包含大致相等的数据量
  const quantileValues = []
  for (let i = 0; i < classCount; i++) {
    // 计算分位点位置（0, 1/classCount, 2/classCount, ..., (classCount-1)/classCount）
    const quantile = i / classCount
    // 计算对应的索引位置
    const index = quantile * (allYields.length - 1)
    const lowerIndex = Math.floor(index)
    const upperIndex = Math.ceil(index)
    const fraction = index - lowerIndex
    
    // 线性插值计算分位数值
    let quantileValue
    if (lowerIndex === upperIndex || fraction === 0) {
      quantileValue = allYields[lowerIndex]
    } else {
      quantileValue = allYields[lowerIndex] * (1 - fraction) + allYields[upperIndex] * fraction
    }
    
    quantileValues.push(quantileValue)
  }
  
  // 确保最后一个分位数是最大值（避免浮点误差）
  quantileValues[classCount - 1] = maxYield

  // 生成图例颜色和标签
  for (let i = 0; i < classCount; i++) {
    const yieldValue = quantileValues[i]
    const color = getColorByYield(yieldValue, minYield, maxYield)
    legendColors.value.push(color)
    legendLabels.value.push(yieldValue.toFixed(0))
  }
}

// 从URL加载GeoJSON
const loadGeoJSONFromUrl = async (url) => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const geojsonData = await response.json()
    await loadGeoJSON(geojsonData)
  } catch (e) {
    console.error('从URL加载GeoJSON失败:', e)
    error.value = '加载GeoJSON失败: ' + e.message
    loading.value = false
    hasData.value = false
  }
}

// 监听props变化
watch(() => props.geojson, (newVal) => {
  if (newVal) {
    loadGeoJSON(newVal)
  }
}, { deep: true })

watch(() => props.geojsonUrl, (newVal) => {
  if (newVal) {
    loadGeoJSONFromUrl(newVal)
  }
})

onMounted(async () => {
  await initMap()
  
  // 如果已有数据，立即加载
  if (props.geojson) {
    await loadGeoJSON(props.geojson)
  } else if (props.geojsonUrl) {
    await loadGeoJSONFromUrl(props.geojsonUrl)
  }
})

// 注意：不主动销毁 maptalks 实例，避免内部全局事件（如 _onDocVisibilitychange）在销毁后访问空对象导致 _getLayers 报错
// 参考项目原始 Map.vue 的实现，仅在页面生命周期内创建一次地图，让 maptalks 自己管理内部事件
onUnmounted(() => {
  // 保留为空，避免干预 maptalks 内部全局事件
})
</script>

<style scoped>
.geojson-map-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.map-loading,
.map-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.9);
  padding: 20px 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.map-error {
  color: #f56c6c;
}

.map-legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 10px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 120px;
  max-width: 140px;
}

.legend-title {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #303133;
  text-align: center;
}

.legend-gradient {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.legend-item {
  height: 16px;
  width: 100%;
  position: relative;
  border: 1px solid #ddd;
  border-radius: 2px;
}

.legend-label {
  position: absolute;
  left: 4px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  color: #333;
  font-weight: 500;
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
}
</style>
