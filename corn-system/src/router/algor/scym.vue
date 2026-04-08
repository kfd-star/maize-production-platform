<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <div class="header-bar">
          <div class="title">玉米产量预测区域版（API2）</div>
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
                <!-- 第一行：算法配置和数据输入 -->
                <div class="top-row">
                  <!-- 左侧：算法配置 -->
                <div class="left-column">
                  <div class="param-card">
                      <div class="card-title">算法配置</div>
                    <div class="param-description">
                        配置SCYM算法的输出参数
                    </div>
                      <el-form label-width="120px">
                        <el-form-item label="产量输出前缀">
                          <el-input v-model="scymAlgorithmConfig.yield_output_prefix" placeholder="test_Cropland_Yield_2025" />
                       </el-form-item>
                     </el-form>
                    <div class="config-actions">
                        <el-button type="primary" @click="saveAlgorithmConfig" size="small">保存配置</el-button>
                        <el-button @click="getCurrentAlgorithmConfig" size="small">获取当前配置</el-button>
                        <el-button @click="resetAlgorithmDefaults" size="small">重置为默认值</el-button>
                    </div>
                  </div>
                </div>

                <!-- 右侧：数据输入 -->
                <div class="right-column">
                  <div class="param-card">
                    <div class="card-title">数据输入</div>
                    <div class="upload-description">
                        上传Sentinel-2影像、ERA5气象数据、玉米分布掩膜和ROI区域文件，这些文件包含用于玉米产量预测区域版（API2）预测的所有输入数据
                    </div>
                    <div class="upload-button-wrapper">
                      <el-button type="primary" @click="showDataUpload = true" size="large">
                        开始上传数据文件并预测
                      </el-button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 第二行：模型系数配置（横跨两列） -->
                <div class="bottom-row">
                  <div class="param-card full-width">
                    <div class="card-title">模型系数配置</div>
                    <div class="param-description">
                      调整统计模型的系数参数以优化预测性能
                    </div>
                    
                    <div class="coefficients-section">
                      <div class="coefficients-grid">
                        <div class="coefficient-item">
                          <label>常数项 (constant):</label>
                          <el-input v-model.number="scymCoefficients.constant" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>平均温度 (tmean):</label>
                          <el-input v-model.number="scymCoefficients.tmean" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>平均温度² (tmean2):</label>
                          <el-input v-model.number="scymCoefficients.tmean2" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>降雨 (rain):</label>
                          <el-input v-model.number="scymCoefficients.rain" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>降雨² (rain2):</label>
                          <el-input v-model.number="scymCoefficients.rain2" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>基础值 (base_value):</label>
                          <el-input v-model.number="scymCoefficients.base_value" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>GCVI常数 (gcvi_constant):</label>
                          <el-input v-model.number="scymCoefficients.gcvi_constant" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>GCVI温度 (gcvi_tmean):</label>
                          <el-input v-model.number="scymCoefficients.gcvi_tmean" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>GCVI温度² (gcvi_tmean2):</label>
                          <el-input v-model.number="scymCoefficients.gcvi_tmean2" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>GCVI降雨 (gcvi_rain):</label>
                          <el-input v-model.number="scymCoefficients.gcvi_rain" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>GCVI降雨² (gcvi_rain2):</label>
                          <el-input v-model.number="scymCoefficients.gcvi_rain2" size="small" style="width:150px" />
                        </div>
                        <div class="coefficient-item">
                          <label>GCVI乘数 (gcvi_multiplier):</label>
                          <el-input v-model.number="scymCoefficients.gcvi_multiplier" size="small" style="width:150px" />
                        </div>
                      </div>
                      <div class="coefficients-actions">
                        <el-button type="primary" @click="saveCoefficients" size="small">保存系数</el-button>
                        <el-button @click="getCurrentCoefficients" size="small">获取当前系数</el-button>
                        <el-button @click="resetCoefficientsDefaults" size="small">重置为默认值</el-button>
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
            <span>玉米产量预测区域版（API2）预测结果</span>
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
                  <span class="stat-label">平均单产</span>
                  <span class="stat-value">{{ output.static_info?.mean?.toFixed(2) || output.per_unit_yield?.toFixed(2) || 'N/A' }} kg/亩</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📊</div>
                <div class="stat-content">
                  <span class="stat-label">单产预测</span>
                  <span class="stat-value">{{ output.per_unit_yield?.toFixed(2) || output.static_info?.mean?.toFixed(2) || 'N/A' }} kg/亩</span>
                </div>
              </div>
                </div>
              </div>

          <!-- PNG预览区域 -->
          <div class="result-preview" v-if="output.task_id" style="margin-top: 20px;">
            <h4>🖼️ 结果预览</h4>
            <div class="preview-container" style="display: flex; flex-direction: column; align-items: center; gap: 10px;">
              <div class="preview-image-wrapper result-preview-wrapper">
                <img 
                  v-if="previewCache[output.task_id]"
                  :src="previewCache[output.task_id]" 
                  alt="预测结果预览" 
                  class="preview-image result-preview-image"
                  @error="(e) => handlePreviewError(e, output.task_id)"
                  @load="handlePreviewLoad"
                  @click="showPreviewImage(previewCache[output.task_id])"
                />
                <div v-else class="preview-loading result-preview-loading" @click="loadPreviewImage(output.task_id)">
                  <i class="el-icon-picture"></i>
                  <span>点击加载预览图</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="result-actions" style="margin-top: 20px; text-align: center;">
            <el-button type="success" @click="downloadResult('tif')" size="large">
              <i class="el-icon-download"></i> 下载TIF
            </el-button>
            <el-button type="success" @click="downloadResult('png')" size="large" style="margin-left: 10px;">
              <i class="el-icon-download"></i> 下载PNG
            </el-button>
            <el-button type="success" @click="downloadResult('json')" size="large" style="margin-left: 10px;">
              <i class="el-icon-download"></i> 下载JSON
            </el-button>
          </div>
        </el-main>
      </el-container>
    </div>

    <!-- 数据文件上传对话框 -->
    <el-dialog v-model="showDataUpload" title="玉米产量预测区域版（API2） - 数据文件上传" width="90%" :close-on-click-modal="false">
      <div class="maize-estimate-upload">
        <div class="upload-header">
          <el-alert
            title="文件上传说明"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              请上传以下文件：Sentinel-2影像（.tif）、ERA5气象数据（.tif）、玉米分布掩膜（.tif）、ROI区域（Shapefile文件）。
              支持点击选择文件夹、拖拽文件到对应区域两种方式。所有文件上传完成后，点击"开始预测"按钮进行分析。
            </template>
          </el-alert>
        </div>
        
        <!-- 四个数据输入区域 -->
        <div class="upload-data-grid" style="grid-template-columns: 1fr 1fr;">
          <!-- Sentinel-2影像 -->
          <div class="upload-data-item">
            <div class="data-input-header">
              <div class="data-input-title">Sentinel-2影像</div>
              <div class="data-input-desc">包含所有.tif文件</div>
            </div>
            <div 
              class="multiple-upload-zone"
              :class="{ 'drag-over': s2DragOver }"
              @dragover.prevent="handleS2DragOver"
              @dragleave.prevent="handleS2DragLeave"
              @drop.prevent="handleS2Drop"
            >
              <div class="upload-zone-content">
                <i class="el-icon-upload"></i>
                <p>拖拽多个.tif文件到此处</p>
                <p class="upload-hint">或</p>
                <el-button @click="selectS2Folder" type="primary" size="default">选择文件夹</el-button>
                <input ref="s2Input" type="file" webkitdirectory directory multiple @change="handleS2Select" style="display: none" accept=".tif" />
              </div>
            </div>
            <div v-if="s2Files.length > 0" class="file-list">
              <div v-for="(file, index) in s2Files" :key="index" class="file-item">
                <i class="el-icon-document"></i><span>{{ file.name }}</span>
              </div>
            </div>
            </div>
            
          <!-- ERA5气象数据 -->
          <div class="upload-data-item">
            <div class="data-input-header">
              <div class="data-input-title">ERA5气象数据</div>
              <div class="data-input-desc">包含所有.tif文件</div>
            </div>
            <div 
              class="multiple-upload-zone"
              :class="{ 'drag-over': era5DragOver }"
              @dragover.prevent="handleEra5DragOver"
              @dragleave.prevent="handleEra5DragLeave"
              @drop.prevent="handleEra5Drop"
            >
              <div class="upload-zone-content">
                <i class="el-icon-upload"></i>
                <p>拖拽多个.tif文件到此处</p>
                <p class="upload-hint">或</p>
                <el-button @click="selectEra5Folder" type="primary" size="default">选择文件夹</el-button>
                <input ref="era5Input" type="file" webkitdirectory directory multiple @change="handleEra5Select" style="display: none" accept=".tif" />
              </div>
            </div>
            <div v-if="era5Files.length > 0" class="file-list">
              <div v-for="(file, index) in era5Files" :key="index" class="file-item">
                <i class="el-icon-document"></i><span>{{ file.name }}</span>
              </div>
            </div>
          </div>

          <!-- 玉米分布掩膜 -->
          <div class="upload-data-item">
            <div class="data-input-header">
              <div class="data-input-title">玉米分布掩膜</div>
              <div class="data-input-desc">单个.tif文件</div>
            </div>
            <div 
              class="multiple-upload-zone"
              :class="{ 'drag-over': maskDragOver }"
              @dragover.prevent="handleMaskDragOver"
              @dragleave.prevent="handleMaskDragLeave"
              @drop.prevent="handleMaskDrop"
            >
              <div class="upload-zone-content">
                <i class="el-icon-upload"></i>
                <p>拖拽.tif文件到此处</p>
                <p class="upload-hint">或</p>
                <el-button @click="selectMaskFile" type="primary" size="default">选择文件</el-button>
                <input ref="maskInput" type="file" @change="handleMaskSelect" style="display: none" accept=".tif" />
              </div>
            </div>
            <div v-if="maskFile" class="file-list">
              <div class="file-item">
                <i class="el-icon-document"></i><span>{{ maskFile.name }}</span>
              </div>
            </div>
            </div>
            
          <!-- ROI区域 -->
          <div class="upload-data-item">
            <div class="data-input-header">
              <div class="data-input-title">ROI区域</div>
              <div class="data-input-desc">包含.shp, .shx, .dbf, .prj, .CPG, .sbn, .sbx, .shp.xml文件</div>
              </div>
            <div 
              class="multiple-upload-zone"
              :class="{ 'drag-over': roiDragOver }"
              @dragover.prevent="handleRoiDragOver"
              @dragleave.prevent="handleRoiDragLeave"
              @drop.prevent="handleRoiDrop"
            >
              <div class="upload-zone-content">
                <i class="el-icon-upload"></i>
                <p>拖拽Shapefile文件到此处</p>
                <p class="upload-hint">或</p>
                <el-button @click="selectRoiFolder" type="primary" size="default">选择文件夹</el-button>
                <input ref="roiInput" type="file" webkitdirectory directory multiple @change="handleRoiSelect" style="display: none" accept=".shp,.shx,.dbf,.prj,.CPG,.cpg,.sbn,.sbx,.xml" />
              </div>
            </div>
            <div v-if="roiFiles.length > 0" class="file-list">
              <div v-for="(file, index) in roiFiles" :key="index" class="file-item">
                <i class="el-icon-document"></i><span>{{ file.name }}</span>
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
    <el-dialog v-model="showTaskHistory" title="玉米产量预测区域版（API2）任务历史" width="95%" :close-on-click-modal="false">
      <div class="task-history">
        <div class="task-history-header">
          <el-button @click="loadTaskHistory" :loading="taskHistoryLoading" size="small">
            <i class="el-icon-refresh"></i> 刷新
          </el-button>
          <span class="task-count">共 {{ taskHistory.length }} 个任务</span>
        </div>
        
        <el-table :data="taskHistory" v-loading="taskHistoryLoading" stripe style="width: 100%">
          <el-table-column prop="task_id" label="任务ID" width="250">
            <template #default="{ row }">
              <span class="task-id">{{ row.task_id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="算法" width="200">
            <template #default="{ row }">
              <span class="algorithm-name">玉米产量预测区域版（API2）</span>
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
          <el-table-column label="统计信息" width="300" align="center">
            <template #default="{ row }">
              <div v-if="row.static_info" class="stats-info">
                <span>单产: {{ parseStaticInfo(row.static_info).mean?.toFixed(2) || row.per_unit_yield?.toFixed(2) || 'N/A' }} kg/亩</span>
              </div>
              <span v-else class="no-stats">无统计信息</span>
            </template>
          </el-table-column>
          <el-table-column label="预览结果" width="200" align="center">
            <template #default="{ row }">
              <div v-if="row.status === 'completed' && row.output_png" class="preview-container">
                <div class="preview-image-wrapper">
                  <img 
                    v-if="previewCache[row.task_id]"
                    :src="previewCache[row.task_id]" 
                    alt="预览图" 
                    class="preview-image"
                    @error="(e) => handlePreviewError(e, row.task_id)"
                    @load="handlePreviewLoad"
                    @click="showPreviewImage(previewCache[row.task_id])"
                  />
                  <div v-else class="preview-loading" @click="loadPreviewImage(row.task_id)">
                    <span>点击加载预览</span>
                  </div>
                </div>
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="downloadPngResult(row)"
                  style="margin-top: 8px; width: 100%"
                >
                  下载PNG
                </el-button>
              </div>
              <span v-else class="no-preview">无预览</span>
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
              <span>平均单产: {{ getStatValue(taskDetailData, 'mean') || taskDetailData.per_unit_yield?.toFixed(2) || 'N/A' }} kg/亩</span>
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
              <div class="info-item">
                <span class="info-label">使用模型:</span>
                <span class="info-value">玉米产量预测区域版（API2）</span>
              </div>
              <div class="info-item" v-if="taskDetailData.output_path">
                <span class="info-label">输出路径:</span>
                <span class="info-value">{{ simplifyOutputPath(taskDetailData.output_path) }}</span>
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
                  <span class="stat-label">平均单产</span>
                  <span class="stat-value">{{ getStatValue(taskDetailData, 'mean') || taskDetailData.per_unit_yield?.toFixed(2) || 'N/A' }} kg/亩</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📊</div>
                <div class="stat-content">
                  <span class="stat-label">单产预测</span>
                  <span class="stat-value">{{ taskDetailData.per_unit_yield?.toFixed(2) || getStatValue(taskDetailData, 'mean') || 'N/A' }} kg/亩</span>
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

    <!-- 图片预览对话框 -->
    <el-dialog 
      v-model="showImagePreview" 
      title="预览图片" 
      width="90%" 
      :close-on-click-modal="true"
      align-center
    >
      <div class="image-preview-container">
        <img 
          :src="previewImageUrl" 
          alt="预览图" 
          class="preview-full-image"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  runScym,
  getScymParams,
  updateScymParams,
  getScymDefaults,
  getScymTasks,
  getScymTask,
  deleteScymTask,
  downloadScymResult,
  cancelScymTask
} from '@/api/scym.js'

const router = useRouter()

// 页面状态
const predicting = ref(false)
const output = ref(null)
const showDataUpload = ref(false)
const showTaskHistory = ref(false)
const showTaskDetail = ref(false)
const showImagePreview = ref(false)
const previewImageUrl = ref('')
const taskHistory = ref([])
const taskHistoryLoading = ref(false)
const taskDetailData = ref(null)
const abortController = ref(null) // 用于取消请求的控制器
const progressText = ref('正在上传文件并运行预测，请稍候...') // 进度提示文本
const taskDetailLoading = ref(false)
const selectedTask = ref(null)
const currentTaskId = ref(null) // 当前运行的任务ID

// 文件夹路径
const folderPaths = ref({
  dataFolder: '',
  shpFolder: ''
})

// 拖拽状态
const s2DragOver = ref(false)
const era5DragOver = ref(false)
const maskDragOver = ref(false)
const roiDragOver = ref(false)

// 文件列表
const s2Files = ref([])
const era5Files = ref([])
const maskFile = ref(null)
const roiFiles = ref([])

// 输出前缀配置（保留用于向后兼容）
const outputPrefix = ref('scym_prediction')

// SCYM参数配置
const scymCoefficients = ref({
  constant: -648.7124,
  tmean: 491.0432,
  tmean2: -11.9421,
  rain: 5.1636,
  rain2: -0.0032,
  base_value: 1424.7642,
  gcvi_constant: -5.1387,
  gcvi_tmean: -0.1163,
  gcvi_tmean2: 0.0035,
  gcvi_rain: -0.0025,
  gcvi_rain2: 0.00000175,
  gcvi_multiplier: 1197.3193
})

const scymAlgorithmConfig = ref({
  yield_output_prefix: 'test_Cropland_Yield_2025'
})

// 文件输入框引用
const s2Input = ref(null)
const era5Input = ref(null)
const maskInput = ref(null)
const roiInput = ref(null)

// Sentinel-2文件处理
const selectS2Folder = () => { if (s2Input.value) s2Input.value.click() }
const handleS2Select = (event) => {
  const files = Array.from(event.target.files || []).filter(f => f.name.toLowerCase().endsWith('.tif'))
  if (files.length === 0) { ElMessage.warning('所选文件夹中没有找到.tif文件'); return }
  s2Files.value = files
  ElMessage.success(`已选择 ${files.length} 个Sentinel-2文件`)
  if (s2Input.value) s2Input.value.value = ''
}
const handleS2DragOver = () => { s2DragOver.value = true }
const handleS2DragLeave = () => { s2DragOver.value = false }
const handleS2Drop = (event) => {
  s2DragOver.value = false
  const files = Array.from(event.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith('.tif'))
  if (files.length === 0) { ElMessage.warning('请拖拽.tif格式的文件'); return }
  s2Files.value = files
  ElMessage.success(`已选择 ${files.length} 个Sentinel-2文件`)
}

// ERA5文件处理
const selectEra5Folder = () => { if (era5Input.value) era5Input.value.click() }
const handleEra5Select = (event) => {
  const files = Array.from(event.target.files || []).filter(f => f.name.toLowerCase().endsWith('.tif'))
  if (files.length === 0) { ElMessage.warning('所选文件夹中没有找到.tif文件'); return }
  era5Files.value = files
  ElMessage.success(`已选择 ${files.length} 个ERA5文件`)
  if (era5Input.value) era5Input.value.value = ''
}
const handleEra5DragOver = () => { era5DragOver.value = true }
const handleEra5DragLeave = () => { era5DragOver.value = false }
const handleEra5Drop = (event) => {
  era5DragOver.value = false
  const files = Array.from(event.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith('.tif'))
  if (files.length === 0) { ElMessage.warning('请拖拽.tif格式的文件'); return }
  era5Files.value = files
  ElMessage.success(`已选择 ${files.length} 个ERA5文件`)
}

// 掩膜文件处理
const selectMaskFile = () => { if (maskInput.value) maskInput.value.click() }
const handleMaskSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.tif')) { ElMessage.warning('请选择.tif格式的文件'); return }
  maskFile.value = file
  ElMessage.success('已选择掩膜文件')
  if (maskInput.value) maskInput.value.value = ''
}
const handleMaskDragOver = () => { maskDragOver.value = true }
const handleMaskDragLeave = () => { maskDragOver.value = false }
const handleMaskDrop = (event) => {
  maskDragOver.value = false
  const file = Array.from(event.dataTransfer.files).find(f => f.name.toLowerCase().endsWith('.tif'))
  if (!file) { ElMessage.warning('请拖拽.tif格式的文件'); return }
  maskFile.value = file
  ElMessage.success('已选择掩膜文件')
}

// ROI文件处理
const selectRoiFolder = () => { if (roiInput.value) roiInput.value.click() }
const handleRoiSelect = (event) => {
  const files = Array.from(event.target.files || []).filter(f => {
    const name = f.name.toLowerCase()
    return name.endsWith('.shp') || name.endsWith('.shx') || name.endsWith('.dbf') || 
           name.endsWith('.prj') || name.endsWith('.cpg') || name.endsWith('.sbn') || 
           name.endsWith('.sbx') || name.endsWith('.shp.xml') || (name.endsWith('.xml') && name.includes('.shp'))
  })
  if (files.length === 0) { ElMessage.warning('所选文件夹中没有找到Shapefile文件'); return }
  if (!files.some(f => f.name.toLowerCase().endsWith('.shp'))) { ElMessage.warning('Shapefile必须包含.shp文件'); return }
  roiFiles.value = files
  ElMessage.success(`已选择 ${files.length} 个ROI文件`)
  if (roiInput.value) roiInput.value.value = ''
  }
const handleRoiDragOver = () => { roiDragOver.value = true }
const handleRoiDragLeave = () => { roiDragOver.value = false }
const handleRoiDrop = (event) => {
  roiDragOver.value = false
  const files = Array.from(event.dataTransfer.files).filter(f => {
    const name = f.name.toLowerCase()
    return name.endsWith('.shp') || name.endsWith('.shx') || name.endsWith('.dbf') || 
           name.endsWith('.prj') || name.endsWith('.cpg') || name.endsWith('.sbn') || 
           name.endsWith('.sbx') || name.endsWith('.shp.xml') || (name.endsWith('.xml') && name.includes('.shp'))
  })
  if (files.length === 0) { ElMessage.warning('请拖拽Shapefile相关文件'); return }
  if (!files.some(f => f.name.toLowerCase().endsWith('.shp'))) { ElMessage.warning('Shapefile必须包含.shp文件'); return }
  roiFiles.value = files
  ElMessage.success(`已选择 ${files.length} 个ROI文件`)
}

// SCYM使用固定配置，无需参数管理

// 返回
const goBack = () => router.push('/home/algor')

// 确认上传并开始预测
const handleUploadConfirm = async () => {
  // 检查是否选择了文件
  if (s2Files.value.length === 0) {
    ElMessage.error('请上传Sentinel-2影像文件')
    return
  }
  
  if (era5Files.value.length === 0) {
    ElMessage.error('请上传ERA5气象数据文件')
    return
  }
  
  // 检查ERA5文件数量，给出内存警告
  if (era5Files.value.length > 100) {
    // 估算内存需求（假设每个文件6个波段，尺寸2631x4290，float64类型）
    const estimatedMemory = (era5Files.value.length * 6 * 2631 * 4290 * 8 / 1024 / 1024 / 1024).toFixed(1)
    try {
      await ElMessageBox.confirm(
        `⚠️ 内存警告\n\n` +
        `您上传了 ${era5Files.value.length} 个ERA5文件，这可能需要约 ${estimatedMemory} GiB 内存。\n\n` +
        `如果您的系统内存不足，可能会遇到内存分配错误。\n\n` +
        `建议：\n` +
        `1. 减少ERA5文件数量到100个以内\n` +
        `2. 使用更小的研究区域\n` +
        `3. 确保系统有足够的可用内存\n\n` +
        `是否继续？`,
        '内存警告',
        {
          confirmButtonText: '继续',
          cancelButtonText: '取消',
          type: 'warning',
          dangerouslyUseHTMLString: false
        }
      )
    } catch {
      // 用户点击取消
    return
  }
  }
  
  if (!maskFile.value) {
    ElMessage.error('请上传玉米分布掩膜文件')
    return
  }
  
  // ROI文件可选
  // if (roiFiles.value.length === 0) {
  //   ElMessage.warning('建议上传ROI区域文件')
  // }
  
  // 关闭对话框
  showDataUpload.value = false
  
  // 开始预测
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
    
    // 上传Sentinel-2文件
    progressText.value = `正在上传 ${s2Files.value.length} 个Sentinel-2文件...`
    s2Files.value.forEach(file => {
      formData.append('s2_files', file)
    })
    
    // 上传ERA5文件
    progressText.value = `正在上传 ${era5Files.value.length} 个ERA5文件...`
    era5Files.value.forEach(file => {
      formData.append('era5_files', file)
      })
    
    // 上传掩膜文件
    if (maskFile.value) {
      progressText.value = '正在上传掩膜文件...'
      formData.append('mask_file', maskFile.value)
    }
    
    // 上传ROI文件（可选）
    if (roiFiles.value.length > 0) {
      progressText.value = `正在上传 ${roiFiles.value.length} 个ROI文件...`
      roiFiles.value.forEach(file => {
        formData.append('roi_files', file)
      })
    }
    
    // 添加输出前缀
    if (outputPrefix.value) {
      formData.append('output_prefix', outputPrefix.value)
    }
    
    // 更新进度提示
    progressText.value = '文件上传完成，正在运行玉米产量预测区域版（API2）预测算法，请稍候...（预计需要较长时间）'
    
    // 开始预测请求
    const res = await runScym(formData, abortController.value)
    
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
      
      // 显示成功消息，包含单产信息
      const perUnitYield = res.data.result.per_unit_yield || stats.mean || 0
      
      ElMessage.success({
        message: `预测完成！平均单产: ${perUnitYield.toFixed(2)} kg/亩`,
        duration: 5000,
        showClose: true
      })
      
      // 自动加载任务详情并显示
      if (res.data.result.task_id) {
        await loadTaskDetail(res.data.result.task_id)
        showTaskDetail.value = true
        // 自动加载PNG预览
        if (res.data.result.task_id && !previewCache.value[res.data.result.task_id]) {
          loadPreviewImage(res.data.result.task_id).catch(err => {
            console.error('加载预览图片失败:', err)
          })
        }
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
      // 提取错误信息
      let errorMessage = '预测失败'
      if (e.response?.data?.detail) {
        errorMessage = e.response.data.detail
      } else if (e.response?.data?.msg) {
        errorMessage = e.response.data.msg
      } else if (e.message) {
        errorMessage = e.message
      }
      
      // 检测内存错误
      if (errorMessage.includes('内存不足') || errorMessage.includes('Unable to allocate') || 
          errorMessage.includes('MemoryError') || errorMessage.includes('ArrayMemoryError')) {
        ElMessage.error({
          message: errorMessage.replace(/\n/g, '<br>'),
          duration: 15000,
          showClose: true,
          dangerouslyUseHTMLString: true
        })
      } else {
        ElMessage.error('预测失败: ' + errorMessage)
      }
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
        await cancelScymTask(currentTaskId.value)
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
  s2Files.value = []
  era5Files.value = []
  maskFile.value = null
  roiFiles.value = []
  s2DragOver.value = false
  era5DragOver.value = false
  maskDragOver.value = false
  roiDragOver.value = false
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
    const res = await getScymTasks()
    if (res && res.data) {
      taskHistory.value = res.data.tasks || []
      
      // 预加载已完成任务的预览图片
      for (const task of taskHistory.value) {
        if (task.status === 'completed' && task.output_png && !previewCache.value[task.task_id]) {
          // 异步加载，不阻塞界面
          loadPreviewImage(task.task_id).catch(err => {
            console.error(`加载任务 ${task.task_id} 预览失败:`, err)
          })
        }
      }
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
    const res = await getScymTask(taskId)
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
    
    await deleteScymTask(task.task_id)
    ElMessage.success('任务删除成功')
    await loadTaskHistory() // 重新加载任务列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

// 下载结果
const downloadResult = async (format) => {
  if (!output.value || !output.value.task_id) {
    ElMessage.error('没有可下载的结果')
    return
  }
  
  try {
    const res = await downloadScymResult(output.value.task_id, format)
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const ext = format === 'tif' ? 'tif' : format === 'png' ? 'png' : 'json'
    link.download = `scym_result.${ext}`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (e) {
    ElMessage.error('下载失败')
  }
}

const downloadTaskResult = async (task) => {
  try {
    // 默认下载TIF格式
    const res = await downloadScymResult(task.task_id, 'tif')
    
    // 创建下载链接
    const blob = new Blob([res.data], { type: 'image/tiff' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `scym_result_${task.task_id}.tif`
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

// PNG 预览图片缓存
const previewCache = ref({})

// 获取预览图片 URL（同步返回，如果缓存中没有则返回空字符串，由图片加载事件处理）
const getPreviewUrl = (taskId) => {
  return previewCache.value[taskId] || ''
}

// 加载预览图片
const loadPreviewImage = async (taskId) => {
  // 如果已经加载过，直接返回
  if (previewCache.value[taskId]) {
    return
  }
  
  try {
    const res = await downloadScymResult(taskId, 'png')
    const blob = new Blob([res.data], { type: 'image/png' })
    const url = window.URL.createObjectURL(blob)
    previewCache.value[taskId] = url
  } catch (error) {
    console.error('加载预览图片失败:', error)
    // 不设置缓存，让图片显示错误占位符
  }
}

// 处理预览图片加载错误
const handlePreviewError = (event, taskId) => {
  // 尝试加载图片
  if (!previewCache.value[taskId]) {
    loadPreviewImage(taskId).then(() => {
      // 重新设置图片源
      if (previewCache.value[taskId]) {
        event.target.src = previewCache.value[taskId]
      } else {
        event.target.style.display = 'none'
      }
    })
  } else {
    event.target.style.display = 'none'
  }
}

// 处理预览图片加载成功
const handlePreviewLoad = (event) => {
  // 图片加载成功，可以显示
}

// 显示预览图片（放大）
const showPreviewImage = (imageUrl) => {
  previewImageUrl.value = imageUrl
  showImagePreview.value = true
}

// 下载 PNG 结果
const downloadPngResult = async (task) => {
  try {
    const res = await downloadScymResult(task.task_id, 'png')
    
    // 创建下载链接
    const blob = new Blob([res.data], { type: 'image/png' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `scym_result_${task.task_id}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('PNG文件下载成功')
  } catch (error) {
    console.error('下载PNG文件失败:', error)
    ElMessage.error('下载PNG文件失败')
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
  return modelName || 'SCYM'
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

// 初始化
// 初始化参数
const initParams = async () => {
  try {
    await fetchScymParams()
  } catch (e) {
    console.log('初始化参数失败:', e)
  }
}

// 获取SCYM参数
const fetchScymParams = async () => {
  try {
    const res = await getScymParams()
    if (res && res.data) {
      if (res.data.coefficients) {
        scymCoefficients.value = { ...scymCoefficients.value, ...res.data.coefficients }
      }
      if (res.data.algorithm_config) {
        scymAlgorithmConfig.value = { ...scymAlgorithmConfig.value, ...res.data.algorithm_config }
        // 同步到 outputPrefix（向后兼容）
        if (res.data.algorithm_config.yield_output_prefix) {
          outputPrefix.value = res.data.algorithm_config.yield_output_prefix
        }
      }
    }
  } catch (e) {
    console.log('获取参数失败:', e)
  }
}

// 保存模型系数
const saveCoefficients = async () => {
  try {
    await updateScymParams({
      coefficients: scymCoefficients.value
    })
    ElMessage.success('模型系数已保存')
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || '模型系数保存失败'
    ElMessage.error(typeof msg === 'string' ? msg : '模型系数保存失败')
  }
}

// 获取当前模型系数
const getCurrentCoefficients = async () => {
  try {
    await fetchScymParams()
    ElMessage.success('已获取当前模型系数')
  } catch (e) {
    ElMessage.error('获取模型系数失败')
  }
}

// 重置模型系数为默认值
const resetCoefficientsDefaults = async () => {
  try {
    const res = await getScymDefaults()
    if (res && res.data && res.data.coefficients) {
      scymCoefficients.value = { ...res.data.coefficients }
      ElMessage.success('已重置为默认值')
    }
  } catch (e) {
    ElMessage.error('重置失败')
  }
}

// 保存算法配置
const saveAlgorithmConfig = async () => {
  try {
    await updateScymParams({
      algorithm_config: scymAlgorithmConfig.value
    })
    ElMessage.success('算法配置已保存')
    // 同步到 outputPrefix（向后兼容）
    outputPrefix.value = scymAlgorithmConfig.value.yield_output_prefix
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || '算法配置保存失败'
    ElMessage.error(typeof msg === 'string' ? msg : '算法配置保存失败')
  }
}

// 获取当前算法配置
const getCurrentAlgorithmConfig = async () => {
  try {
    await fetchScymParams()
    ElMessage.success('已获取当前算法配置')
  } catch (e) {
    ElMessage.error('获取算法配置失败')
  }
}

// 重置算法配置为默认值
const resetAlgorithmDefaults = async () => {
  try {
    const res = await getScymDefaults()
    if (res && res.data && res.data.algorithm_config) {
      scymAlgorithmConfig.value = { ...res.data.algorithm_config }
      // 同步到 outputPrefix（向后兼容）
      outputPrefix.value = scymAlgorithmConfig.value.yield_output_prefix
      ElMessage.success('已重置为默认值')
    }
  } catch (e) {
    ElMessage.error('重置失败')
  }
}

onMounted(async () => {
  await initParams()
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
}

.bottom-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
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

.full-width {
  grid-column: 1 / -1;
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

.result-preview {
  margin: 20px 0;
}

.result-preview h4 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.result-preview .preview-image-wrapper.result-preview-wrapper {
  max-width: 100%;
  width: 100%;
  max-height: 800px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 10px;
  background: #f9f9f9;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.result-preview .preview-image.result-preview-image {
  max-width: 100%;
  max-height: 780px;
  width: auto;
  height: auto;
  object-fit: contain;
  cursor: pointer;
  border-radius: 4px;
  transition: transform 0.3s, box-shadow 0.3s;
  display: block;
}

.result-preview .preview-image:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.result-preview .preview-loading.result-preview-loading {
  text-align: center;
  padding: 40px;
  cursor: pointer;
  color: #409eff;
  transition: background-color 0.3s;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.result-preview .preview-loading.result-preview-loading i {
  font-size: 48px;
  margin-bottom: 10px;
  display: block;
}

.result-preview .preview-loading.result-preview-loading:hover {
  background-color: #ecf5ff;
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
  overflow-x: auto;
}

.task-history .el-table {
  min-width: 1500px;
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
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
  text-align: center;
}

.stats-info span {
  line-height: 1.4;
  text-align: center;
}

.no-stats {
  color: #909399;
  font-size: 12px;
  text-align: center;
  display: block;
}

/* 预览图片样式 */
.preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0 auto;
  width: 100%;
}

.preview-image-wrapper {
  width: 120px;
  height: 120px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  cursor: pointer;
  transition: transform 0.3s;
}

.preview-image:hover {
  transform: scale(1.05);
  opacity: 0.9;
}

/* 图片预览对话框样式 */
.image-preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  max-height: 80vh;
  overflow: auto;
  background: #f5f7fa;
  padding: 20px;
}

.preview-full-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.preview-loading {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #909399;
  font-size: 12px;
  gap: 8px;
  transition: background-color 0.3s;
}

.preview-loading:hover {
  background-color: #e4e7ed;
}

.preview-loading span {
  text-align: center;
}

.no-preview {
  color: #909399;
  font-size: 12px;
}

/* 参数配置样式 */
.coefficients-section {
  margin-top: 20px;
}

.coefficients-section h4 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.coefficients-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.coefficient-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.coefficient-item label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.coefficients-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  justify-content: center;
}

.config-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
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
