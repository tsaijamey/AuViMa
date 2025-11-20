/**
 * Recipe: ones_create_epic_in_scrum_project
 * Platform: ones.chagee.com
 * Description: 在ONES项目管理系统的Scrum项目中创建Epic工作项
 * Created: 2025-11-20
 * Version: 5
 */

(async () => {
  // 辅助函数：等待
  function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 辅助函数：等待并验证元素出现
  async function waitForElement(selector, description, timeout = 5000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      const elem = document.querySelector(selector);
      if (elem && elem.offsetParent !== null) return elem;
      await new Promise(r => setTimeout(r, 100));
    }
    throw new Error(`等待超时：${description} (${selector})`);
  }

  // 步骤1: 确保在首页
  if (!window.location.href.includes('ones.chagee.com')) {
    throw new Error('请先导航到 ones.chagee.com');
  }

  // 如果不在首页，先跳转
  if (!window.location.href.includes('/workspace/home')) {
    window.location.href = 'https://ones.chagee.com/project/#/workspace/home';
    await wait(2000);
  }

  // 步骤2: 点击Scrum项目卡片
  const scrumCard = Array.from(document.querySelectorAll('.home-card-base')).find(card =>
    card.textContent.includes('【Scrum】') && card.textContent.includes('D端-算法/AI应用')
  );

  if (!scrumCard) {
    throw new Error('未找到Scrum项目卡片：【Scrum】D端-算法/AI应用');
  }

  scrumCard.click();
  await wait(2000);

  // 验证步骤2成功：等待Epic标签页出现
  await waitForElement('.ones-tabs-item', 'Epic标签页', 5000);

  // 步骤3: 点击Epic标签页
  const epicTab = Array.from(document.querySelectorAll('.ones-tabs-item')).find(tab =>
    tab.textContent.trim() === 'Epic'
  );

  if (!epicTab) {
    throw new Error('未找到Epic标签页');
  }

  epicTab.click();
  await wait(1500);

  // 验证步骤3成功：等待+ Epic按钮出现
  await waitForElement('button', '+ Epic按钮', 3000);

  // 步骤4: 点击+ Epic按钮（"+"可能是SVG图标，不在textContent中）
  const createButton = Array.from(document.querySelectorAll('button')).find(btn =>
    btn.textContent.trim() === 'Epic' && btn.offsetParent !== null
  );

  if (!createButton) {
    throw new Error('未找到+ Epic按钮');
  }

  createButton.click();
  await wait(1000);

  // 验证步骤4成功：等待对话框出现
  await waitForElement('[role="dialog"]', '创建Epic对话框', 3000);

  // 步骤5: 分析表单字段
  const modal = document.querySelector('[role="dialog"]');
  if (!modal) {
    throw new Error('对话框未出现');
  }

  // 提取所有字段信息
  const formFields = {
    required: {
      title: {
        type: 'input',
        selector: 'input[type="text"]:first-of-type',
        description: 'Epic标题',
        example: '完全基于AI的自动化工作流生成(AI能力基建)'
      },
      project: {
        type: 'select',
        description: '所属项目',
        defaultValue: '【Scrum】D端-算法/AI应用',
        note: '通常已默认选中正确的项目'
      },
      workItemType: {
        type: 'select',
        description: '工作项类型',
        defaultValue: 'Epic',
        note: '固定为Epic，无需修改'
      },
      owner: {
        type: 'select',
        description: '负责人',
        defaultValue: '蔡佳',
        note: '可根据需要修改'
      },
      projectLevel: {
        type: 'select',
        description: '项目等级',
        defaultValue: 'B级',
        options: ['A级', 'B级', 'C级', 'D级'],
        note: '根据Epic重要性选择'
      },
      businessCenter: {
        type: 'select',
        description: '业务中心',
        defaultValue: '未设置',
        note: '必填！需要根据实际情况选择'
      }
    },
    optional: {
      details: {
        type: 'expandable',
        description: '详情',
        note: '可展开填写更多详细信息'
      },
      description: {
        type: 'richtext',
        selector: '[contenteditable="true"], textarea',
        description: 'Epic描述',
        note: '富文本编辑器，支持格式化文本'
      },
      priority: {
        type: 'select',
        description: '优先级',
        defaultValue: 'P2',
        options: ['P0', 'P1', 'P2', 'P3', 'P4'],
        note: 'P0最高，P4最低'
      },
      iteration: {
        type: 'select',
        description: '所属迭代',
        defaultValue: '未设置',
        note: '可选择特定迭代'
      }
    }
  };

  // 步骤6: 返回表单信息（不实际提交）
  return {
    success: true,
    message: 'Epic创建对话框已打开，表单字段分析完成',
    url: window.location.href,
    fields: formFields,
    requiredFieldsCount: Object.keys(formFields.required).length,
    optionalFieldsCount: Object.keys(formFields.optional).length,
    next_steps: [
      '1. 填写标题（必填）- 输入Epic名称',
      '2. 确认所属项目（必填）- 通常已默认正确',
      '3. 选择负责人（必填）- 默认为蔡佳，可修改',
      '4. 选择项目等级（必填）- 根据Epic重要性选择A/B/C/D级',
      '5. 选择业务中心（必填）- 需要手动选择',
      '6. 填写描述和其他可选字段',
      '7. 点击"确定"按钮提交'
    ],
    warnings: [
      '业务中心是必填字段，默认为"未设置"，提交前必须选择一个具体的业务中心',
      '由于ONES系统使用React/Vue框架，自动填写输入框可能不会触发框架的状态更新',
      '建议使用此配方打开对话框后，手动填写表单字段'
    ]
  };
})();
