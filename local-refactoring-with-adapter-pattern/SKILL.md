---
name: local-refactoring-with-adapter-pattern
description: 使用 Adapter 模式对现有代码进行局部重构以提升可测试性。适用于代码直接调用外部包函数、业务逻辑与数据库强耦合、希望为现有业务函数编写单元测试或抽取逻辑供 RPC 复用的场景。当用户提到"局部重构"、"提升可测试性"、"Adapter 模式重构"、"mock 外部依赖"时使用。
---

# 局部重构：使用 Adapter 模式提高可测试性

当需要对现有代码进行局部重构以便于编写单元测试时，使用 Adapter 模式是一个有效的方法。

## 问题场景

以下情况适合使用此模式：

1. 代码直接调用外部包的函数（如 `model.GetUserByUserName()`）
2. 业务逻辑与数据库操作强耦合
3. 希望为现有业务函数编写单元测试，不想搭建完整的测试环境
4. 需要将业务逻辑抽取出来，提供给 RPC 服务或其他服务调用

## 重构步骤

### 步骤1：定义 Adapter 接口

创建 Adapter 接口，包含所有需要 mock 的函数：

```go
// adapter.go
type Adapter interface {
    // CheckPasswordRules 检查密码规则
    CheckPasswordRules(userReq request.UpdateUserPwdReq) (request.UpdateUserPwdReq, error)
    // GetUserByUserName 获取用户信息
    GetUserByUserName(userName string) (*model.User, error)
    // CheckProhibitUpdatePwd 检查是否禁止修改密码
    CheckProhibitUpdatePwd(u *model.User) (bool, error)
    // ... 更多方法
}
```

### 步骤2：实现 Adapter

创建 AdapterImpl，每个方法简单地委托调用原有函数：

```go
type AdapterImpl struct{}

func (a AdapterImpl) CheckPasswordRules(userReq request.UpdateUserPwdReq) (request.UpdateUserPwdReq, error) {
    return CheckPasswordRules(userReq)  // 委托调用
}

func (a AdapterImpl) GetUserByUserName(userName string) (*model.User, error) {
    user, err := GetUserByUserName(userName)
    return &user, err
}
```

### 步骤3：定义全局变量

```go
var globalRestartPassword Adapter = AdapterImpl{}
```

### 步骤4：修改业务函数

将直接调用改为通过 Adapter 调用：

```go
// 重构前
user, err := model.GetUserByUserName(clientReq.Username)

// 重构后
user, err := globalRestartPassword.GetUserByUserName(clientReq.Username)
```

### 步骤5：提供注入接口（可选）

```go
// SetEIAAuthChecker 设置 EIA 认证检查器（用于测试注入mock）
func SetEIAAuthChecker(checker EIAAuthChecker) {
    globalEIAAuthChecker = checker
}
```

## 测试策略

### 模式1：使用 Mock 测试业务函数

```go
// mock_test.go
import "github.com/stretchr/testify/mock"

type MockAdapter struct {
    mock.Mock
}

func (m *MockAdapter) GetUserByUserName(userName string) (*model.User, error) {
    args := m.Called(userName)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*model.User), args.Error(1)
}

// uim_client_new_test.go
var mockAdapter *MockAdapter
var origAdapter Adapter

BeforeEach(func() {
    mockAdapter = &MockAdapter{}
    origAdapter = globalRestartPassword
    globalRestartPassword = mockAdapter  // 注入 mock
})

AfterEach(func() {
    globalRestartPassword = origAdapter  // 还原
})

It("测试用例", func() {
    mockAdapter.On("GetUserByUserName", "testuser").
        Return(&model.User{ID: 100}, nil)

    code, msg := ClientModifyUserPassword(clientReq)

    Expect(code).To(Equal(ecode.OK))
})
```

### 模式2：使用 gomonkey 测试 Adapter 本身

```go
import gomonkey "github.com/agiledragon/gomonkey/v2"

It("mock 函数", func() {
    patches := gomonkey.ApplyFunc(CheckPasswordRules,
        func(req request.UpdateUserPwdReq) (request.UpdateUserPwdReq, error) {
            return req, nil
        })
    defer patches.Reset()

    result, err := adapter.CheckPasswordRules(userReq)
    Expect(err).NotTo(HaveOccurred())
})

It("mock 结构体方法", func() {
    patches := gomonkey.ApplyMethod(userModel, "UpdateUserPasswordNew",
        func(u *model.User, userID int, password string, hit bool) error {
            return nil
        })
    defer patches.Reset()

    err := adapter.UpdateUserPasswordNew(userModel, userReq, false)
    Expect(err).NotTo(HaveOccurred())
})
```

## 关键注意事项

### 1. 类型转换问题

当 mock 返回 `authx.AuthCode` 类型的接口方法时，确保 mock 正确返回类型：

```go
// 错误示例
func (m *MockAuthToken) Code() int {
    return args.Int(0)
}

// 正确示例
func (m *MockAuthToken) Code() authx.AuthCode {
    if args.Get(0) == nil {
        return 0  // 返回 AuthCode 的零值
    }
    return args.Get(0).(authx.AuthCode)
}
```

### 2. 接口方法完整性

确保 mock 实现了接口的所有方法，包括可能被遗漏的：

```go
// AuthToken 接口需要：
// - Code() AuthCode
// - ErrCode() string
// - Message() string
// - Token() string
// - ExpiresAt() time.Time
// - RefreshToken() string
// - PasswordStatus() PasswordStatus
// - TokenType() string
// - Success() bool
// - Get() map[string]interface{}
```

### 3. gomonkey 的限制

- 无法 mock 外部包的函数
- `ApplyFunc()` 用于 mock 包级别函数
- `ApplyMethod()` 用于 mock 结构体方法

### 4. 重试机制的测试

对于带重试逻辑的代码，测试时需要验证重试次数：

```go
It("更新用户密码重试后成功", func() {
    callCount := 0

    patches := gomonkey.ApplyMethod(userModel, "UpdateUserPasswordNew",
        func(u *model.User, userID int, password string, hit bool) error {
            callCount++
            if callCount < 2 {
                return errors.New("retry")
            }
            return nil
        })
    defer patches.Reset()

    err := adapter.UpdateUserPasswordNew(userModel, userReq, false)
    Expect(err).NotTo(HaveOccurred())
    Expect(callCount).To(Equal(2))  // 验证重试了2次
})
```

## 重构收益

1. **提高可测试性**：通过 Adapter 接口，可以轻松 mock 底层依赖
2. **降低耦合度**：业务逻辑不再直接依赖具体实现
3. **便于集成测试/端到端测试**：可以注入不同的 Adapter 实现
4. **代码复用**：可以将业务逻辑提供给 RPC 服务或其他服务调用

## 测试风格建议

- 使用 Ginkgo + gomega 作为 BDD 测试框架
- 使用 testify/mock 作为 mock 库
- 使用 gomonkey 进行函数和结构体方法的 mock
- 单测文件命名为 `*_test.go`
- Mock 统一放到 `mock_test.go` 中
