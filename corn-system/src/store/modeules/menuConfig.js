//
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
/* 
    title: 树形结构名称
    key: 树结点的唯一标识符,
    type: 数据类型,
    level：树节点的层级，最上层为1，依次往下增加
    children: 子节点 */
export const useMenuConfig = defineStore(
  'MenuConfig',
  () => {
    const menuConfig = ref([
      {
        title: '基础数据',
        key: 'basedata',
        level: 1,
        childrend: [
          {
            title: '气象数据',
            key: 'climate',
            level: 2,
            childrend: [
              {
                title: 'climate',
                key: 'climate',
                type: 'table',
                level: 3,
              },
            ],
          },
          {
            title: '土壤数据',
            key: 'soil',
            level: 2,
            childrend: [
              {
                title: 'Soil',
                type: 'table',
                key: 'Soil',
                level: 3,
              },
            ],
          },
          {
            title: 'fertilization',
            key: 'fertilization',
            level: 2,
            childrend: [
              {
                title: 'fertilization',
                type: 'table',
                key: 'fertilization',
                level: 3,
              },
            ],
          },
          {
            title: 'future_data',
            key: 'future',
            level: 2,
            childrend: [
              {
                title: 'future',
                type: 'table',
                key: 'future',
                level: 3,
              },
            ],
          },
          {
            title: 'irrigation_data',
            key: 'irrigation',
            level: 2,
            childrend: [
              {
                title: 'irrigation',
                type: 'table',
                key: 'irrigation',
                level: 3,
              },
            ],
          },
          {
            title: 'multi_site',
            key: 'multi_site',
            level: 2,
            childrend: [
              {
                title: 'multi_site_fertilizer',
                type: 'table',
                key: 'multi_site_fertilizer',
                level: 3,
              },
            ],
          },
          {
            title: 'nitrogen_limited',
            key: 'nitrogen_limited',
            level: 2,
            childrend: [
              {
                title: 'nitrogen_limited_fertilizer',
                type: 'table',
                key: 'nitrogen_limited_fertilizer',
                level: 3,
              },
            ],
          },
          {
            title: 'potential_bj',
            key: 'potential_bj',
            level: 2,
            childrend: [
              {
                title: 'potential_bj_fertilizer',
                type: 'table',
                key: 'potential_bj_fertilizer',
                level: 3,
              },
            ],
          },
          {
            title: 'potential_fz',
            key: 'potential_fz',
            level: 2,
            childrend: [
              {
                title: 'potential_fz_fertilizer',
                type: 'table',
                key: 'potential_fz_fertilizer',
                level: 3,
              },
            ],
          },
          {
            title: 'sowing_data',
            key: 'sowing',
            level: 2,
            childrend: [
              {
                title: 'sowing',
                type: 'table',
                key: 'sowing',
                level: 3,
              },
            ],
          },
          {
            title: 'variety_data',
            key: 'variety',
            level: 2,
            childrend: [
              {
                title: 'variety',
                type: 'table',
                key: 'variety',
                level: 3,
              },
            ],
          },
          {
            title: 'water_limited',
            key: 'water_limited',
            level: 2,
            childrend: [
              {
                title: 'water_limited',
                type: 'table',
                key: 'water_limited',
                level: 3,
              },
              {
                title: 'water_limited_fz',
                type: 'table',
                key: 'water_limited_fz',
                level: 3,
              },
            ],
          },
          {
            title: '2023',
            key: '2023',
            level: 2,
            childrend: [
              {
                title: '2023数据',
                type: 'table',
                key: '2023数据',
                level: 3,
              },
            ],
          },
          {
            title: '矢量数据',
            key: 'vector',
            level: 2,
            childrend: [
              {
                title: '红星农场地块矢量图',
                type: 'geojson',
                key: 'hxnc',
                level: 3,
                checked: false,
              },
            ],
          },
          {
            title: '影像数据',
            key: 'image',
            level: 2,
            childrend: [
              {
                title: '周围_7_8月份_Sentinel卫星_RGB_visualize',
                type: 'image',
                key: 'image0',
                name: '0',
                level: 3,
                checked: false,
              },
              {
                title: '典型地块(1区3组3西8月15日)_无人机多光谱_四波段合成',
                type: 'image',
                key: 'image1',
                name: '1',
                level: 3,
                checked: false,
              },

              {
                title: '典型地块(1区3组3西8月15日)_无人机多光谱_RedEdge',
                type: 'image',
                key: 'image2',
                name: '2',
                level: 3,
                checked: false,
              },
              {
                title: '典型地块(1区3组3西8月15日)_无人机多光谱_Red',
                type: 'image',
                key: 'image3',
                name: '3',
                level: 3,
                checked: false,
              },

              {
                title: '典型地块(1区3组3西8月15日)_无人机多光谱_NIR',
                type: 'image',
                key: 'image4',
                name: '4',
                level: 3,
                checked: false,
              },
              {
                title: '典型地块(1区3组3西8月15日)_无人机多光谱_Green',
                type: 'image',
                key: 'image5',
                name: '5',
                level: 3,
                checked: false,
              },

              {
                title: '典型地块(1区3组3西8月15日)_无人机RGB影像',
                type: 'image',
                key: 'image6',
                name: '6',
                level: 3,
                checked: false,
              },
              {
                title: '地块_7_8月份_Sentinel卫星_RGB_visualize',
                type: 'image',
                key: 'image7',
                name: '7',
                level: 3,
                checked: false,
              },
            ],
          },
        ],
      },
      {
        title: '模型算法',
        key: 'algorithm',
        level: 1,
        childrend: [
          {
            title: 'LAI同化算法',
            key: 'lai',
            level: 2,
            type: 'algor',
          },
          {
            title: '玉米生长模拟',
            key: 'shine',
            level: 2,
            type: 'algor',
          },
          {
            title: '玉米产量预测',
            key: 'production',
            level: 2,
            type: 'algor',
          },
          {
            title: '玉米产量预测区域版（API1）',
            key: 'maizeEstimate',
            level: 2,
            type: 'algor',
          },
          {
            title: '玉米产量预测区域版（GNAH）',
            key: 'gnah',
            level: 2,
            type: 'algor',
          },
        ],
      },
      {
        title: '生产力预测',
        key: 'prediction',
        level: 1,
        childrend: [],
      },
      {
        title: '专题图输出',
        key: 'subject',
        level: 1,
        childrend: [],
      },
    ])
    //所属分类赋值
    const belongCategory = ref('')
    //找到第三层数据的父节点
    const findParentTitle = (targetKey, menu = menuConfig.value) => {
      for (const item of menu) {
        if (item.childrend) {
          for (const child of item.childrend) {
            if (child.title === targetKey) {
              return item.title // 找到目标的父级，返回父级的 title
            }
            // 一层一层递归
            const parentTitle = findParentTitle(targetKey, item.childrend)
            if (parentTitle) {
              belongCategory.value = parentTitle
              return parentTitle
            }
          }
        }
      }
      return null // 没找到返回 null
    }
    // 上传execl时，在第二层的childrend中添加数据
    // 上传 Excel 时，在第二层的 childrend 中添加数据
    const addFileToMenu = (newFile) => {
      // 找到目标一级目录
      const parent = menuConfig.value.find((item) =>
        item.childrend.some((child) => child.title === belongCategory.value),
      )

      if (parent) {
        // 找到二级目录
        const target = parent.childrend.find(
          (child) => child.title === belongCategory.value,
        )

        if (target) {
          // 添加新对象到 childrend
          target.childrend.push(newFile)
        } else {
          console.warn(`未找到 key 为 "${belongCategory.value}" 的二级目录`)
        }
      } else {
        console.warn(`未找到包含 "${belongCategory.value}" 的一级目录`)
      }
    }
    //删除第三层的数据
    const delThreeMenu = (filename, menu = menuConfig.value) => {
      for (const item of menu) {
        if (item.childrend) {
          for (const child of item.childrend) {
            if (child.title === filename) {
              return (item.childrend = item.childrend.filter(
                (child) => child.title !== filename,
              )) //
            }
            // 一层一层递归
            delThreeMenu(filename, item.childrend)
          }
        }
      }
      return null // 没找到返回 null
    }

    return {
      addFileToMenu,
      menuConfig,
      belongCategory,
      findParentTitle,
      delThreeMenu,
    }
  },
  {
    persist: true,
  },
)
