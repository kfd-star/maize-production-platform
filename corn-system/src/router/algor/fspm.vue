<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <div class="header-bar">
          <div class="title">玉米生长模拟</div>
          <div class="actions">
            <el-button plain @click="openDesc">参数说明</el-button>
            <el-button @click="goBack">返回</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <div class="fspm-main">
          <el-container>
            <el-main>
              <div class="content-grid">
                <!-- 左侧：参数配置 -->
                <div class="left-column">
                  <!-- 基础参数配置 -->
                  <div class="param-card">
                    <div class="card-title">基础参数配置</div>
                    <el-form :model="parameters" label-width="120px" size="small">
                      <el-form-item label="玉米品种">
                        <el-select v-model="parameters.cultivar" style="width: 200px">
                          <el-option 
                            v-for="option in cultivarOptions" 
                            :key="option" 
                            :label="option" 
                            :value="option" 
                          />
                        </el-select>
                      </el-form-item>
                      
                      <el-form-item label="种植密度">
                        <el-input-number 
                          v-model="parameters.density" 
                          :min="1000" 
                          :max="10000" 
                          :step="100"
                          style="width: 200px"
                        />
                        <span class="unit">株/公顷</span>
                      </el-form-item>
                      
                      <el-form-item label="行距">
                        <el-input-number 
                          v-model="parameters.row_distance" 
                          :min="30" 
                          :max="100" 
                          :step="5"
                          style="width: 200px"
                        />
                        <span class="unit">厘米</span>
                      </el-form-item>
                      
                      <el-form-item label="行数">
                        <el-input-number 
                          v-model="parameters.num_rows" 
                          :min="1" 
                          :max="10" 
                          :step="1"
                          style="width: 200px"
                        />
                      </el-form-item>
                      
                      <el-form-item label="每行株数">
                        <el-input-number 
                          v-model="parameters.plants_per_row" 
                          :min="1" 
                          :max="20" 
                          :step="1"
                          style="width: 200px"
                        />
                      </el-form-item>
                      
                      <el-form-item label="方位角范围">
                        <el-input-number 
                          v-model="parameters.plant_azimuth_range" 
                          :min="0" 
                          :max="90" 
                          :step="5"
                          style="width: 200px"
                        />
                        <span class="unit">度</span>
                      </el-form-item>
                      
                      <el-form-item label="ROI植物数">
                        <el-input-number 
                          v-model="parameters.roi_num_plants" 
                          :min="1" 
                          :max="20" 
                          :step="1"
                          style="width: 200px"
                        />
                      </el-form-item>
                    </el-form>
                  </div>

                  <!-- 时间参数配置 -->
                  <div class="param-card">
                    <div class="card-title">时间参数配置</div>
                    <el-form :model="parameters" label-width="120px" size="small">
                      <el-form-item label="种植日期">
                        <el-date-picker
                          v-model="plantingDate"
                          type="date"
                          placeholder="选择种植日期"
                          format="YYYY/MM/DD"
                          value-format="YYYY/MM/DD"
                          style="width: 200px"
                        />
                      </el-form-item>
                      
                      <el-form-item label="开始日期">
                        <el-date-picker
                          v-model="startDate"
                          type="date"
                          placeholder="选择开始日期"
                          format="YYYY/MM/DD"
                          value-format="YYYY/MM/DD"
                          style="width: 200px"
                        />
                      </el-form-item>
                      
                      <el-form-item label="结束日期">
                        <el-date-picker
                          v-model="endDate"
                          type="date"
                          placeholder="选择结束日期"
                          format="YYYY/MM/DD"
                          value-format="YYYY/MM/DD"
                          style="width: 200px"
                        />
                      </el-form-item>
                    </el-form>
                  </div>

                  <!-- 地理参数配置 -->
                  <div class="param-card">
                    <div class="card-title">地理参数配置</div>
                    <el-form :model="parameters" label-width="120px" size="small">
                      <el-form-item label="经度">
                        <el-input-number 
                          v-model="parameters.longitude" 
                          :min="70" 
                          :max="140" 
                          :step="0.1"
                          :precision="1"
                          style="width: 200px"
                        />
                        <span class="unit">度</span>
                      </el-form-item>
                      
                      <el-form-item label="纬度">
                        <el-input-number 
                          v-model="parameters.latitude" 
                          :min="15" 
                          :max="55" 
                          :step="0.1"
                          :precision="1"
                          style="width: 200px"
                        />
                        <span class="unit">度</span>
                      </el-form-item>
                    </el-form>
                  </div>

                  <!-- 其他参数配置 -->
                  <div class="param-card">
                    <div class="card-title">其他参数配置</div>
                    <el-form :model="parameters" label-width="120px" size="small">
                      <el-form-item label="双面刻面">
                        <el-switch v-model="parameters.double_side_facet" />
                      </el-form-item>
                      
                      <el-form-item label="冠层重建">
                        <el-select v-model="parameters.canopy_recon_mode" style="width: 200px">
                          <el-option label="是" value="True" />
                          <el-option label="否" value="False" />
                        </el-select>
                      </el-form-item>
                      
                      <el-form-item label="使用测量高度">
                        <el-select v-model="parameters.use_measured_heights" style="width: 200px">
                          <el-option label="是" value="True" />
                          <el-option label="否" value="False" />
                        </el-select>
                      </el-form-item>
                    </el-form>
                  </div>

                  <!-- 参数操作按钮 -->
                  <div class="param-actions">
                    <el-button @click="loadParameters">加载参数</el-button>
                    <el-button @click="saveParameters">保存参数</el-button>
                    <el-button @click="resetParameters">重置参数</el-button>
                  </div>
                </div>

                <!-- 右侧：文件上传和任务管理 -->
                <div class="right-column">
                  <!-- 文件上传 -->
                  <div class="upload-card">
                    <div class="card-title">文件上传</div>
                    <div class="upload-section">
                      <div class="file-upload-item">
                        <div class="file-label">植物网格文件 (.obj)</div>
                        <el-upload
                          ref="plantMeshUpload"
                          :auto-upload="false"
                          :limit="1"
                          :on-change="handlePlantMeshChange"
                          accept=".obj"
                        >
                          <el-button size="small" type="primary">选择文件</el-button>
                        </el-upload>
                        <div v-if="plantMeshFile" class="file-info">
                          {{ plantMeshFile.name }}
                        </div>
                      </div>

                      <div class="file-upload-item">
                        <div class="file-label">气象数据文件 (.csv)</div>
                        <el-upload
                          ref="meteorologicalUpload"
                          :auto-upload="false"
                          :limit="1"
                          :on-change="handleMeteorologicalChange"
                          accept=".csv"
                        >
                          <el-button size="small" type="primary">选择文件</el-button>
                        </el-upload>
                        <div v-if="meteorologicalFile" class="file-info">
                          {{ meteorologicalFile.name }}
                        </div>
                      </div>

                      <div class="file-upload-item">
                        <div class="file-label">冠层数据文件 (.csv)</div>
                        <el-upload
                          ref="canopyUpload"
                          :auto-upload="false"
                          :limit="1"
                          :on-change="handleCanopyChange"
                          accept=".csv"
                        >
                          <el-button size="small" type="primary">选择文件</el-button>
                        </el-upload>
                        <div v-if="canopyFile" class="file-info">
                          {{ canopyFile.name }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 任务管理 -->
                  <div class="task-card">
                    <div class="card-title">任务管理</div>
                    <div class="task-controls">
                      <el-button 
                        type="primary" 
                        @click="startTask"
                        :disabled="!canStartTask || taskRunning"
                        :loading="taskRunning"
                      >
                        {{ taskRunning ? '运行中...' : '开始任务' }}
                      </el-button>
                      <el-button 
                        type="danger" 
                        @click="cancelTask"
                        :disabled="!taskRunning"
                      >
                        取消任务
                      </el-button>
                      <el-button 
                        type="warning" 
                        @click="cleanupPorts"
                        :loading="cleaning"
                        style="margin-left: 10px"
                      >
                        {{ cleaning ? '清理中...' : '清理8000端口' }}
                      </el-button>
                    </div>

                    <!-- 任务状态 -->
                    <div v-if="currentTask" class="task-status">
                      <div class="status-item">
                        <span class="label">任务ID:</span>
                        <span class="value">{{ currentTask.task_id }}</span>
                      </div>
                      <div class="status-item">
                        <span class="label">状态:</span>
                        <el-tag :type="getStatusType(currentTask.status)">
                          {{ getStatusText(currentTask.status) }}
                        </el-tag>
                      </div>
                      <div class="status-item">
                        <span class="label">进度:</span>
                        <el-progress 
                          :percentage="currentTask.progress" 
                          :status="currentTask.status === 'failed' ? 'exception' : ''"
                        />
                      </div>
                      <div class="status-item">
                        <span class="label">消息:</span>
                        <span class="value">{{ currentTask.message }}</span>
                      </div>
                    </div>

                    <!-- 任务历史 -->
                    <div class="task-history">
                      <div class="history-title">任务历史</div>
                      <el-table :data="taskHistory" size="small" max-height="300">
                        <el-table-column prop="task_id" label="任务ID" width="120" />
                        <el-table-column prop="status" label="状态" width="80">
                          <template #default="scope">
                            <el-tag :type="getStatusType(scope.row.status)" size="small">
                              {{ getStatusText(scope.row.status) }}
                            </el-tag>
                          </template>
                        </el-table-column>
                        <el-table-column prop="progress" label="进度" width="80">
                          <template #default="scope">
                            {{ scope.row.progress }}%
                          </template>
                        </el-table-column>
                        <el-table-column prop="created_at" label="创建时间" width="150">
                          <template #default="scope">
                            {{ formatDate(scope.row.created_at) }}
                          </template>
                        </el-table-column>
                        <el-table-column label="操作" width="120">
                          <template #default="scope">
                            <el-button 
                              size="small" 
                              type="primary" 
                              @click="viewTaskResult(scope.row.task_id)"
                              :disabled="scope.row.status !== 'completed'"
                            >
                              查看结果
                            </el-button>
                            <el-button 
                              size="small" 
                              type="danger" 
                              @click="deleteTask(scope.row.task_id)"
                            >
                              删除
                            </el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                    </div>
                  </div>
                </div>
              </div>
            </el-main>
          </el-container>
        </div>
      </el-main>
    </el-container>

    <!-- 参数说明对话框 -->
    <el-dialog v-model="descDialogVisible" title="玉米生长模拟（FSPM）参数详细说明" width="80%">
      <div class="param-descriptions">
        <!-- 系统说明 -->
        <div class="param-group">
          <div class="group-title">🌱 系统说明</div>
          <div class="group-content">
            <p><strong>玉米生长模拟系统（FSPM）</strong>是基于功能-结构植物模型（Functional-Structural Plant Model）的玉米生长仿真系统。该系统通过模拟玉米植株的形态发育、生理过程和环境响应，预测玉米在不同环境条件下的生长表现。</p>
            <p><strong>主要功能：</strong></p>
            <ul>
              <li>模拟玉米植株的三维形态发育过程</li>
              <li>计算植株的光合作用、呼吸作用和物质分配</li>
              <li>预测玉米产量和生物量积累</li>
              <li>分析环境因子对玉米生长的影响</li>
            </ul>
          </div>
        </div>

        <!-- 输入参数说明 -->
        <div class="param-group">
          <div class="group-title">📥 输入参数说明</div>
          <div class="group-content">
            <div class="param-item">
              <div class="param-name">植物网格文件 (.obj)</div>
              <div class="param-desc">
                <p>玉米植株的三维几何模型文件，包含植株的几何形状信息。</p>
                <ul>
                  <li><strong>格式：</strong>OBJ格式的3D模型文件</li>
                  <li><strong>内容：</strong>包含顶点坐标、面片信息等几何数据</li>
                  <li><strong>用途：</strong>定义植株的初始形态结构</li>
                  <li><strong>要求：</strong>文件大小不超过50MB，包含完整的几何信息</li>
                </ul>
              </div>
            </div>

            <div class="param-item">
              <div class="param-name">气象数据文件 (.csv)</div>
              <div class="param-desc">
                <p>包含模拟期间的气象观测数据，用于驱动植物生长模型。</p>
                <ul>
                  <li><strong>格式：</strong>CSV格式，包含日期、温度、辐射等数据</li>
                  <li><strong>必需字段：</strong>日期、最高温度、最低温度、太阳辐射</li>
                  <li><strong>时间范围：</strong>建议覆盖整个生长季（3-8个月）</li>
                  <li><strong>数据质量：</strong>要求数据完整，无缺失值</li>
                </ul>
              </div>
            </div>

            <div class="param-item">
              <div class="param-name">冠层数据文件 (.csv)</div>
              <div class="param-desc">
                <p>描述玉米冠层结构和空间分布的数据文件。</p>
                <ul>
                  <li><strong>格式：</strong>CSV格式，包含位置、方位角等信息</li>
                  <li><strong>内容：</strong>植株位置坐标、叶片角度等</li>
                  <li><strong>用途：</strong>定义冠层的空间结构和光分布</li>
                  <li><strong>精度：</strong>影响光截获和光合作用计算的准确性</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- 模型参数说明 -->
        <div class="param-group">
          <div class="group-title">⚙️ 模型参数说明</div>
          <div class="group-content">
            <div class="param-item">
              <div class="param-name">模拟开始日期</div>
              <div class="param-desc">开始模拟的日期，通常为播种日期或出苗日期。格式：YYYY-MM-DD</div>
            </div>
            <div class="param-item">
              <div class="param-name">模拟结束日期</div>
              <div class="param-desc">结束模拟的日期，通常为收获日期。格式：YYYY-MM-DD</div>
            </div>
            <div class="param-item">
              <div class="param-name">时间步长（天）</div>
              <div class="param-desc">模拟的时间间隔，建议设置为1天，确保模拟精度。</div>
            </div>
            <div class="param-item">
              <div class="param-name">植株密度（株/平方米）</div>
              <div class="param-desc">单位面积内的植株数量，影响冠层结构和光截获。</div>
            </div>
            <div class="param-item">
              <div class="param-name">品种参数</div>
              <div class="param-desc">玉米品种的遗传参数，包括叶片生长速率、光合效率等。</div>
            </div>
          </div>
        </div>

        <!-- 输出结果说明 -->
        <div class="param-group">
          <div class="group-title">📊 输出结果说明</div>
          <div class="group-content">
            <div class="param-item">
              <div class="param-name">results.csv - 主要结果文件</div>
              <div class="param-desc">
                <p>包含模拟期间每日的生长数据，主要字段包括：</p>
                <ul>
                  <li><strong>date：</strong>模拟日期</li>
                  <li><strong>height(cm)：</strong>植株高度（厘米）</li>
                  <li><strong>NPP(g/plant)：</strong>净初级生产力（克/株）</li>
                </ul>
                <p><strong>注意：</strong>该文件是FSPM算法的主要输出结果，包含每日的植株高度和净初级生产力数据，可用于分析玉米生长过程和产量预测。</p>
              </div>
            </div>

            <div class="param-item">
              <div class="param-name">ProcessFiles/ - 过程文件目录</div>
              <div class="param-desc">
                <p>包含模拟过程中的中间结果和详细数据：</p>
                <ul>
                  <li><strong>1-canopy_obj：</strong>冠层3D模型文件</li>
                  <li><strong>1-canopy_pnt：</strong>冠层点云数据文件</li>
                  <li><strong>2-climate_data：</strong>气象数据处理结果</li>
                  <li><strong>3-canopy_cgf：</strong>冠层几何配置文件</li>
                  <li><strong>3-PAR_outputs：</strong>光合有效辐射输出数据</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- 使用说明 -->
        <div class="param-group">
          <div class="group-title">📋 使用说明</div>
          <div class="group-content">
            <ol>
              <li><strong>准备数据：</strong>确保所有输入文件格式正确，数据完整</li>
              <li><strong>设置参数：</strong>根据实际情况调整模拟参数</li>
              <li><strong>启动任务：</strong>点击"启动任务"开始模拟</li>
              <li><strong>监控进度：</strong>通过进度条和状态信息监控模拟进度</li>
              <li><strong>查看结果：</strong>模拟完成后查看结果摘要和详细数据</li>
              <li><strong>下载结果：</strong>可以下载CSV结果文件进行进一步分析</li>
            </ol>
          </div>
        </div>

        <!-- 注意事项 -->
        <div class="param-group">
          <div class="group-title">⚠️ 注意事项</div>
          <div class="group-content">
            <ul>
              <li>模拟时间较长，请耐心等待，不要关闭浏览器</li>
              <li>确保输入数据的时间范围与模拟日期范围一致</li>
              <li>如果模拟失败，请检查输入文件格式和数据质量</li>
              <li>结果文件会保存在服务器上，建议及时下载</li>
              <li>可以随时取消正在运行的任务</li>
            </ul>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 结果展示对话框 -->
    <el-dialog v-model="resultDialogVisible" title="玉米生长模拟结果" width="80%" :close-on-click-modal="false">
      <div v-if="currentTaskResult">
        <!-- 结果摘要 -->
        <div class="result-summary" v-if="currentTaskResult.data_summary">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-card class="summary-card">
                <div class="summary-title">模拟天数</div>
                <div class="summary-value">{{ currentTaskResult.data_summary.total_days }} 天</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="summary-card">
                <div class="summary-title">日期范围</div>
                <div class="summary-value">{{ currentTaskResult.data_summary.date_range }}</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="summary-card">
                <div class="summary-title">最大高度</div>
                <div class="summary-value">{{ currentTaskResult.data_summary.max_height.toFixed(2) }} cm</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="summary-card">
                <div class="summary-title">平均NPP</div>
                <div class="summary-value">{{ currentTaskResult.data_summary.avg_npp.toFixed(3) }} g/plant</div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- 输入文件信息 -->
        <div class="input-files-section" v-if="currentTaskResult.input_files">
          <h4>📁 输入文件</h4>
          <div class="files-grid">
            <div class="file-item" v-for="(fileName, key) in currentTaskResult.input_files" :key="key">
              <span class="file-label">{{ getFileLabel(key) }}:</span>
              <span class="file-value">{{ fileName }}</span>
            </div>
          </div>
        </div>

        <!-- 算法参数 -->
        <div class="algorithm-params-section" v-if="currentTaskResult.algorithm_params">
          <h4>⚙️ 算法参数</h4>
          <div class="params-grid">
            <div class="result-param-item" v-for="(value, key) in currentTaskResult.algorithm_params" :key="key">
              <span class="param-label">{{ getParamLabel(key) }}:</span>
              <span class="param-value">{{ value }}</span>
            </div>
          </div>
        </div>

        <!-- 输出文件路径 -->
        <div class="output-path" v-if="currentTaskResult.output_file">
          <el-alert
            title="输出文件路径"
            :description="currentTaskResult.output_file"
            type="info"
            :closable="false"
            style="margin-bottom: 20px"
          >
            <template #default>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ currentTaskResult.output_file }}</span>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="downloadResult"
                  :loading="downloading"
                >
                  {{ downloading ? '下载中...' : '下载CSV文件' }}
                </el-button>
              </div>
            </template>
          </el-alert>
        </div>

        <!-- ProcessFiles文件夹路径 -->
        <div class="process-files-path" v-if="currentTaskResult.parameters && currentTaskResult.parameters.path_process">
          <el-alert
            title="ProcessFiles文件夹路径"
            :description="currentTaskResult.parameters.path_process"
            type="success"
            :closable="false"
            style="margin-bottom: 20px"
          >
            <template #default>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ currentTaskResult.parameters.path_process }}</span>
                <el-button 
                  type="success" 
                  size="small" 
                  @click="downloadProcessFiles"
                  :loading="downloadingProcess"
                >
                  {{ downloadingProcess ? '下载中...' : '下载ProcessFiles' }}
                </el-button>
              </div>
            </template>
          </el-alert>
        </div>

        <!-- 数据表格 -->
        <div class="result-table" v-if="currentTaskResult.data">
          <el-table :data="currentTaskResult.data" stripe border max-height="400">
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="height(cm)" label="高度 (cm)" width="120">
              <template #default="scope">
                {{ parseFloat(scope.row['height(cm)']).toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="NPP(g/plant)" label="NPP (g/plant)" width="140">
              <template #default="scope">
                {{ parseFloat(scope.row['NPP(g/plant)']).toFixed(3) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 错误信息 -->
        <div v-if="currentTaskResult.data_error" class="error-message">
          <el-alert
            :title="currentTaskResult.data_error"
            type="error"
            :closable="false"
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { 
  getFSPMParameters, 
  updateFSPMParameters, 
  getFSPMDefaults,
  getFSPMDescriptions,
  startFSPMTask,
  getFSPMTaskStatus,
  cancelFSPMTask,
  listFSPMTasks,
  deleteFSPMTask
} from '@/api/fspm.js'

const router = useRouter()

// 响应式数据
const parameters = ref({
  cultivar: 'JK968',
  density: 4000,
  row_distance: 60,
  num_rows: 2,
  plants_per_row: 3,
  plant_azimuth_range: 15,
  roi_num_plants: 4,
  date_planting: '2021/06/26',
  date_start: '2021/06/30',
  date_end: '2021/09/01',
  longitude: 116.3,
  latitude: 39.5,
  double_side_facet: false,
  canopy_recon_mode: 'True',
  use_measured_heights: 'False'
})

const cultivarOptions = ['JK968', 'JNK728', 'JMC01', 'J2416', 'DE1', 'J724']

// 日期处理
const plantingDate = ref('2021/06/26')
const startDate = ref('2021/06/30')
const endDate = ref('2021/09/01')

// 文件上传
const plantMeshFile = ref(null)
const meteorologicalFile = ref(null)
const canopyFile = ref(null)

// 任务管理
const currentTask = ref(null)
const taskHistory = ref([])
const taskRunning = ref(false)
const statusCheckInterval = ref(null)

// 对话框
const descDialogVisible = ref(false)
const parameterDescriptions = ref({})
const resultDialogVisible = ref(false)
const currentTaskResult = ref(null)
const downloading = ref(false)
const downloadingProcess = ref(false)
const currentTaskId = ref(null)

// 端口清理
const cleaning = ref(false)

// 计算属性
const canStartTask = computed(() => {
  return plantMeshFile.value && meteorologicalFile.value && canopyFile.value
})

// 方法
const loadParameters = async () => {
  try {
    const response = await getFSPMParameters()
    parameters.value = response.data
    plantingDate.value = parameters.value.date_planting
    startDate.value = parameters.value.date_start
    endDate.value = parameters.value.date_end
    ElMessage.success('参数加载成功')
  } catch (error) {
    ElMessage.error('参数加载失败: ' + error.message)
  }
}

const saveParameters = async () => {
  try {
    // 更新日期参数
    parameters.value.date_planting = plantingDate.value
    parameters.value.date_start = startDate.value
    parameters.value.date_end = endDate.value
    
    await updateFSPMParameters(parameters.value)
    ElMessage.success('参数保存成功')
  } catch (error) {
    ElMessage.error('参数保存失败: ' + error.message)
  }
}

const resetParameters = async () => {
  try {
    const response = await getFSPMDefaults()
    parameters.value = response.data
    plantingDate.value = parameters.value.date_planting
    startDate.value = parameters.value.date_start
    endDate.value = parameters.value.date_end
    ElMessage.success('参数已重置为默认值')
  } catch (error) {
    ElMessage.error('参数重置失败: ' + error.message)
  }
}

const handlePlantMeshChange = (file) => {
  plantMeshFile.value = file.raw
}

const handleMeteorologicalChange = (file) => {
  meteorologicalFile.value = file.raw
}

const handleCanopyChange = (file) => {
  canopyFile.value = file.raw
}

const startTask = async () => {
  if (!canStartTask.value) {
    ElMessage.warning('请先上传所有必需文件')
    return
  }

  try {
    const formData = new FormData()
    formData.append('plant_mesh_file', plantMeshFile.value)
    formData.append('meteorological_file', meteorologicalFile.value)
    formData.append('canopy_file', canopyFile.value)

    const response = await startFSPMTask(formData)
    currentTask.value = response.data
    taskRunning.value = true
    
    // 开始状态检查
    startStatusCheck()
    
    ElMessage.success('任务已启动')
  } catch (error) {
    ElMessage.error('任务启动失败: ' + error.message)
  }
}

const cancelTask = async () => {
  if (!currentTask.value) return

  try {
    // 立即更新前端状态为"取消中"
    currentTask.value.status = 'cancelling'
    currentTask.value.message = '正在取消任务...'
    ElMessage.info('正在取消任务...')
    
    // 发送取消请求到后端
    await cancelFSPMTask(currentTask.value.task_id)
    
    // 继续状态检查，等待后端确认取消
    // 不立即停止状态检查，让后端确认取消状态
  } catch (error) {
    ElMessage.error('任务取消失败: ' + error.message)
    // 如果取消失败，恢复原状态
    if (currentTask.value) {
      currentTask.value.status = 'running'
      currentTask.value.message = '取消失败，任务继续运行'
    }
  }
}

const startStatusCheck = () => {
  statusCheckInterval.value = setInterval(async () => {
    if (!currentTask.value) return

    try {
      const response = await getFSPMTaskStatus(currentTask.value.task_id)
      currentTask.value = response.data
      
      if (['completed', 'failed', 'cancelled'].includes(currentTask.value.status)) {
        taskRunning.value = false
        stopStatusCheck()
        loadTaskHistory()
      }
      
      // 如果后端确认了取消状态，停止检查
      if (currentTask.value.status === 'cancelled') {
        ElMessage.success('任务已取消')
      }
    } catch (error) {
      console.error('状态检查失败:', error)
    }
  }, 2000)
}

const stopStatusCheck = () => {
  if (statusCheckInterval.value) {
    clearInterval(statusCheckInterval.value)
    statusCheckInterval.value = null
  }
}

const loadTaskHistory = async () => {
  try {
    const response = await listFSPMTasks()
    taskHistory.value = response.data.tasks
  } catch (error) {
    console.error('加载任务历史失败:', error)
  }
}

const deleteTask = async (taskId) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${taskId}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deleteFSPMTask(taskId)
    loadTaskHistory()
    ElMessage.success('任务已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('任务删除失败: ' + error.message)
    }
  }
}

const viewTaskResult = async (taskId) => {
  try {
    const response = await getFSPMTaskStatus(taskId)
    const task = response.data
    
    if (task.status === 'completed' && task.result) {
      currentTaskResult.value = task.result
      currentTaskId.value = taskId
      resultDialogVisible.value = true
    } else {
      ElMessage.warning('任务尚未完成或没有结果数据')
    }
  } catch (error) {
    ElMessage.error('获取任务结果失败: ' + error.message)
  }
}

const downloadResult = async () => {
  if (!currentTaskId.value) return
  
  try {
    downloading.value = true
    const response = await fetch(`/api/fspm/download/${currentTaskId.value}`)
    
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `results_${currentTaskId.value}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('文件下载成功')
    } else {
      ElMessage.error('文件下载失败')
    }
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloading.value = false
  }
}

const downloadProcessFiles = async () => {
  if (!currentTaskId.value) return
  
  try {
    downloadingProcess.value = true
    console.log('开始下载ProcessFiles:', currentTaskId.value)
    
    const response = await fetch(`/api/fspm/download/process/${currentTaskId.value}`)
    console.log('响应状态:', response.status, response.statusText)
    console.log('响应头:', response.headers)
    
    if (response.ok) {
      const blob = await response.blob()
      console.log('Blob大小:', blob.size, '字节')
      console.log('Blob类型:', blob.type)
      
      if (blob.size === 0) {
        ElMessage.error('下载的文件为空，请检查服务器端压缩包')
        return
      }
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ProcessFiles_${currentTaskId.value}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success(`ProcessFiles文件夹下载成功 (${(blob.size / 1024 / 1024).toFixed(2)} MB)`)
    } else {
      const errorText = await response.text()
      console.error('下载失败:', response.status, errorText)
      ElMessage.error(`ProcessFiles文件夹下载失败: ${response.status}`)
    }
  } catch (error) {
    console.error('下载异常:', error)
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingProcess.value = false
  }
}

const cleanupPorts = async () => {
  try {
    cleaning.value = true
    ElMessage.info('正在清理8000端口...')
    
    const response = await fetch('/api/fspm/cleanup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      ElMessage.success(`端口清理成功: ${result.message}`)
    } else {
      const error = await response.json()
      ElMessage.error(`端口清理失败: ${error.detail}`)
    }
  } catch (error) {
    ElMessage.error('端口清理失败: ' + error.message)
  } finally {
    cleaning.value = false
  }
}

const getStatusType = (status) => {
  const statusMap = {
    pending: 'info',
    running: 'warning',
    cancelling: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '等待中',
    running: '运行中',
    cancelling: '取消中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString()
}


const openDesc = async () => {
  try {
    const response = await getFSPMDescriptions()
    parameterDescriptions.value = response.data.descriptions
    descDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取参数说明失败: ' + error.message)
  }
}

const goBack = () => {
  router.go(-1)
}

// 文件标签处理函数
const getFileLabel = (key) => {
  const labels = {
    'plant_mesh_file': '植物网格文件',
    'meteorological_file': '气象数据文件',
    'canopy_file': '冠层数据文件'
  }
  return labels[key] || key
}

// 参数标签处理函数
const getParamLabel = (key) => {
  const labels = {
    'cultivar': '玉米品种',
    'density': '种植密度',
    'row_distance': '行距',
    'num_rows': '行数',
    'plants_per_row': '每行株数',
    'plant_azimuth_range': '植物方位角范围',
    'roi_num_plants': 'ROI植物数量',
    'date_planting': '种植日期',
    'date_start': '开始日期',
    'date_end': '结束日期',
    'longitude': '经度',
    'latitude': '纬度',
    'double_side_facet': '双面刻面',
    'canopy_recon_mode': '冠层重建模式',
    'use_measured_heights': '使用测量高度'
  }
  return labels[key] || key
}

// 生命周期
onMounted(() => {
  loadParameters()
  loadTaskHistory()
})

onUnmounted(() => {
  stopStatusCheck()
})
</script>

<style scoped>
/* Header样式 */
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.actions {
  display: flex;
  gap: 10px;
}

.fspm-main {
  padding: 20px;
  margin-top: -20px; /* 内容上移，保持顶部一行不变 */
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  /* 移除固定高度，让内容自然流动，使用浏览器滚动条 */
}

.left-column, .right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  /* 移除内部滚动，使用浏览器滚动条 */
  overflow: visible;
  height: auto; /* 移除固定高度，让内容自然流动 */
}

.param-card, .upload-card, .task-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #333;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.unit {
  margin-left: 8px;
  color: #666;
  font-size: 12px;
}

.param-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.file-upload-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-label {
  font-weight: 500;
  color: #333;
}

.file-info {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.task-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.task-status {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.status-item:last-child {
  margin-bottom: 0;
}

.label {
  font-weight: 500;
  margin-right: 10px;
  min-width: 60px;
}

.value {
  color: #666;
}

.task-history {
  margin-top: 20px;
}

.history-title {
  font-weight: 500;
  margin-bottom: 10px;
  color: #333;
}

.param-descriptions {
  max-height: 400px;
  overflow-y: auto;
}

.param-desc-item {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.param-desc-item:last-child {
  border-bottom: none;
}

.param-name {
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.param-desc {
  color: #666;
  line-height: 1.5;
}

/* 结果展示样式 */
.result-summary {
  margin-bottom: 20px;
}

.summary-card {
  text-align: center;
  padding: 10px;
}

.summary-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.output-path {
  margin-bottom: 20px;
}

.result-table {
  margin-top: 20px;
}

.error-message {
  margin-top: 20px;
}

/* 参数说明对话框样式 */
.param-descriptions {
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 10px;
}

.param-group {
  margin-bottom: 30px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.group-title {
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: white;
  padding: 15px 20px;
  font-size: 16px;
  font-weight: bold;
  margin: 0;
}

.group-content {
  padding: 20px;
  background: #fafbfc;
}

.param-item {
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #409eff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.param-item:last-child {
  margin-bottom: 0;
}

.param-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.param-name::before {
  content: "📌";
  margin-right: 8px;
  font-size: 14px;
}

.param-desc {
  color: #606266;
  line-height: 1.6;
}

.param-desc p {
  margin: 0 0 10px 0;
}

.param-desc ul, .param-desc ol {
  margin: 10px 0;
  padding-left: 20px;
}

.param-desc li {
  margin-bottom: 5px;
  line-height: 1.5;
}

.param-desc strong {
  color: #409eff;
  font-weight: 600;
}

/* 滚动条样式 */
.param-descriptions::-webkit-scrollbar {
  width: 6px;
}

.param-descriptions::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.param-descriptions::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.param-descriptions::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 结果展示对话框中的输入文件和算法参数样式 */
.input-files-section, .algorithm-params-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.input-files-section h4, .algorithm-params-section h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.files-grid, .params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

/* 结果展示对话框中的文件项和参数项样式 */
.file-item, .result-param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  height: 48px;
  min-height: 48px;
  max-height: 48px;
}

.file-label, .param-label {
  font-weight: 600;
  color: #606266;
  min-width: 120px;
}

.file-value, .param-value {
  color: #303133;
  font-family: 'Courier New', monospace;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  height: 24px;
  min-height: 24px;
  max-height: 24px;
  display: flex;
  align-items: center;
  word-break: break-all;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
