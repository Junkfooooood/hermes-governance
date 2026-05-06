/**
 * Centralized state mapping: internal states → human-readable labels.
 * Preserves internal names as tooltip/debug info.
 */

export interface StateInfo {
  label: string;
  shortLabel: string;
  category: "pending" | "active" | "success" | "error" | "rejected";
  color: { bg: string; text: string; dot: string };
  description: string;
}

const STATE_MAP: Record<string, StateInfo> = {
  created: {
    label: "等待处理",
    shortLabel: "等待",
    category: "pending",
    color: { bg: "bg-gray-100", text: "text-gray-700", dot: "bg-gray-400" },
    description: "事务已创建，等待开始处理",
  },
  interview: {
    label: "需求澄清中",
    shortLabel: "澄清",
    category: "active",
    color: { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" },
    description: "中书省正在分析和澄清需求",
  },
  interview_complete: {
    label: "需求已澄清",
    shortLabel: "已澄清",
    category: "active",
    color: { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" },
    description: "需求澄清完成，准备制定方案",
  },
  plan: {
    label: "制定方案中",
    shortLabel: "规划",
    category: "active",
    color: { bg: "bg-indigo-50", text: "text-indigo-700", dot: "bg-indigo-500" },
    description: "中书省正在制定执行方案",
  },
  plan_complete: {
    label: "方案已制定",
    shortLabel: "已规划",
    category: "active",
    color: { bg: "bg-indigo-50", text: "text-indigo-700", dot: "bg-indigo-500" },
    description: "执行方案已制定，等待审核",
  },
  review: {
    label: "合规审核中",
    shortLabel: "审核",
    category: "active",
    color: { bg: "bg-purple-50", text: "text-purple-700", dot: "bg-purple-500" },
    description: "门下省正在审核方案合规性",
  },
  review_spec_complete: {
    label: "合规审核通过",
    shortLabel: "合规通过",
    category: "active",
    color: { bg: "bg-purple-50", text: "text-purple-700", dot: "bg-purple-500" },
    description: "方案合规性审核通过",
  },
  review_quality: {
    label: "质量审核中",
    shortLabel: "质检",
    category: "active",
    color: { bg: "bg-purple-50", text: "text-purple-700", dot: "bg-purple-500" },
    description: "门下省正在审核方案质量",
  },
  review_quality_complete: {
    label: "质量审核通过",
    shortLabel: "质检通过",
    category: "active",
    color: { bg: "bg-purple-50", text: "text-purple-700", dot: "bg-purple-500" },
    description: "方案质量审核通过",
  },
  decompose: {
    label: "任务分解中",
    shortLabel: "分解",
    category: "active",
    color: { bg: "bg-cyan-50", text: "text-cyan-700", dot: "bg-cyan-500" },
    description: "尚书省正在将方案拆解为原子任务",
  },
  decompose_complete: {
    label: "任务已分解",
    shortLabel: "已分解",
    category: "active",
    color: { bg: "bg-cyan-50", text: "text-cyan-700", dot: "bg-cyan-500" },
    description: "任务分解完成，准备派发",
  },
  dispatch: {
    label: "任务派发中",
    shortLabel: "派发",
    category: "active",
    color: { bg: "bg-teal-50", text: "text-teal-700", dot: "bg-teal-500" },
    description: "尚书省正在向六部派发执行合同",
  },
  dispatch_complete: {
    label: "已派发执行",
    shortLabel: "已派发",
    category: "active",
    color: { bg: "bg-teal-50", text: "text-teal-700", dot: "bg-teal-500" },
    description: "执行合同已派发到各部",
  },
  execute: {
    label: "执行中",
    shortLabel: "执行",
    category: "active",
    color: { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" },
    description: "六部正在并行执行任务",
  },
  execute_complete: {
    label: "执行完成",
    shortLabel: "已执行",
    category: "active",
    color: { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" },
    description: "所有子任务执行完成",
  },
  verify: {
    label: "验证中",
    shortLabel: "验证",
    category: "active",
    color: { bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" },
    description: "刑部正在验证执行结果",
  },
  verify_complete: {
    label: "验证通过",
    shortLabel: "已验证",
    category: "active",
    color: { bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" },
    description: "执行结果验证通过",
  },
  integrate: {
    label: "结果整合中",
    shortLabel: "整合",
    category: "active",
    color: { bg: "bg-green-50", text: "text-green-700", dot: "bg-green-500" },
    description: "尚书省正在整合最终结果",
  },
  complete: {
    label: "已完成",
    shortLabel: "完成",
    category: "success",
    color: { bg: "bg-green-100", text: "text-green-800", dot: "bg-green-500" },
    description: "事务处理完成",
  },
  rejected: {
    label: "已驳回",
    shortLabel: "驳回",
    category: "rejected",
    color: { bg: "bg-red-100", text: "text-red-800", dot: "bg-red-500" },
    description: "方案被门下省驳回",
  },
  error: {
    label: "处理失败",
    shortLabel: "失败",
    category: "error",
    color: { bg: "bg-red-100", text: "text-red-800", dot: "bg-red-500" },
    description: "处理过程中出现错误",
  },
};

const AGENT_LIFECYCLE_MAP: Record<string, { label: string; color: string }> = {
  idle: { label: "空闲", color: "text-gray-500" },
  activated: { label: "已激活", color: "text-blue-600" },
  execute: { label: "执行中", color: "text-blue-600" },
  deactivate: { label: "已停用", color: "text-gray-400" },
};

const ROLE_LABELS: Record<string, string> = {
  zhongshu: "中书省",
  menxia: "门下省",
  shangshu: "尚书省",
  gongbu: "工部",
  hubu: "户部",
  libu: "礼部",
  bingbu: "兵部",
  xingbu: "刑部",
  "libu-renshi": "吏部",
};

const ROLE_DESCRIPTIONS: Record<string, string> = {
  zhongshu: "决策规划 — 需求澄清、方案制定",
  menxia: "审核把关 — 合规审核、质量审核",
  shangshu: "执行调度 — 任务分解、派发、整合",
  gongbu: "工程执行 — 代码编写、文件操作",
  hubu: "资源管理 — 数据处理、Web操作",
  libu: "文档管理 — 文档编写、格式化",
  bingbu: "运行执行 — 终端命令、进程管理",
  xingbu: "质量验证 — 测试、安全扫描",
  "libu-renshi": "人事管理 — 人员分配、协调",
};

const TIER_LABELS: Record<string, string> = {
  ministry: "三省 (决策层)",
  department: "六部 (执行层)",
};

export function getStateInfo(state: string): StateInfo {
  return (
    STATE_MAP[state] ?? {
      label: state,
      shortLabel: state,
      category: "pending",
      color: { bg: "bg-gray-100", text: "text-gray-600", dot: "bg-gray-400" },
      description: "未知状态",
    }
  );
}

export function getAgentLifecycle(lifecycle: string) {
  return (
    AGENT_LIFECYCLE_MAP[lifecycle] ?? {
      label: lifecycle,
      color: "text-gray-500",
    }
  );
}

export function getRoleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}

export function getRoleDescription(role: string): string {
  return ROLE_DESCRIPTIONS[role] ?? "";
}

export function getTierLabel(tier: string): string {
  return TIER_LABELS[tier] ?? tier;
}

export function isActiveState(state: string): boolean {
  const info = getStateInfo(state);
  return info.category === "active";
}

export function isTerminalState(state: string): boolean {
  const info = getStateInfo(state);
  return info.category === "success" || info.category === "error" || info.category === "rejected";
}
