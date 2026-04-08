<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <div class="header-bar">
          <div class="title">玉米产量预测区域版（API1）</div>
          <div class="actions">
            <el-button type="primary" @click="viewTaskHistory">📋 任务历史</el-button>
            <el-button @click="goBack">返回</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <div class="maize-estimate-main">
          <el-container>
            <el-main>
              <div class="content-grid">
                <!-- 第一行：模型配置和数据输入 -->
                <div class="top-row">
                  <!-- 左侧：模型配置 -->
                  <div class="left-column">
                  <div class="param-card">
                    <div class="card-title">模型文件选择</div>
                    <div class="param-description">
                      选择要使用的预训练模型文件
                    </div>
                     <el-form :model="config" label-width="100px">
                       <el-form-item label="模型文件">
                         <el-select v-model="config.current_model" style="width: 100%;" placeholder="请选择模型文件">
                           <el-option 
                             v-for="model in availableModels" 
                             :key="model" 
                             :label="model" 
                             :value="model" 
                           />
                         </el-select>
                       </el-form-item>
                     </el-form>
                    <div class="config-actions">
                      <el-button @click="scanModelFiles" size="small">刷新模型列表</el-button>
                      <el-button @click="getCurrentConfig" size="small">获取当前配置</el-button>
                      <el-button type="primary" @click="saveConfig" size="small">保存配置</el-button>
                    </div>
                  </div>
                </div>

                <!-- 右侧：数据输入 -->
                <div class="right-column">
                  <div class="param-card">
                    <div class="card-title">数据输入</div>
                    <div class="upload-description">
                      上传数据文件夹和Shapefile文件夹，这些文件包含用于玉米产量预测区域版（API1）预测的所有输入数据
                    </div>
                    <div class="upload-button-wrapper">
                      <el-button type="primary" @click="showDataUpload = true" size="large">
                        开始上传数据文件并预测
                      </el-button>
                    </div>
                  </div>
                </div>
                </div>

                <!-- 第二行：参数配置（横跨两列） -->
              <div class="bottom-row">
                <div class="param-card full-width">
                  <div class="card-title">算法参数配置</div>
                  <div class="param-description">
                    调整优化算法参数以优化预测性能。
                    <span class="param-tip">
                      （当前实现：修改参数后需重启 Maize_Yield_API1 服务后，新的参数才会在后续预测中生效）
                    </span>
                  </div>
                  
                  <div class="parameters-section">
                    <div class="parameters-grid">
                      <div class="parameter-item">
                        <label>种群大小 (POPULATION_SIZE):</label>
                        <el-input-number v-model.number="maizeEstimateParams.POPULATION_SIZE" :min="1" :max="1000" size="small" style="width:150px" />
                      </div>
                      <div class="parameter-item">
                        <label>最大迭代次数 (MAX_GENERATIONS):</label>
                        <el-input-number v-model.number="maizeEstimateParams.MAX_GENERATIONS" :min="1" :max="10000" size="small" style="width:150px" />
                      </div>
                      <div class="parameter-item">
                        <label>超时时间 (TIMEOUT):</label>
                        <div style="display: flex; align-items: center; gap: 5px;">
                          <el-input-number v-model.number="maizeEstimateParams.TIMEOUT" :min="1" :max="86400" size="small" style="width:150px" />
                          <span style="color: #666;">秒</span>
                        </div>
                      </div>
                      <div class="parameter-item">
                        <label>API超时时间 (API_TIMEOUT):</label>
                        <div style="display: flex; align-items: center; gap: 5px;">
                          <el-input-number v-model.number="maizeEstimateParams.API_TIMEOUT" :min="1" :max="86400" size="small" style="width:150px" />
                          <span style="color: #666;">秒</span>
                        </div>
                      </div>
                      <div class="parameter-item">
                        <label>最大工作线程数 (MAX_WORKERS):</label>
                        <el-input-number v-model.number="maizeEstimateParams.MAX_WORKERS" :min="1" :max="32" size="small" style="width:150px" />
                      </div>
                    </div>
                    <div class="parameters-actions">
                      <el-button type="primary" @click="saveParameters" size="small">保存参数</el-button>
                      <el-button @click="getCurrentParameters" size="small">获取当前参数</el-button>
                      <el-button @click="resetParametersDefaults" size="small">重置为默认值</el-button>
                    </div>
                  </div>
                </div>
              </div>
              </div>
            </el-main>
          </el-container>
        </div>
      </el-main>
    </el-container>

    <!-- 预测结果展示区域 -->
    <div class="outputData" v-if="output">
      <el-container>
        <el-header class="result-header">
          <div class="result-header-content">
            <i class="el-icon-success"></i>
            <span>玉米产量预测区域版（API1）预测结果</span>
          </div>
        </el-header>
        <el-main>
          <el-alert 
            type="success" 
            :closable="false" 
            v-if="output.task_id" 
            :title="`预测完成！输出文件已生成`"
            description="文件已保存到指定路径，可下载查看详细结果"
            show-icon
            class="result-alert"
          />
          
          <div class="result-stats" v-if="output.static_info">
            <h4>📊 预测统计信息</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">📈</div>
                <div class="stat-content">
                  <span class="stat-label">平均产量</span>
                  <span class="stat-value">{{ output.static_info.mean?.toFixed(2) }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🏆</div>
                <div class="stat-content">
                  <span class="stat-label">最高产量</span>
                  <span class="stat-value">{{ output.static_info.max?.toFixed(2) }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📉</div>
                <div class="stat-content">
                  <span class="stat-label">最低产量</span>
                  <span class="stat-value">{{ output.static_info.min?.toFixed(2) }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🔢</div>
                <div class="stat-content">
                  <span class="stat-label">样本数量</span>
                  <span class="stat-value">{{ output.static_info.count }} 个</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- GeoJSON地图预览 -->
          <div class="result-map" v-if="output.task_id && geojsonData" style="margin-top: 20px;">
            <h4>🗺️ 地理信息预览</h4>
            <div class="map-wrapper">
              <GeoJSONMap 
                :geojson="geojsonData" 
                :height="'500px'"
                :show-legend="true"
              />
            </div>
          </div>
          
          <div class="result-actions" style="margin-top: 20px; text-align: center;">
            <el-button type="success" @click="downloadResult('geojson')" size="large">
              <i class="el-icon-download"></i> 下载GeoJSON
            </el-button>
            <el-button type="success" @click="downloadResult('csv')" size="large" style="margin-left: 10px;">
              <i class="el-icon-download"></i> 下载CSV
            </el-button>
          </div>
        </el-main>
      </el-container>
    </div>

    <!-- 数据文件上传对话框 -->
    <el-dialog v-model="showDataUpload" title="玉米产量预测区域版（API1） - 数据文件上传" width="90%" :close-on-click-modal="false">
      <div class="maize-estimate-upload">
        <div class="upload-header">
          <el-alert
            title="文件上传说明"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              请上传数据文件夹（包含所有.npy文件）和Shapefile文件夹（包含.shp, .shx, .dbf, .prj, .CPG, .sbn, .sbx, .shp.xml文件）。
              支持点击选择文件夹、拖拽文件到对应区域两种方式。所有文件上传完成后，点击"开始预测"按钮进行分析。
            </template>
          </el-alert>
        </div>
        
        <!-- 左右两块数据输入区域 -->
        <div class="upload-data-grid">
          <!-- 左侧：数据文件夹路径 -->
          <div class="upload-data-item">
            <div class="data-input-header">
              <div class="data-input-title">数据文件夹路径</div>
              <div class="data-input-desc">包含所有.npy文件</div>
            </div>
            
            <!-- 一次性拖拽多个文件区域 -->
            <div 
              class="multiple-upload-zone"
              :class="{ 'drag-over': dataFolderDragOver }"
              @dragover.prevent="handleDataFolderDragOver"
              @dragleave.prevent="handleDataFolderDragLeave"
              @drop.prevent="handleDataFolderDrop"
            >
              <div class="upload-zone-content">
                <i class="el-icon-upload"></i>
                <p>拖拽多个.npy文件到此处</p>
                <p class="upload-hint">或</p>
                <el-button @click="selectDataFolder" type="primary" size="default">
                  选择文件夹
                </el-button>
                <input
                  ref="dataFolderInput"
                  type="file"
                  webkitdirectory
                  directory
                  multiple
                  @change="handleDataFolderSelect"
                  style="display: none"
                  accept=".npy"
                />
              </div>
            </div>
            
            <!-- 已选择路径显示 -->
            <div v-if="folderPaths.dataFolder" class="selected-path">
              <i class="el-icon-folder"></i>
              <span>{{ folderPaths.dataFolder }}</span>
            </div>
            
            <!-- 文件列表 -->
            <div v-if="dataFolderFiles.length > 0" class="file-list">
              <div v-for="(file, index) in dataFolderFiles" :key="index" class="file-item">
                <i class="el-icon-document"></i>
                <span>{{ file.name }}</span>
              </div>
            </div>
          </div>

          <!-- 右侧：Shapefile文件夹路径 -->
          <div class="upload-data-item">
            <div class="data-input-header">
              <div class="data-input-title">Shapefile文件夹路径</div>
              <div class="data-input-desc">包含.shp, .shx, .dbf, .prj, .CPG, .sbn, .sbx, .shp.xml文件</div>
            </div>
            
            <!-- 一次性拖拽多个文件区域 -->
            <div 
              class="multiple-upload-zone"
              :class="{ 'drag-over': shpFolderDragOver }"
              @dragover.prevent="handleShpFolderDragOver"
              @dragleave.prevent="handleShpFolderDragLeave"
              @drop.prevent="handleShpFolderDrop"
            >
              <div class="upload-zone-content">
                <i class="el-icon-upload"></i>
                <p>拖拽Shapefile文件到此处</p>
                <p class="upload-hint">或</p>
                <el-button @click="selectShpFolder" type="primary" size="default">
                  选择文件夹
                </el-button>
                <input
                  ref="shpFolderInput"
                  type="file"
                  webkitdirectory
                  directory
                  multiple
                  @change="handleShpFolderSelect"
                  style="display: none"
                  accept=".shp,.shx,.dbf,.prj,.CPG,.cpg,.sbn,.sbx,.xml"
                />
              </div>
            </div>
            
            <!-- 已选择路径显示 -->
            <div v-if="folderPaths.shpFolder" class="selected-path">
              <i class="el-icon-folder"></i>
              <span>{{ folderPaths.shpFolder }}</span>
            </div>
            
            <!-- 文件列表 -->
            <div v-if="shpFolderFiles.length > 0" class="file-list">
              <div v-for="(file, index) in shpFolderFiles" :key="index" class="file-item">
                <i class="el-icon-document"></i>
                <span>{{ file.name }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="upload-actions">
          <el-button type="primary" @click="handleUploadConfirm" :loading="predicting" size="large">
            开始预测
          </el-button>
          <el-button @click="showDataUpload = false" size="large">关闭</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 任务历史对话框 -->
    <el-dialog v-model="showTaskHistory" title="玉米产量预测区域版（API1）任务历史" width="80%" :close-on-click-modal="false">
      <div class="task-history">
        <div class="task-history-header">
          <el-button @click="loadTaskHistory" :loading="taskHistoryLoading" size="small">
            <i class="el-icon-refresh"></i> 刷新
          </el-button>
          <span class="task-count">共 {{ taskHistory.length }} 个任务</span>
        </div>
        
        <el-table :data="taskHistory" v-loading="taskHistoryLoading" stripe>
          <el-table-column prop="task_id" label="任务ID" width="250">
            <template #default="{ row }">
              <span class="task-id">{{ row.task_id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="算法" width="200">
            <template #default="{ row }">
              <span class="algorithm-name">玉米产量预测区域版（API1）</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatTaskTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'danger'">
                {{ row.status === 'completed' ? '完成' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="在地图中显示" width="120" align="center">
            <template #default="{ row }">
              <el-button 
                v-if="row.status === 'completed'" 
                type="primary" 
                @click="showMapPreview(row)"
                size="small"
                title="在地图中显示"
                circle
                style="padding: 6px; min-width: 32px;"
              >
                <span style="font-size: 18px; line-height: 1;">🗺️</span>
              </el-button>
              <span v-else class="no-map">-</span>
            </template>
          </el-table-column>
          <el-table-column label="统计信息" width="300">
            <template #default="{ row }">
              <div v-if="row.static_info" class="stats-info">
                <span>平均: {{ parseStaticInfo(row.static_info).mean?.toFixed(2) }}</span>
                <span>最大: {{ parseStaticInfo(row.static_info).max?.toFixed(2) }}</span>
                <span>最小: {{ parseStaticInfo(row.static_info).min?.toFixed(2) }}</span>
                <span>数量: {{ parseStaticInfo(row.static_info).count }}</span>
              </div>
              <span v-else class="no-stats">无统计信息</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="viewTaskDetail(row)">查看结果</el-button>
              <el-button size="small" type="success" @click="downloadTaskResult(row)">下载</el-button>
              <el-button size="small" type="danger" @click="deleteTask(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showTaskHistory = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 地图预览对话框 -->
    <el-dialog 
      v-model="showMapPreviewDialog" 
      title="地理信息预览" 
      width="90%" 
      :close-on-click-modal="false"
      @close="closeMapPreview"
    >
      <div class="map-preview-container" v-loading="mapPreviewLoading">
        <div v-if="mapPreviewGeoJSON" class="map-wrapper">
          <GeoJSONMap 
            :geojson="mapPreviewGeoJSON" 
            :height="'600px'"
            :show-legend="true"
          />
        </div>
        <div v-else-if="!mapPreviewLoading" class="no-map-data">
          <el-alert
            title="无法加载地图数据"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              该任务可能没有生成GeoJSON文件，或文件已丢失。
            </template>
          </el-alert>
        </div>
      </div>
      <template #footer>
        <el-button @click="closeMapPreview">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog v-model="showTaskDetail" title="任务详情" width="70%" :close-on-click-modal="false">
      <div class="task-detail" v-loading="taskDetailLoading">
        <!-- 成功提示 -->
        <el-alert
          v-if="taskDetailData && taskDetailData.status === 'completed'"
          title="预测完成！"
          type="success"
          :closable="true"
          show-icon
          class="result-alert"
        >
          <template #default>
            <div v-if="taskDetailData.data_summary || taskDetailData.static_info" class="alert-stats">
              <span>平均产量: {{ getStatValue(taskDetailData, 'mean') }} kg/ha</span>
              <span>最高产量: {{ getStatValue(taskDetailData, 'max') }} kg/ha</span>
              <span>最低产量: {{ getStatValue(taskDetailData, 'min') }} kg/ha</span>
              <span>样本数: {{ getStatValue(taskDetailData, 'count') }} 条</span>
            </div>
          </template>
        </el-alert>
        
        <div v-if="taskDetailData" class="task-detail-content">
          <!-- 任务基本信息 -->
          <div class="task-info-section">
            <h4>📋 任务信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">任务ID:</span>
                <span class="info-value">{{ taskDetailData.task_id }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">创建时间:</span>
                <span class="info-value">{{ formatTaskTime(taskDetailData.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">状态:</span>
                <el-tag :type="taskDetailData.status === 'completed' ? 'success' : 'danger'">
                  {{ taskDetailData.status === 'completed' ? '完成' : '失败' }}
                </el-tag>
              </div>
              <div class="info-item" v-if="taskDetailData.model_name">
                <span class="info-label">使用模型:</span>
                <span class="info-value">{{ getModelName(taskDetailData.model_name) }}</span>
              </div>
              <div class="info-item" v-if="taskDetailData.output_path">
                <span class="info-label">输出路径:</span>
                <span class="info-value">{{ simplifyOutputPath(taskDetailData.output_path) }}</span>
              </div>
            </div>
          </div>

          <!-- 本次任务使用的算法参数快照 -->
          <div
            class="task-info-section"
            v-if="taskDetailData.algorithm_params_used && Object.keys(taskDetailData.algorithm_params_used).length"
          >
            <h4>⚙️ 算法参数（本次任务使用）</h4>
            <div class="info-grid">
              <div class="info-item" v-for="(v, k) in taskDetailData.algorithm_params_used" :key="k">
                <span class="info-label">{{ k }}:</span>
                <span class="info-value">{{ v }}</span>
              </div>
            </div>
          </div>

          <!-- 预测结果统计 -->
          <div class="result-summary-section" v-if="taskDetailData.data_summary || taskDetailData.static_info">
            <h4>📊 预测结果统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">📈</div>
                <div class="stat-content">
                  <span class="stat-label">平均产量</span>
                  <span class="stat-value">{{ getStatValue(taskDetailData, 'mean') }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🏆</div>
                <div class="stat-content">
                  <span class="stat-label">最高产量</span>
                  <span class="stat-value">{{ getStatValue(taskDetailData, 'max') }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📉</div>
                <div class="stat-content">
                  <span class="stat-label">最低产量</span>
                  <span class="stat-value">{{ getStatValue(taskDetailData, 'min') }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🔢</div>
                <div class="stat-content">
                  <span class="stat-label">记录数量</span>
                  <span class="stat-value">{{ getStatValue(taskDetailData, 'count') }} 条</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 错误信息 -->
          <div class="error-section" v-if="taskDetailData.error">
            <h4>❌ 错误信息</h4>
            <el-alert :title="taskDetailData.error" type="error" :closable="false" />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTaskDetail = false">关闭</el-button>
        <el-button type="success" @click="downloadTaskResult(selectedTask)" v-if="selectedTask">
          下载结果文件
        </el-button>
      </template>
    </el-dialog>

    <!-- 预测进度对话框 -->
    <el-dialog 
      v-model="predicting" 
      title="正在运行预测" 
      width="500px" 
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="prediction-progress">
        <el-progress 
          :percentage="100" 
          :indeterminate="true"
          :duration="3"
          status="success"
        />
        <div class="progress-text">{{ progressText }}</div>
        <div class="progress-hint">预测可能需要几分钟时间，请耐心等待...</div>
      </div>
      <template #footer>
        <el-button type="danger" @click="cancelPrediction" :disabled="!abortController">
          取消任务
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { useRouter } from 'vue-router'
import GeoJSONMap from '@/components/GeoJSONMap.vue'
import {
  runMaizeEstimate,
  getMaizeEstimateParams,
  updateMaizeEstimateParams,
  getMaizeEstimateDefaults,
  getMaizeEstimateTasks,
  getMaizeEstimateTask,
  deleteMaizeEstimateTask,
  downloadMaizeEstimateResult,
  cancelMaizeEstimateTask
} from '@/api/maizeEstimate.js'

const router = useRouter()

// 页面状态
const predicting = ref(false)
const output = ref(null)
const showDataUpload = ref(false)
const geojsonData = ref(null)
const showTaskHistory = ref(false)
const showTaskDetail = ref(false)
const taskHistory = ref([])
const taskHistoryLoading = ref(false)
const taskDetailData = ref(null)
const abortController = ref(null) // 用于取消请求的控制器
const progressText = ref('正在上传文件并运行预测，请稍候...') // 进度提示文本
const taskDetailLoading = ref(false)
const selectedTask = ref(null)
const currentTaskId = ref(null) // 当前运行的任务ID

// 地图预览相关
const showMapPreviewDialog = ref(false)
const mapPreviewGeoJSON = ref(null)
const mapPreviewLoading = ref(false)
const currentPreviewTaskId = ref(null)

// 文件夹路径
const folderPaths = ref({
  dataFolder: '',
  shpFolder: ''
})

// 拖拽状态
const dataFolderDragOver = ref(false)
const shpFolderDragOver = ref(false)

// 文件列表
const dataFolderFiles = ref([])
const shpFolderFiles = ref([])

// 模型配置
const config = ref({
  model_path: 'TL-ONEYEAR425_MUS_SLB_Time_1031.sav',
  current_model: 'TL-ONEYEAR425_MUS_SLB_Time_1031.sav'
})

const availableModels = ref([])

// 参数配置
const maizeEstimateParams = ref({
  POPULATION_SIZE: 50,
  MAX_GENERATIONS: 100,
  TIMEOUT: 3600,
  API_TIMEOUT: 3600,
  MAX_WORKERS: 4
})

// 文件输入框引用
const dataFolderInput = ref(null)
const shpFolderInput = ref(null)

// 选择数据文件夹（使用文件选择器）
const selectDataFolder = () => {
  if (dataFolderInput.value) {
    dataFolderInput.value.click()
  }
}

// 处理数据文件夹选择
const handleDataFolderSelect = (event) => {
  const files = Array.from(event.target.files || [])
  
  if (files.length === 0) return
  
  // 过滤出.npy文件
  const npyFiles = files.filter(file => file.name.endsWith('.npy'))
  
  if (npyFiles.length === 0) {
    ElMessage.warning('所选文件夹中没有找到.npy文件')
    return
  }
  
  // 存储文件列表
  dataFolderFiles.value = npyFiles
  folderPaths.value.dataFolder = '' // 清空路径，使用文件模式
  
  // 从文件路径推断文件夹路径（如果可能）
  if (npyFiles.length > 0) {
    const firstFile = npyFiles[0]
    // 获取文件的 webkitRelativePath，提取文件夹路径
    if (firstFile.webkitRelativePath) {
      const folderPath = firstFile.webkitRelativePath.split('/')[0]
      folderPaths.value.dataFolder = folderPath
    }
  }
  
  ElMessage.success(`已选择 ${npyFiles.length} 个.npy文件`)
  
  // 重置input，以便可以再次选择
  if (dataFolderInput.value) {
    dataFolderInput.value.value = ''
  }
}

// 选择Shapefile文件夹（使用文件选择器）
const selectShpFolder = () => {
  if (shpFolderInput.value) {
    shpFolderInput.value.click()
  }
}

// 处理Shapefile文件夹选择
const handleShpFolderSelect = (event) => {
  const files = Array.from(event.target.files || [])
  
  if (files.length === 0) return
  
  // 过滤出Shapefile相关文件（包括.CPG, .sbn, .sbx, .shp.xml文件）
  const shpFiles = files.filter(file => {
    const name = file.name.toLowerCase()
    return name.endsWith('.shp') || name.endsWith('.shx') || 
           name.endsWith('.dbf') || name.endsWith('.prj') ||
           name.endsWith('.cpg') || name.endsWith('.sbn') || 
           name.endsWith('.sbx') || name.endsWith('.shp.xml') || 
           (name.endsWith('.xml') && name.includes('.shp'))
  })
  
  if (shpFiles.length === 0) {
    ElMessage.warning('所选文件夹中没有找到Shapefile文件（.shp, .shx, .dbf, .prj, .CPG, .sbn, .sbx, .shp.xml）')
    return
  }
  
  // 检查是否包含.shp文件
  const hasShp = shpFiles.some(file => file.name.toLowerCase().endsWith('.shp'))
  if (!hasShp) {
    ElMessage.warning('Shapefile必须包含.shp文件')
    return
  }
  
  // 存储文件列表
  shpFolderFiles.value = shpFiles
  folderPaths.value.shpFolder = '' // 清空路径，使用文件模式
  
  // 从文件路径推断文件夹路径（如果可能）
  if (shpFiles.length > 0) {
    const firstFile = shpFiles[0]
    // 获取文件的 webkitRelativePath，提取文件夹路径
    if (firstFile.webkitRelativePath) {
      const folderPath = firstFile.webkitRelativePath.split('/')[0]
      folderPaths.value.shpFolder = folderPath
    }
  }
  
  ElMessage.success(`已选择 ${shpFiles.length} 个Shapefile文件`)
  
  // 重置input，以便可以再次选择
  if (shpFolderInput.value) {
    shpFolderInput.value.value = ''
  }
}

// 数据文件夹拖拽处理
const handleDataFolderDragOver = () => {
  dataFolderDragOver.value = true
}

const handleDataFolderDragLeave = () => {
  dataFolderDragOver.value = false
}

const handleDataFolderDrop = (event) => {
  dataFolderDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  
  if (files.length === 0) return
  
  // 过滤出.npy文件
  const npyFiles = files.filter(file => file.name.endsWith('.npy'))
  
  if (npyFiles.length === 0) {
    ElMessage.warning('请拖拽.npy格式的文件')
    return
  }
  
  // 如果只有一个文件，尝试从路径推断文件夹
  if (npyFiles.length === 1) {
    ElMessage.info('检测到单个文件，请提供文件夹路径或拖拽多个文件')
    dataFolderFiles.value = npyFiles
    return
  }
  
  // 多个文件，存储文件列表
  dataFolderFiles.value = npyFiles
  folderPaths.value.dataFolder = '' // 清空路径，使用文件模式
  ElMessage.success(`已选择 ${npyFiles.length} 个.npy文件`)
}

// Shapefile文件夹拖拽处理
const handleShpFolderDragOver = () => {
  shpFolderDragOver.value = true
}

const handleShpFolderDragLeave = () => {
  shpFolderDragOver.value = false
}

const handleShpFolderDrop = (event) => {
  shpFolderDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  
  if (files.length === 0) return
  
  // 过滤出Shapefile相关文件（包括.CPG, .sbn, .sbx, .shp.xml文件）
  const shpFiles = files.filter(file => {
    const name = file.name.toLowerCase()
    return name.endsWith('.shp') || name.endsWith('.shx') || 
           name.endsWith('.dbf') || name.endsWith('.prj') ||
           name.endsWith('.cpg') || name.endsWith('.sbn') || 
           name.endsWith('.sbx') || name.endsWith('.shp.xml') || 
           (name.endsWith('.xml') && name.includes('.shp'))
  })
  
  if (shpFiles.length === 0) {
    ElMessage.warning('请拖拽Shapefile相关文件（.shp, .shx, .dbf, .prj, .CPG, .sbn, .sbx, .shp.xml）')
    return
  }
  
  // 检查是否包含.shp文件
  const hasShp = shpFiles.some(file => file.name.toLowerCase().endsWith('.shp'))
  if (!hasShp) {
    ElMessage.warning('Shapefile必须包含.shp文件')
    return
  }
  
  // 存储文件列表
  shpFolderFiles.value = shpFiles
  folderPaths.value.shpFolder = '' // 清空路径，使用文件模式
  ElMessage.success(`已选择 ${shpFiles.length} 个Shapefile文件`)
}

// 保存配置
const saveConfig = async () => {
  try {
    await updateMaizeEstimateParams(config.value)
    ElMessage.success('配置保存成功')
  } catch (e) {
    ElMessage.error('配置保存失败')
  }
}

// 扫描模型文件
const scanModelFiles = async () => {
  try {
    const res = await getMaizeEstimateDefaults()
    if (res && res.data && res.data.available_models) {
      availableModels.value = res.data.available_models
      ElMessage.success('模型列表已更新')
    }
  } catch (e) {
    ElMessage.error('获取模型列表失败')
  }
}

// 获取当前配置
const getCurrentConfig = async () => {
  try {
    const res = await getMaizeEstimateParams()
    if (res && res.data && res.data.config) {
      config.value = { ...config.value, ...res.data.config }
      ElMessage.success('配置已加载')
    }
  } catch (e) {
    ElMessage.error('获取配置失败')
  }
}

// 返回
const goBack = () => router.push('/home/algor')

// 确认上传并开始预测
const handleUploadConfirm = async () => {
  // 检查是否选择了文件（必须通过文件夹选择器或拖拽）
  if (dataFolderFiles.value.length === 0) {
    ElMessage.error('请选择文件夹或拖拽.npy文件')
    return
  }
  
  if (shpFolderFiles.value.length === 0) {
    ElMessage.error('请选择文件夹或拖拽Shapefile文件')
    return
  }
  
  // 关闭对话框
  showDataUpload.value = false
  
  // 开始预测（文件会上传 to 服务器）
  await runPrediction()
}

// 运行预测
const runPrediction = async () => {
  try {
    predicting.value = true
    progressText.value = '正在准备上传文件...'
    
    // 创建 AbortController 用于取消请求
    abortController.value = new AbortController()
    
    const formData = new FormData()
    
    // 必须通过文件上传方式（选择文件夹或拖拽文件）
    // 因为浏览器安全限制，无法直接访问用户本地路径
    if (dataFolderFiles.value.length > 0) {
      // 文件上传方式：上传所有.npy文件
      console.log('使用文件上传方式上传数据文件')
      progressText.value = `正在上传 ${dataFolderFiles.value.length} 个数据文件...`
      dataFolderFiles.value.forEach(file => {
        formData.append('data_files', file)
      })
    } else {
      ElMessage.error('请选择文件夹或拖拽.npy文件')
      predicting.value = false
      abortController.value = null
      return
    }
    
    if (shpFolderFiles.value.length > 0) {
      // 文件上传方式：上传所有Shapefile文件
      console.log('使用文件上传方式上传Shapefile')
      progressText.value = `正在上传 ${shpFolderFiles.value.length} 个Shapefile文件...`
      shpFolderFiles.value.forEach(file => {
        formData.append('shp_files', file)
      })
    } else {
      ElMessage.error('请选择文件夹或拖拽Shapefile文件')
      predicting.value = false
      abortController.value = null
      return
    }
    
    // 更新进度提示
    progressText.value = '文件上传完成，正在运行预测算法，请稍候...（预计需要几分钟）'
    
    // 开始预测请求
    const res = await runMaizeEstimate(formData, abortController.value)
    
    // 如果请求成功，获取任务ID
    if (res && res.data && res.data.code === 200 && res.data.result?.task_id) {
      currentTaskId.value = res.data.result.task_id
    }
    
    if (res && res.data && res.data.code === 200) {
      output.value = res.data.result
      
      // 解析统计信息
      const staticInfo = res.data.result.static_info
      let stats = {}
      if (typeof staticInfo === 'string') {
        try {
          stats = JSON.parse(staticInfo)
        } catch (e) {
          console.error('解析统计信息失败:', e)
        }
      } else {
        stats = staticInfo || {}
      }
      
      // 显示成功消息，包含统计信息
      const meanYield = stats.mean ? stats.mean.toFixed(2) : 'N/A'
      const maxYield = stats.max ? stats.max.toFixed(2) : 'N/A'
      const minYield = stats.min ? stats.min.toFixed(2) : 'N/A'
      const count = stats.count || 0
      
      ElMessage.success({
        message: `预测完成！平均产量: ${meanYield} kg/ha，最高: ${maxYield} kg/ha，最低: ${minYield} kg/ha，样本数: ${count}`,
        duration: 5000,
        showClose: true
      })
      
      // 自动加载任务详情并显示
      if (res.data.result.task_id) {
        await loadTaskDetail(res.data.result.task_id)
        showTaskDetail.value = true
        // 加载GeoJSON数据用于地图预览
        await loadGeoJSONForPreview(res.data.result.task_id)
      }
      
      // 关闭上传对话框
      showDataUpload.value = false
      
      // 刷新任务历史
      await loadTaskHistory()
    } else {
      ElMessage.error(res.data?.msg || '预测失败')
    }
  } catch (e) {
    console.error('预测错误:', e)
    
    // 检查是否是用户取消
    if (e.name === 'CanceledError' || e.message === 'canceled' || e.code === 'ERR_CANCELED') {
      ElMessage.info('预测任务已取消')
    } else if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
      ElMessage.warning({
        message: '请求超时，但后端可能仍在处理。请稍后在任务历史中查看结果。',
        duration: 8000,
        showClose: true
      })
      // 超时后刷新任务历史，可能任务已经完成
      setTimeout(() => {
        loadTaskHistory()
      }, 2000)
    } else {
      ElMessage.error('预测失败: ' + (e.response?.data?.error || e.message))
    }
  } finally {
    predicting.value = false
    abortController.value = null
    progressText.value = '正在上传文件并运行预测，请稍候...'
    // 注意：不清空 currentTaskId，因为可能在 finally 之前就被设置了
    // 如果任务完成或失败，currentTaskId 会在成功/失败处理中保留，用于查询任务状态
  }
}

// 取消预测任务
const cancelPrediction = async () => {
  if (!abortController.value && !currentTaskId.value) {
    ElMessage.warning('没有正在运行的任务')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要取消当前预测任务吗？',
      '取消任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 1. 取消前端HTTP请求
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
    
    // 2. 调用后端API取消任务（如果任务ID存在）
    if (currentTaskId.value) {
      try {
        await cancelMaizeEstimateTask(currentTaskId.value)
        ElMessage.success('任务取消请求已发送到服务器')
      } catch (e) {
        console.error('调用取消API失败:', e)
        // 即使后端取消失败，前端也已经取消了请求
        ElMessage.warning('前端请求已取消，但后端任务可能仍在运行')
      }
    }
    
    predicting.value = false
    progressText.value = '正在上传文件并运行预测，请稍候...'
    currentTaskId.value = null
    ElMessage.info('任务已取消')
  } catch (error) {
    // 用户点击了取消，不执行任何操作
  }
}

// 重置表单
const resetForm = () => {
  folderPaths.value = { dataFolder: '', shpFolder: '' }
  dataFolderFiles.value = []
  shpFolderFiles.value = []
  dataFolderDragOver.value = false
  shpFolderDragOver.value = false
  output.value = null
}

// 查看任务历史
const viewTaskHistory = async () => {
  showTaskHistory.value = true
  await loadTaskHistory()
}

const loadTaskHistory = async () => {
  try {
    taskHistoryLoading.value = true
    const res = await getMaizeEstimateTasks()
    if (res && res.data) {
      taskHistory.value = res.data.tasks || []
    }
  } catch (e) {
    console.error('加载任务历史失败:', e)
    ElMessage.error('加载任务历史失败')
  } finally {
    taskHistoryLoading.value = false
  }
}

// 加载任务详情（通过task_id）
const loadTaskDetail = async (taskId) => {
  try {
    taskDetailLoading.value = true
    const res = await getMaizeEstimateTask(taskId)
    if (res && res.data) {
      taskDetailData.value = res.data
      // 设置selectedTask以便显示任务ID等信息
      selectedTask.value = { task_id: taskId }
    }
  } catch (e) {
    console.error('加载任务详情失败:', e)
    ElMessage.error('加载任务详情失败')
  } finally {
    taskDetailLoading.value = false
  }
}

// 查看任务详情
const viewTaskDetail = async (task) => {
  selectedTask.value = task
  showTaskDetail.value = true
  await loadTaskDetail(task.task_id)
}

// 显示地图预览
const showMapPreview = async (task) => {
  if (!task || !task.task_id) {
    ElMessage.warning('任务信息不完整')
    return
  }
  
  currentPreviewTaskId.value = task.task_id
  showMapPreviewDialog.value = true
  mapPreviewLoading.value = true
  mapPreviewGeoJSON.value = null
  
  try {
    const res = await downloadMaizeEstimateResult(task.task_id, 'geojson')
    // 处理blob响应
    let geojson
    if (res.data instanceof Blob) {
      const text = await res.data.text()
      geojson = JSON.parse(text)
    } else if (typeof res.data === 'string') {
      geojson = JSON.parse(res.data)
    } else {
      geojson = res.data
    }
    mapPreviewGeoJSON.value = geojson
  } catch (e) {
    console.error('加载GeoJSON失败:', e)
    ElMessage.error('加载地图数据失败: ' + (e.message || '未知错误'))
    mapPreviewGeoJSON.value = null
  } finally {
    mapPreviewLoading.value = false
  }
}

// 关闭地图预览
const closeMapPreview = () => {
  showMapPreviewDialog.value = false
  // 延迟清理数据，避免关闭动画时闪烁
  setTimeout(() => {
    mapPreviewGeoJSON.value = null
    currentPreviewTaskId.value = null
  }, 300)
}

// 删除任务
const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.task_id}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deleteMaizeEstimateTask(task.task_id)
    ElMessage.success('任务删除成功')
    await loadTaskHistory() // 重新加载任务列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

// 加载GeoJSON数据用于地图预览
const loadGeoJSONForPreview = async (taskId) => {
  if (!taskId) return
  
  try {
    const res = await downloadMaizeEstimateResult(taskId, 'geojson')
    // 处理blob响应
    let geojson
    if (res.data instanceof Blob) {
      const text = await res.data.text()
      geojson = JSON.parse(text)
    } else if (typeof res.data === 'string') {
      geojson = JSON.parse(res.data)
    } else {
      geojson = res.data
    }
    geojsonData.value = geojson
  } catch (e) {
    console.error('加载GeoJSON失败:', e)
    // 不显示错误消息，因为这只是预览功能
    geojsonData.value = null
  }
}

// 下载结果
const downloadResult = async (format) => {
  if (!output.value || !output.value.task_id) {
    ElMessage.error('没有可下载的结果')
    return
  }
  
  try {
    const res = await downloadMaizeEstimateResult(output.value.task_id, format)
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `prediction_results.${format === 'geojson' ? 'geojson' : 'csv'}`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (e) {
    ElMessage.error('下载失败')
  }
}

const downloadTaskResult = async (task) => {
  try {
    // 默认下载GeoJSON格式
    const res = await downloadMaizeEstimateResult(task.task_id, 'geojson')
    
    // 创建下载链接
    const blob = new Blob([res.data], { type: 'application/geo+json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `prediction_results_${task.task_id}.geojson`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('文件下载成功')
  } catch (error) {
    console.error('下载文件失败:', error)
    ElMessage.error('下载文件失败')
  }
}

// 格式化任务时间
const formatTaskTime = (timeStr) => {
  if (!timeStr) return '未知时间'
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

// 获取模型名称显示
const getModelName = (modelName) => {
  if (!modelName) return 'TL-ONEYEAR425_MUS_SLB_Time_1031.sav'
  // 提取模型文件名，保留完整文件名（包括扩展名）
  const fileName = modelName.split('/').pop() || modelName.split('\\').pop() || modelName
  return fileName || 'TL-ONEYEAR425_MUS_SLB_Time_1031.sav'
}

// 简化输出路径显示
const simplifyOutputPath = (outputPath) => {
  if (!outputPath) return ''
  // 统一使用正斜杠
  const pathStr = outputPath.replace(/\\/g, '/')
  
  // 查找 output/ 的位置
  const outputIndex = pathStr.indexOf('output/')
  if (outputIndex !== -1) {
    // 提取 output/ 后面的部分
    const afterOutput = pathStr.substring(outputIndex + 7)
    // 如果包含文件路径（如 prediction_results.geojson），只取目录名
    const parts = afterOutput.split('/')
    const dirName = parts[0] // 获取第一个目录名（任务ID_时间戳）
    return 'output/' + dirName
  }
  
  // 如果找不到 output，尝试从路径中提取任务目录名（包含下划线的目录名）
  const parts = pathStr.split('/')
  for (let i = parts.length - 1; i >= 0; i--) {
    const part = parts[i]
    if (part && part.includes('_') && part.length > 20) {
      // 可能是任务ID_时间戳格式
      return 'output/' + part
    }
  }
  
  // 如果都找不到，返回原路径的最后一部分
  return pathStr.split('/').pop() || outputPath
}

// 解析统计信息
const parseStaticInfo = (staticInfo) => {
  if (!staticInfo) return { mean: 0, max: 0, min: 0, count: 0 }
  if (typeof staticInfo === 'string') {
    try {
      return JSON.parse(staticInfo)
    } catch {
      return { mean: 0, max: 0, min: 0, count: 0 }
    }
  }
  return staticInfo
}

// 获取统计值
const getStatValue = (taskData, key) => {
  let value = 0
  if (taskData.data_summary) {
    const map = {
      'mean': 'mean_yield',
      'max': 'max_yield',
      'min': 'min_yield',
      'count': 'total_records'
    }
    value = taskData.data_summary[map[key]] || 0
  } else if (taskData.static_info) {
    const staticInfo = parseStaticInfo(taskData.static_info)
    value = staticInfo[key] || 0
  }
  
  // 如果是 count，直接返回整数
  if (key === 'count') {
    return Math.round(value)
  }
  
  // 其他数值类型，格式化为2位小数
  if (typeof value === 'number') {
    return value.toFixed(2)
  }
  
  return value
}

// 获取当前参数
const fetchMaizeEstimateParams = async () => {
  try {
    const res = await getMaizeEstimateParams()
    if (res && res.data) {
      // 后端返回结构: { config, params, available_models }
      const p = res.data.params || {}

      if (p.POPULATION_SIZE !== undefined) maizeEstimateParams.value.POPULATION_SIZE = p.POPULATION_SIZE
      if (p.MAX_GENERATIONS !== undefined) maizeEstimateParams.value.MAX_GENERATIONS = p.MAX_GENERATIONS
      if (p.TIMEOUT !== undefined) maizeEstimateParams.value.TIMEOUT = p.TIMEOUT
      if (p.API_TIMEOUT !== undefined) maizeEstimateParams.value.API_TIMEOUT = p.API_TIMEOUT
      if (p.MAX_WORKERS !== undefined) maizeEstimateParams.value.MAX_WORKERS = p.MAX_WORKERS
    }
  } catch (e) {
    console.error('获取参数失败:', e)
  }
}

// 保存参数
const saveParameters = async () => {
  try {
    await updateMaizeEstimateParams(maizeEstimateParams.value)
    ElMessage.success('参数已保存')
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || '参数保存失败'
    ElMessage.error(typeof msg === 'string' ? msg : '参数保存失败')
  }
}

// 获取当前参数
const getCurrentParameters = async () => {
  try {
    await fetchMaizeEstimateParams()
    ElMessage.success('已获取当前参数')
  } catch (e) {
    ElMessage.error('获取参数失败')
  }
}

// 重置参数为默认值
const resetParametersDefaults = async () => {
  try {
    const res = await getMaizeEstimateDefaults()
    if (res && res.data) {
      // 后端返回结构: { config, params, available_models }
      if (res.data.params) {
        maizeEstimateParams.value = { ...maizeEstimateParams.value, ...res.data.params }
      }
      if (res.data.config) {
        config.value = { ...config.value, ...res.data.config }
      }
      if (res.data.available_models) {
        availableModels.value = res.data.available_models
      }
      ElMessage.success('已重置为默认值')
    }
  } catch (e) {
    ElMessage.error('重置失败')
  }
}

// 初始化
onMounted(async () => {
  try {
    // 加载参数
    await fetchMaizeEstimateParams()
    const res = await getMaizeEstimateParams()
    if (res && res.data) {
      if (res.data.config) {
        config.value = { ...config.value, ...res.data.config }
      }
      if (res.data.available_models) {
        availableModels.value = res.data.available_models
      }
    }
  } catch (e) {
    console.error('初始化失败:', e)
  }
})
</script>

<style scoped>
.maize-estimate-main {
  padding: 10px 20px 20px 20px;
}

.content-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.top-row {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 20px;
  width: 100%;
}

.bottom-row {
  width: 100%;
  max-width: 100%;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
  align-items: stretch;
}

.left-column .param-card,
.right-column .param-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 150px;
}

.param-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
}

.card-title {
  font-weight: 600;
  font-size: 18px;
  margin-bottom: 8px;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 4px;
}

.param-description {
  color: #606266;
  margin-bottom: 20px;
  font-size: 14px;
  line-height: 1.6;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.param-tip {
  font-size: 12px;
  color: #f56c6c;
  margin-left: 8px;
}

.upload-description {
  color: #606266;
  margin-bottom: 12px;
  font-size: 14px;
  line-height: 1.5;
  flex: 1;
}

.config-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: auto;
  padding-top: 8px;
}

.full-width {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.parameters-section {
  margin-top: 15px;
}

.parameters-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.parameter-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  align-items: flex-start;
}

.parameter-item label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.parameters-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  justify-content: center;
}

/* 确保右侧数据输入卡片内容也能填充高度 */
.right-column .param-card {
  justify-content: space-between;
}

.upload-button-wrapper {
  margin-top: auto;
  padding-top: 8px;
  display: flex;
  justify-content: center;
}

.folder-input-section {
  margin-top: 20px;
}

.input-with-button {
  display: flex;
  align-items: center;
  width: 100%;
}

.folder-form :deep(.el-form-item__label) {
  white-space: nowrap;
  overflow: visible;
}

/* 数据输入网格布局 */
.data-input-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.data-input-item {
  display: flex;
  flex-direction: column;
}

.data-input-header {
  margin-bottom: 12px;
}

.data-input-title {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
  margin-bottom: 4px;
}

.data-input-desc {
  font-size: 12px;
  color: #909399;
}

/* 上传区域样式 */
.upload-zone {
  border: 2px dashed #409eff;
  border-radius: 8px;
  padding: 30px 20px;
  text-align: center;
  background: #f0f9ff;
  margin-top: 10px;
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-zone:hover {
  border-color: #66b1ff;
  background: #e6f7ff;
}

.upload-zone.drag-over {
  border-color: #409eff;
  border-style: solid;
  background: #e6f7ff;
  transform: scale(1.02);
}

.upload-zone-content {
  color: #606266;
  width: 100%;
}

.upload-zone-content i {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 16px;
  display: block;
}

.upload-zone-content p {
  margin: 8px 0;
  font-size: 14px;
  color: #303133;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin: 12px 0;
}

/* 已选择路径显示 */
.selected-path {
  margin-top: 12px;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #303133;
}

.selected-path i {
  color: #409eff;
  font-size: 16px;
}

.selected-path span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 文件列表 */
.file-list {
  margin-top: 12px;
  max-height: 150px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 8px;
  background: #fafafa;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  margin-bottom: 4px;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.file-item:last-child {
  margin-bottom: 0;
}

.file-item i {
  color: #409eff;
  font-size: 14px;
}

.file-item span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 数据上传对话框样式 */
.maize-estimate-upload {
  padding: 10px;
}

.upload-header {
  margin-bottom: 20px;
}

.upload-data-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.upload-data-item {
  display: flex;
  flex-direction: column;
}

.multiple-upload-zone {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 30px;
  text-align: center;
  background: #fafafa;
  margin-top: 10px;
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.multiple-upload-zone:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.multiple-upload-zone.drag-over {
  border-color: #409eff;
  border-style: solid;
  background: #e6f7ff;
  transform: scale(1.02);
}

.upload-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  margin-top: 20px;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 100%;
}

.header-bar .title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-bar .actions {
  display: flex;
  gap: 10px;
}

.outputData {
  margin-top: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.result-header {
  background: #f0f9ff;
  border-bottom: 1px solid #e9ecef;
  padding: 0 20px;
}

.result-header-content {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 100%;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.result-alert {
  margin-bottom: 20px;
}

.alert-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
  font-size: 14px;
}

.alert-stats span {
  color: #67c23a;
  font-weight: 500;
}

.prediction-progress {
  padding: 20px 0;
  text-align: center;
}

.progress-text {
  margin-top: 20px;
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.progress-hint {
  margin-top: 12px;
  font-size: 14px;
  color: #909399;
}

.result-stats {
  margin: 20px 0;
}

.result-stats h4 {
  margin-bottom: 20px;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.stat-icon {
  font-size: 32px;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.stat-value {
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.result-map {
  margin: 20px 0;
}

.result-map h4 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.map-wrapper {
  width: 100%;
  height: 500px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-actions {
  text-align: center;
  padding: 20px 0;
}

.el-upload__tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

/* 任务历史样式 */
.task-history {
  padding: 20px;
}

.task-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.task-count {
  color: #606266;
  font-size: 14px;
}

.task-id {
  font-family: monospace;
  font-size: 12px;
  color: #409eff;
  word-break: break-all;
  line-height: 1.4;
}

.model-name,
.algorithm-name {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

.stats-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.stats-info span {
  line-height: 1.4;
}

.no-stats {
  color: #909399;
  font-size: 12px;
}

.no-map {
  color: #909399;
  font-size: 12px;
}

/* 地图预览样式 */
.map-preview-container {
  min-height: 600px;
  position: relative;
}

.map-preview-container .map-wrapper {
  width: 100%;
  height: 600px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.map-preview-container .no-map-data {
  padding: 40px;
  text-align: center;
}

/* 任务详情样式 */
.task-detail {
  padding: 20px;
}

.task-detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.task-info-section,
.result-summary-section,
.error-section {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.task-info-section h4,
.result-summary-section h4,
.error-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.info-label {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.info-value {
  color: #606266;
  font-size: 13px;
  word-break: break-all;
}

.task-detail .stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.task-detail .stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.task-detail .stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.task-detail .stat-icon {
  font-size: 24px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f9ff;
  border-radius: 50%;
  flex-shrink: 0;
}

.task-detail .stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.task-detail .stat-label {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
}

.task-detail .stat-value {
  font-weight: 600;
  color: #409eff;
  font-size: 18px;
  word-break: break-word;
  overflow-wrap: break-word;
}
</style>
