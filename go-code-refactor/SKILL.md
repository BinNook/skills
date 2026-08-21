---
name: go-code-refactor
description: 指导 Go 语言项目的代码重构，涵盖分层架构设计、代码规范、性能优化和回执处理等最佳实践。当用户要求重构 Go 代码、优化 Go 项目结构、改善代码分层或进行 Go 重构前置分析（业务流程梳理、架构设计、TODO 跟踪）时使用。触发关键词："Go 重构"、"重构 Go 代码"、"代码分层"、"Go 性能优化"。
---

# Go 代码重构技能

## 技能概述

本技能用于指导 Go 语言项目的代码重构工作，包括分层架构设计、代码规范、性能优化和回执处理等方面的最佳实践。

---

## 一、重构前置工作

### 1.1 业务流程分析

在开始重构之前，必须完成以下步骤：

1. **阅读现有代码**：全面理解当前代码的业务逻辑和数据流
2. **识别痛点**：找出代码中存在的问题（函数过长、重复调用、性能问题等）
3. **绘制流程图**：使用 Mermaid 等工具绘制业务流程图
4. **输出分析文档**：将业务流程分析结果输出到 `doc/xxx_analysis.md`

### 1.2 架构设计

在理解业务后，进行架构设计：

1. **分层设计**：将代码按职责分层（基础设施层 → 同步器层 → 处理器层 → 协调器层）
2. **接口抽象**：定义清晰的接口，便于测试和扩展
3. **输出设计文档**：将架构设计输出到 `doc/xxx_refactor_design.md`

### 1.3 待办事项跟踪

创建 `TODO.list` 文件，记录重构进度：

```markdown
# 重构待办事项

## 已完成项目

| 组件 | 文件路径 | 状态 | 说明 |
|------|----------|------|------|
| 类型定义 | `scope/types/types.go` | ✅ 完成 | 同步结果等类型 |

## 待完成项目

| 组件 | 状态 | 说明 |
|------|------|------|
| 单元测试 | ⏳ 待开始 | 为各组件编写单元测试 |
```

---

## 二、代码规范

### 2.1 函数设计原则

```go
// 规范要求：
// 1. 每个函数职责单一
// 2. 代码块控制在 30-50 行
// 3. 函数嵌套不超过 3 层
// 4. 参数不超过 5 个，超过考虑使用结构体

// 好的示例
func (p *Processor) syncDepartment(dept model.Department) error {
    // 验证参数
    if err := p.validate(dept); err != nil {
        return err
    }

    // 执行同步
    return p.doSync(dept)
}

// 不好的示例（函数过长、职责不单一）
func (p *Processor) process() error {
    // 200+ 行代码，包含多个不相关的逻辑
}
```

### 2.2 常量命名规范

```go
// 规范要求：常量必须使用 ALL_CAPS_WITH_UNDERSCORES 命名风格

// 好的示例
const (
    OBJECT_TYPE_DEPT       = 1
    OBJECT_TYPE_USER       = 2
    DEPT_PAGE_SIZE         = 500
    USER_PAGE_SIZE         = 500
    LOCK_RENEW_THRESHOLD   = 1000
    ROOT_DEPARTMENT_ID     = 0
    ROOT_DEPARTMENT_CODE   = "0000"
    SYNC_RESULT_SUCCESS    = "同步成功"
)

// 不好的示例（使用驼峰命名）
const (
    ObjectTypeDept = 1  // 错误
    deptPageSize = 500  // 错误
)
```

### 2.3 注释规范

```go
// 规范要求：
// 1. 每个类型必须有用途说明
// 2. 每个函数必须说明参数、返回值、处理流程
// 3. 复杂逻辑必须有行内注释

// 好的示例
// DeptSyncResult 部门同步结果
//
// 用途：记录批量部门同步的结果，包括成功/失败数量和失败部门列表
// 生命周期：在 SyncBatch 中创建，返回给调用者
// 使用示例：
//
//	result := syncer.SyncBatch(depts)
//	if result.HasError() {
//	    log.Error("sync failed", result.ErrorCount)
//	}
type DeptSyncResult struct {
    // CreateCount 创建成功的部门数量
    CreateCount int

    // UpdateCount 更新成功的部门数量
    UpdateCount int

    // ErrorCount 同步失败的部门数量
    ErrorCount int

    // FailedDeptCodes 失败的部门 code 集合
    // Key: 部门 code
    // Value: 是否失败（始终为 true）
    FailedDeptCodes map[string]bool
}
```

### 2.4 错误处理规范

```go
// 规范要求：
// 1. 使用 errors.Is() 判断特定错误类型
// 2. 使用 fmt.Errorf() 包装错误，保留上下文
// 3. 区分可恢复错误和不可恢复错误

// 好的示例
func (p *Processor) loadUser(username string) (model.User, error) {
    user, err := p.source.User(username)
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            // 特定错误：用户未找到
            return model.User{}, fmt.Errorf("在%s数据源未找到标识为%s的人员",
                p.source.DataTypeName(), username)
        }
        // 其他错误：包装并返回
        return model.User{}, fmt.Errorf("查询用户[%s]失败: %w", username, err)
    }
    return user, nil
}
```

---

## 三、分层架构设计

### 3.1 推荐目录结构

```
scope/
├── types/
│   └── types.go          # 类型定义
├── constants.go          # 常量定义
├── interfaces.go         # 接口定义
├── context.go            # 同步上下文
├── coordinator.go        # 协调器（入口）
├── infra/                # 基础设施层
│   ├── cache_manager.go  # 缓存管理
│   ├── lock_manager.go   # 锁管理
│   ├── status_reporter.go # 状态上报
│   └── data_loader.go    # 数据加载
├── syncer/               # 同步器层
│   ├── dept_syncer.go    # 部门同步
│   ├── user_syncer.go    # 用户同步
│   └── dept_chain_resolver.go # 部门链路解析
├── processor/            # 处理器层
│   ├── dept_processor.go # 部门处理器
│   └── user_processor.go # 用户处理器
└── deleter/              # 删除器层
    ├── dept_deleter.go   # 部门删除
    └── user_deleter.go   # 用户删除
```

### 3.2 各层职责

| 层级 | 职责 | 示例 |
|------|------|------|
| 类型层 | 定义数据结构 | SyncResult, ScopeProgress |
| 基础设施层 | 提供通用能力 | 缓存、锁、状态上报、数据加载 |
| 同步器层 | 执行具体同步操作 | 创建/更新部门、用户 |
| 处理器层 | 处理单个 scope 的完整流程 | 加载数据→同步→上报 |
| 协调器层 | 协调整体流程 | 预热缓存→遍历 scope→清理资源 |

### 3.3 接口设计原则

```go
// 规范要求：
// 1. 接口应小而精，遵循单一职责
// 2. 依赖接口而非具体实现
// 3. 接口应在使用方定义

// 好的示例
type CacheManager interface {
    WarmUp(dataTypes []int) error
    GetDept(code string) (model.Department, bool)
    SetDept(dept model.Department)
    GetDeptID(code string) (int, bool)
    GetUser(username string) (model.User, bool)
    SetUser(user model.User)
    Clear()
}

type DataLoader interface {
    LoadDept(code string) (model.Department, error)
    LoadDeptTree(code string) (*types.DeptTree, error)
    LoadUser(username string) (model.User, error)
}
```

---

## 四、性能优化

### 4.1 缓存策略

```go
// 规范要求：
// 1. 在同步开始前预热缓存，避免重复 SDK 调用
// 2. 使用 map 缓存频繁查询的数据
// 3. 同步结束后清理缓存，释放内存

// 缓存管理器示例
type CacheManager struct {
    mu sync.RWMutex

    // targetDepts 目标端部门缓存
    // Key: department.Code
    targetDepts map[string]model.Department

    // targetUsers 目标端用户缓存
    // Key: user.Username
    targetUsers map[string]model.User

    // sourceDepts 数据源部门缓存
    // 避免重复调用 s.source.Department()
    sourceDepts map[string]model.Department
}

// 预热缓存
func (c *CacheManager) WarmUp(dataTypes []int) error {
    // 一次性加载所有目标端数据
    depts, err := c.dataLoader.LoadTargetDepts(dataTypes)
    if err != nil {
        return err
    }
    c.targetDepts = depts

    users, err := c.dataLoader.LoadTargetUsers(dataTypes)
    if err != nil {
        return err
    }
    c.targetUsers = users

    return nil
}
```

### 4.2 批量处理

```go
// 规范要求：
// 1. 批量操作使用合适的批次大小（如 100）
// 2. 避免在循环中进行单条 SDK 调用

// 好的示例
const USER_DELETE_BATCH_SIZE = 100

func (d *UserDeleter) deleteUsers(userIDs []int) error {
    for i := 0; i < len(userIDs); i += USER_DELETE_BATCH_SIZE {
        end := i + USER_DELETE_BATCH_SIZE
        if end > len(userIDs) {
            end = len(userIDs)
        }

        batch := userIDs[i:end]
        if err := d.target.DeleteBatchUser(batch, dataSourceType); err != nil {
            // 记录错误但继续处理
            errorCount += len(batch)
            continue
        }
        deleteCount += len(batch)
    }
    return nil
}
```

### 4.3 内存优化

```go
// 规范要求：
// 1. 预分配 slice 容量
// 2. 及时清理不再使用的数据
// 3. 避免不必要的数据拷贝

// 好的示例
func (c *SyncContext) Clear() {
    c.mu.Lock()
    defer c.mu.Unlock()

    // 清理所有缓存数据
    c.scopes = nil
    c.sortedScopes = nil
    c.scopeMap = nil
    c.completedIDs = nil
    c.syncedDepts = nil
    c.syncedUsers = nil
    c.failedChildDepts = nil
    c.failedUserDepts = nil
    c.deptProgress = nil
    c.statistics = nil
}
```

---

## 五、回执处理规范

### 5.1 回执状态规则

```go
// 核心规则：
// 1. 只有 scope 对应的人员/部门在数据源中"未找到"时，状态才是失败
// 2. 其他所有情况（包括同步错误），状态都是成功（带错误消息）

// 状态设置逻辑
func (r *StatusReporter) setScopeStatus(
    scopeItem *openapi.EIAScope,
    syncErr error,
    isBusinessContinue bool,  // true=成功状态, false=失败状态
) {
    if syncErr == nil {
        scopeItem.Status = openapi.EIASyncSuccess
        scopeItem.Result = "同步成功"
        return
    }

    if isBusinessContinue {
        // 业务可继续：状态为成功，Result 保留消息
        scopeItem.Status = openapi.EIASyncSuccess
        scopeItem.Result = syncErr.Error()
    } else {
        // 真正的错误（如未找到）：状态为失败
        scopeItem.Status = openapi.EIASyncFailed
        scopeItem.Result = syncErr.Error()
    }
}
```

### 5.2 错误消息格式

| 场景 | 消息格式 | 状态 |
|------|----------|------|
| 人员未找到 | "在{数据源}数据源未找到标识为{用户名}的人员" | 失败 |
| 部门未找到 | "在{数据源}数据源未找到标识为{部门}的部门" | 失败 |
| 人员所属部门创建失败 | "因该人员所属的部门[{部门}]创建失败，将其归属到部门[{父部门}]下" | 成功 |
| 子部门创建失败 | "因[{子部门1}][{子部门2}]创建失败，其下人员暂归属至[{主部门}]，具体失败信息查看同步程序日志" | 成功 |
| 部门成功+子部门成功+用户部分失败 | "部门[{部门}]同步成功，子部门同步成功，部分人员同步失败，具体信息查看同步服务日志" | 成功 |
| 部门成功+子部门部分失败+用户部分失败 | "部门[{部门}]同步成功，部分子部门同步失败，部分人员同步失败，具体信息查看同步服务日志" | 成功 |

---

## 六、集成与切换

### 6.1 创建新入口方法

```go
// 创建 V2 方法，使用新架构
func (s *Syncer) ExecFilterScopeV2(datasourceFilter openapi.GetDatasourceResp) error {
    // 创建门面
    scopeSync := NewScopeSync(s.source, s.target, s.updateUserNeedPassword)

    // 执行同步
    if err := scopeSync.Execute(datasourceFilter); err != nil {
        logs.Error("sync failed", logs.FieldErr(err))
    }

    // 执行删除
    if err := scopeSync.ExecuteDelete(
        cfg.DepartmentDeleteEnable,
        cfg.UserDeleteEnable,
        datasourceFilter,
    ); err != nil {
        logs.Error("delete failed", logs.FieldErr(err))
    }

    return nil
}
```

### 6.2 切换调用点

```go
// 在 Exec() 方法中切换
if len(datasourceInfo.Scope.Data) > 0 {
    // 使用新架构
    err = s.ExecFilterScopeV2(datasourceInfo)

    // 如需回滚，改为：
    // err = s.ExecFilterScope(datasourceInfo)
}
```

### 6.3 保留旧代码

重构完成后，建议保留旧代码一段时间：
- 作为对照和回滚备份
- 保留测试用例作为参考
- 验证通过后再清理

---

## 七、测试规范

### 7.1 测试框架

使用 Ginkgo v2 + Gomega 测试框架：

```go
// suite_test.go
package xxx_test

import (
    "testing"
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func TestXxx(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Xxx Suite")
}
```

### 7.2 Mock 代码组织

Mock 代码统一放入 `mock_test.go` 文件：

```go
// mock_test.go
package xxx_test

import (
    "github.com/stretchr/testify/mock"
)

type MockDataSource struct {
    mock.Mock
}

func (m *MockDataSource) Department(code string) (model.Department, error) {
    args := m.Called(code)
    return args.Get(0).(model.Department), args.Error(1)
}
```

---

## 八、检查清单

每个组件完成后确认：

- [ ] 代码行数符合规范（30-50行）
- [ ] 注释完整（说明用途、参数、返回值）
- [ ] 无重复查询（使用缓存）
- [ ] 使用常量替代魔法数字
- [ ] 常量命名使用 ALL_CAPS_WITH_UNDERSCORES
- [ ] 错误消息格式与旧代码一致
- [ ] 回执状态规则正确
- [ ] 单元测试覆盖
- [ ] 编译通过
- [ ] 集成测试通过

---

## 九、版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-01-30 | 初始版本，基于范围同步重构项目总结 |
