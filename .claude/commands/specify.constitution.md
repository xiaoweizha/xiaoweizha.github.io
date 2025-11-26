# Specify Constitution

Display the design system constitution and guidelines for this Specify project.

## Design System Constitution

### 核心原则 (Core Principles)

1. **一致性 (Consistency)** - 所有设计元素应保持一致的视觉语言
2. **可访问性 (Accessibility)** - 遵循WCAG 2.1 AA标准
3. **可扩展性 (Scalability)** - 设计系统应能适应未来的需求变化
4. **简洁性 (Simplicity)** - 保持设计的简洁和直观

### Token 分类规范

#### 颜色 (Colors)
- **主色调**: `--color-primary-*` (50-900)
- **次要色**: `--color-secondary-*` (50-900)
- **中性色**: `--color-neutral-*` (50-900)
- **语义色**: `--color-success`, `--color-warning`, `--color-error`, `--color-info`
- **表面色**: `--color-surface-*`, `--color-background-*`

#### 间距 (Spacing)
- **基础单位**: 4px
- **尺度**: `--spacing-xs` (4px), `--spacing-sm` (8px), `--spacing-md` (16px), `--spacing-lg` (24px), `--spacing-xl` (32px), `--spacing-xxl` (48px)

#### 字体 (Typography)
- **字体族**: `--font-family-primary`, `--font-family-secondary`, `--font-family-mono`
- **字号**: `--font-size-xs` 到 `--font-size-xxl`
- **行高**: `--line-height-tight`, `--line-height-normal`, `--line-height-loose`
- **字重**: `--font-weight-light`, `--font-weight-normal`, `--font-weight-medium`, `--font-weight-bold`

#### 阴影 (Shadows)
- **层级**: `--shadow-xs`, `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-xl`
- **用途**: 用于表示元素的层级和重要性

#### 边框和圆角 (Borders & Radius)
- **边框宽度**: `--border-width-thin`, `--border-width-thick`
- **圆角**: `--border-radius-xs` 到 `--border-radius-full`

### 命名约定 (Naming Conventions)

1. **语义化命名**: 使用描述用途的名称而非具体值
   - 好：`--color-primary`, `--spacing-md`
   - 坏：`--color-blue`, `--spacing-16px`

2. **层级结构**: 使用连字符分隔层级
   - `--component-element-variant-state`
   - 例如: `--button-primary-background-hover`

3. **状态修饰符**:
   - `hover`, `focus`, `active`, `disabled`
   - `pressed`, `selected`, `expanded`

### 组件规范

#### 按钮 (Buttons)
- **变体**: primary, secondary, tertiary, ghost
- **尺寸**: xs, sm, md, lg, xl
- **状态**: default, hover, focus, active, disabled

#### 输入框 (Inputs)
- **类型**: text, email, password, number, search
- **状态**: default, focus, error, success, disabled
- **尺寸**: sm, md, lg

### 质量标准

1. **对比度**: 文本与背景的对比度至少为4.5:1
2. **触摸目标**: 最小44x44px的可点击区域
3. **响应式**: 支持移动端、平板和桌面端
4. **暗色模式**: 所有组件必须支持暗色主题

### 工作流程

1. **设计**: 在Figma中使用标准化的tokens
2. **同步**: 使用`npm run specify:pull`同步到代码
3. **实现**: 在组件中使用生成的CSS变量
4. **测试**: 确保符合可访问性和响应式要求
5. **文档**: 更新组件文档和使用示例

### 版本管理

- **主版本**: 破坏性变更（删除tokens或重大重命名）
- **次版本**: 新增功能（新tokens或组件变体）
- **补丁版本**: 修复和微调（颜色值优化等）

---

此constitution定义了本项目设计系统的核心规范，所有设计决策都应遵循这些原则。