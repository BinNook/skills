---
name: go-development-standards
description: 定义 Go 项目的开发规范，包括代码分层架构、代码组织、测试标准等。当用户进行 Go 语言开发（新功能开发、代码重构、单元测试编写、Bug 修复）时应遵循这些规范。触发关键词："Go 开发规范"、"Go 代码规范"、"Go 项目结构"、"Go 单元测试规范"。
---

# Go 开发规范技能

本技能定义了 Go 项目的开发规范、代码组织、测试标准等要求。Claude 在进行 Go 开发时应遵循这些规范。

## 触发条件

当用户要求进行 Go 语言开发时使用本技能，包括：
- 新功能开发
- 代码重构
- 单元测试编写
- Bug 修复

---

## 1. 代码分层架构

### 1.1 分层原则

采用分层架构，依赖方向从上到下，禁止反向依赖：

```
types (类型定义层)
   ↓
infra (基础设施层)
   ↓
syncer/loader (数据操作层)
   ↓
processor (业务处理层)
   ↓
coordinator (协调层)
```

### 1.2 各层职责

| 层级 | 职责 | 示例 |
|-----|------|-----|
| types | 接口定义、数据结构、常量 | `DataLoader` 接口、`SyncResult` 结构体 |
| infra | 基础设施：缓存、锁、上报 | `CacheManager`、`LockManager` |
| syncer/loader | 具体数据操作 | `DepartmentSyncer`、`DataLoader` |
| processor | 业务流程处理 | `DeptProcessor`、`UserProcessor` |
| coordinator | 流程协调、组装 | `SyncCoordinator` |

### 1.3 依赖注入

- 所有依赖通过构造函数注入
- 构造函数命名：`NewXxx(deps...) *Xxx`
- 依赖使用接口类型，不使用具体实现

```go
// 正确示例
func NewUserProcessor(
    dataLoader types.DataLoader,
    userSyncer types.UserSyncer,
    cache types.CacheManager,
) *UserProcessor {
    return &UserProcessor{
        dataLoader: dataLoader,
        userSyncer: userSyncer,
        cache:      cache,
    }
}

// 错误示例：直接依赖具体实现
func NewUserProcessor(loader *DataLoaderImpl) *UserProcessor { ... }
```

---

## 2. 接口设计规范

### 2.1 接口定义位置

- 接口统一定义在 `types` 包中
- 接口实现放在对应的功能包中

### 2.2 接口命名

| 类型 | 命名规则 | 示例 |
|-----|---------|-----|
| 行为接口 | 动词+er | `DataLoader`、`StatusReporter` |
| 能力接口 | 形容词+able | `Cacheable`、`Syncable` |
| 管理类接口 | 名词+Manager | `CacheManager`、`LockManager` |

### 2.3 接口粒度

- 接口应该小而专注（接口隔离原则）
- 避免"胖接口"，单个接口方法不超过 5-7 个
- 复杂功能拆分为多个小接口

```go
// 正确：小而专注的接口
type DataLoader interface {
    LoadDept(code string) (Department, error)
    LoadUser(username string) (User, error)
}

type CacheManager interface {
    GetDept(code string) (Department, bool)
    SetDept(dept Department)
}

// 错误：过于庞大的接口
type AllInOneManager interface {
    LoadDept(code string) (Department, error)
    LoadUser(username string) (User, error)
    GetDept(code string) (Department, bool)
    SetDept(dept Department)
    Lock() error
    Unlock() error
    // ... 更多方法
}
```

---

## 3. 错误处理规范

### 3.1 错误分类

根据业务影响将错误分为两类：

| 错误类型 | 处理方式 | 示例 |
|---------|---------|-----|
| 致命错误 | 终止流程，返回失败 | 数据源"未找到"错误 |
| 可继续错误 | 记录日志，继续处理 | 网络超时、临时错误 |

### 3.2 错误判断

```go
import (
    "errors"
    "gorm.io/gorm"
)

// 判断是否为"未找到"错误
func isNotFoundError(err error) bool {
    return errors.Is(err, gorm.ErrRecordNotFound)
}

// 根据错误类型决定处理方式
func handleError(err error) {
    if isNotFoundError(err) {
        // 致命错误：上报失败状态
        reporter.ReportStatus(scopeItem, err, false)
    } else {
        // 可继续错误：上报成功状态，记录警告
        reporter.ReportStatus(scopeItem, err, true)
    }
}
```

### 3.3 错误包装

使用 `fmt.Errorf` 配合 `%w` 进行错误包装，保留原始错误链：

```go
// 正确：包装错误
if err != nil {
    return fmt.Errorf("查询用户[%s]失败: %w", username, err)
}

// 错误：丢失原始错误信息
if err != nil {
    return errors.New("查询用户失败")
}
```

### 3.4 错误返回原则

- 底层函数返回原始错误
- 中间层包装添加上下文
- 顶层决定如何处理（日志、上报、重试）

---

## 4. 单元测试规范

### 4.1 测试框架

使用 **Ginkgo v2 + Gomega + testify/mock** 组合：

```go
import (
    . "github.com/onsi/ginkgo/v2"
    "github.com/onsi/gomega"              // 注意：不使用 . 导入
    "github.com/stretchr/testify/mock"
)
```

**重要：gomega 包不使用 `.` 导入，使用 `gomega.` 前缀调用**

### 4.2 测试文件组织

每个包的测试文件结构：

```
package_name/
├── xxx.go                    # 源代码
├── suite_test.go            # 测试套件入口
├── mock_test.go             # Mock 实现（所有 Mock 集中）
├── xxx_test.go              # 具体测试用例
└── yyy_test.go              # 其他测试用例
```

### 4.3 suite_test.go 模板

```go
// Package xxx_test 包单元测试
package xxx_test

import (
    "testing"

    . "github.com/onsi/ginkgo/v2"
    "github.com/onsi/gomega"
)

func TestXxx(t *testing.T) {
    gomega.RegisterFailHandler(Fail)
    RunSpecs(t, "Xxx Suite")
}
```

### 4.4 Mock 实现规范

```go
// mock_test.go
package xxx_test

import (
    "github.com/stretchr/testify/mock"
    "your/project/types"
)

// MockDataLoader 数据加载器 Mock
type MockDataLoader struct {
    mock.Mock
}

func (m *MockDataLoader) LoadDept(code string) (types.Department, error) {
    args := m.Called(code)
    if args.Get(0) == nil {
        return types.Department{}, args.Error(1)
    }
    return args.Get(0).(types.Department), args.Error(1)
}
```

### 4.5 测试用例结构

使用 Describe/Context/It 三层结构：

```go
var _ = Describe("UserProcessor", func() {

    var (
        mockLoader *MockDataLoader
        processor  *UserProcessor
    )

    BeforeEach(func() {
        mockLoader = new(MockDataLoader)
        processor = NewUserProcessor(mockLoader)
    })

    AfterEach(func() {
        // 清理资源
    })

    Describe("Process", func() {
        Context("当用户存在时", func() {
            BeforeEach(func() {
                mockLoader.On("LoadUser", "user001").Return(testUser, nil)
            })

            It("应该成功处理", func() {
                err := processor.Process("user001")
                gomega.Expect(err).To(gomega.BeNil())
            })
        })

        Context("当用户不存在时", func() {
            BeforeEach(func() {
                mockLoader.On("LoadUser", "user001").Return(nil, gorm.ErrRecordNotFound)
            })

            It("应该返回错误", func() {
                err := processor.Process("user001")
                gomega.Expect(err).NotTo(gomega.BeNil())
            })
        })
    })
})
```

### 4.6 Mock 匹配器使用

```go
// 精确匹配
mockTarget.On("CreateUser", testUser).Return(nil)

// 任意参数
mockTarget.On("CreateUser", mock.Anything).Return(nil)

// 条件匹配
mockTarget.On("CreateUser", mock.MatchedBy(func(u User) bool {
    return u.Username == "user001"
})).Return(nil)

// 错误类型匹配 - 使用 mock.Anything 处理包装错误
mockReporter.On("ReportStatus", scopeItem, mock.Anything, true).Return(nil)
```

### 4.7 测试辅助函数

将测试辅助函数放在 mock_test.go 中：

```go
// createTestUser 创建测试用用户
func createTestUser(username, name, deptCode string) model.User {
    return model.User{
        Username:       username,
        FullName:       name,
        DepartmentCode: deptCode,
    }
}

// createTestDepartment 创建测试用部门
func createTestDepartment(code, name, parentCode string, level int) model.Department {
    return model.Department{
        Code:       code,
        Name:       name,
        ParentCode: parentCode,
        Level:      level,
    }
}
```

---

## 5. 日志规范

### 5.1 使用结构化日志

```go
import "go.uber.org/zap"

// 正确：结构化日志
logger.Info("sync: user created",
    zap.String("username", user.Username),
    zap.Int("dept_id", user.DeptID),
)

// 错误：字符串拼接
logger.Info(fmt.Sprintf("sync: user %s created in dept %d", user.Username, user.DeptID))
```

### 5.2 日志级别使用

| 级别 | 使用场景 |
|-----|---------|
| Debug | 调试信息，生产环境关闭 |
| Info | 关键业务节点、操作完成 |
| Warn | 可恢复的异常、降级处理 |
| Error | 错误但不影响主流程 |
| Fatal | 致命错误，程序退出 |

### 5.3 日志前缀规范

使用统一前缀标识模块：

```go
logger.Info("sync: starting department sync")
logger.Info("cache: warming up cache")
logger.Error("api: request failed")
```

---

## 6. 命名规范

### 6.1 文件命名

| 类型 | 命名规则 | 示例 |
|-----|---------|-----|
| 源文件 | 小写下划线 | `dept_syncer.go` |
| 测试文件 | `*_test.go` | `dept_syncer_test.go` |
| 接口文件 | `interfaces.go` 或 `types.go` | `types/interfaces.go` |

### 6.2 变量命名

| 类型 | 命名规则 | 示例 |
|-----|---------|-----|
| 局部变量 | 驼峰 | `userName`, `deptCode` |
| 包级变量 | 驼峰 | `defaultTimeout` |
| 常量 | 全大写下划线 | `MAX_RETRY_COUNT` |
| Mock 变量 | mock+类型 | `mockLoader`, `mockCache` |

### 6.3 函数命名

| 类型 | 命名规则 | 示例 |
|-----|---------|-----|
| 构造函数 | New+类型名 | `NewUserProcessor` |
| 获取方法 | Get+属性 | `GetUserByID` |
| 设置方法 | Set+属性 | `SetTimeout` |
| 判断方法 | Is/Has/Can | `IsValid`, `HasPermission` |
| 私有方法 | 小写开头 | `loadFromCache` |

---

## 7. 代码组织最佳实践

### 7.1 单一职责

每个结构体/函数只做一件事：

```go
// 正确：职责单一
type DeptSyncer struct { /* 只负责部门同步 */ }
type UserSyncer struct { /* 只负责用户同步 */ }

// 错误：职责混杂
type DataSyncer struct { /* 同时处理部门和用户 */ }
```

### 7.2 参数对象

超过 3 个参数时使用结构体：

```go
// 正确：使用配置结构体
type SyncOptions struct {
    Timeout     time.Duration
    RetryCount  int
    BatchSize   int
    EnableCache bool
}

func NewSyncer(opts SyncOptions) *Syncer { ... }

// 错误：参数过多
func NewSyncer(timeout time.Duration, retryCount, batchSize int, enableCache bool) *Syncer { ... }
```

### 7.3 返回值

- 成功返回值在前，error 在后
- 如有多个返回值，考虑使用结构体

```go
// 标准返回
func LoadUser(id int) (User, error)

// 复杂返回使用结构体
type SyncResult struct {
    SuccessCount int
    FailedCount  int
    FailedItems  []string
}

func SyncBatch(items []Item) (*SyncResult, error)
```

---

## 8. 注意事项

### 8.1 避免的做法

- 不要在接口中定义过多方法
- 不要在测试中使用 `time.Sleep`，使用 mock 或 channel
- 不要忽略错误返回值
- 不要在循环中使用 `defer`
- 不要过度使用反射

### 8.2 推荐的做法

- 优先使用组合而非继承
- 尽早返回，减少嵌套
- 使用 context 传递取消信号和超时
- 资源使用后及时释放
- 并发安全的数据结构使用 sync 包

---

## 9. 检查清单

开发完成后检查：

- [ ] 所有公开函数有注释
- [ ] 错误都被正确处理
- [ ] 单元测试覆盖主要逻辑
- [ ] Mock 代码集中在 mock_test.go
- [ ] 测试使用 suite_test.go 作为入口
- [ ] 日志使用结构化格式
- [ ] 依赖通过构造函数注入
- [ ] 接口定义在 types 包
