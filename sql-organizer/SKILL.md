---
name: sql-organizer
description: SQL文件整理工具，用于规范化和重组织MySQL/MariaDB补丁SQL文件结构。适用于：整理混乱的SQL补丁文件、统一INSERT语句风格、按操作类型分组SQL语句。触发场景：用户需要整理SQL文件结构、规范化INSERT语句、或者提到"SQL整理"、"SQL规范"、"整理SQL文件"等。
---

# SQL文件整理工具

整理MySQL/MariaDB补丁SQL文件，使其结构清晰、风格统一。

## 文件结构规范

按照以下Section顺序组织SQL文件：

```
Section 1: 文件头
  - USE `database_name`
  - SET NAMES utf8
  - SET FOREIGN_KEY_CHECKS = 0

Section 2: 建表语句 (CREATE TABLE IF NOT EXISTS)
  - 按功能分组：部门、用户、终端、硬件信息等

Section 3: 表结构修改 (ALTER TABLE)
  - 按表名分组，同一表的修改集中在一起

Section 4: 索引创建 (CREATE INDEX IF NOT EXISTS)

Section 5: 数据操作 (INSERT/UPDATE/DELETE)
  - 子分组顺序：INSERT → UPDATE → DELETE
  - 每种操作内按表名分组

Section 6: 存储过程
  - 存储过程定义、调用、删除

Section 7: 文件尾
  - SET FOREIGN_KEY_CHECKS = 1
```

## INSERT语句规范

**判断标准**：根据INSERT语句中是否包含`id`字段，选择不同的插入方式。

### INSERT语句中包含id字段 → 使用 INSERT IGNORE

适用于INSERT语句中明确包含`id`字段的情况：

```sql
INSERT IGNORE INTO `database`.`table_name` (`id`, `field1`, `field2`, `created_at`)
VALUES (1, 'value1', 'value2', NOW());
```

**前提条件**：表必须有唯一键约束（通常是`id`主键），INSERT IGNORE才能防止重复插入。

如需添加唯一键：
```sql
ALTER TABLE `database`.`table_name` ADD UNIQUE INDEX IF NOT EXISTS `uk_field1_field2` (`field1`, `field2`);
```

### INSERT语句中不包含id字段 → 使用 INSERT ... WHERE NOT EXISTS

**重要**：遇到不包含`id`字段的INSERT语句时，必须向用户确认插入条件。

#### 处理流程

1. **识别INSERT语句**：分析INSERT语句，提取插入的字段列表
2. **向用户展示**：列出当前写入的字段，询问插入条件
3. **确认条件**：用户指定用于判断重复的字段（通常是业务唯一键）
4. **转换语句**：使用确认的条件生成幂等INSERT语句

#### 示例流程

原始语句：
```sql
INSERT INTO `udcp_uim`.`dcmc_sys_config` (`sys_key`, `sys_value`, `sys_group`, `remark`, `created_at`)
VALUES ('AssetAuthorizeStatus', 'off', 'assets', '资产认证开启状态', NOW());
```

向用户确认：
```
发现INSERT语句不包含id字段：
  表：udcp_uim.dcmc_sys_config
  写入字段：sys_key, sys_value, sys_group, remark, created_at
  
请确认：应该用哪个字段（或字段组合）判断数据是否已存在？
```

用户确认后（如使用`sys_key`判断），转换结果：
```sql
INSERT INTO `udcp_uim`.`dcmc_sys_config` (`sys_key`, `sys_value`, `sys_group`, `remark`, `created_at`)
SELECT 'AssetAuthorizeStatus', 'off', 'assets', '资产认证开启状态', NOW()
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM `udcp_uim`.`dcmc_sys_config` WHERE `sys_key`='AssetAuthorizeStatus'
);
```

## UPDATE语句规范

### 排版格式

```sql
-- ----------------------------
-- 表名：操作说明
-- ----------------------------
UPDATE `database`.`table_name`
SET
    `field1` = 'value1',
    `field2` = 'value2',
    `updated_at` = NOW()
WHERE `id` = 1;
```

### 分组规则

- 按表名分组，同一表的UPDATE语句集中在一起
- 每组前添加注释说明表名和操作目的
- 多个UPDATE语句操作同一表时，用空行分隔

### 示例

```sql
-- ----------------------------
-- dcmc_sys_config：更新系统配置
-- ----------------------------
UPDATE `udcp_uim`.`dcmc_sys_config`
SET `sys_value` = 'on', `updated_at` = NOW()
WHERE `sys_key` = 'AssetAuthorizeStatus';

UPDATE `udcp_uim`.`dcmc_sys_config`
SET `sys_value` = 'true', `updated_at` = NOW()
WHERE `sys_key` = 'domain_login';
```

## DELETE语句规范

### 排版格式

```sql
-- ----------------------------
-- 表名：删除条件说明
-- ----------------------------
DELETE FROM `database`.`table_name`
WHERE `field` = 'value';
```

### 安全提示

**重要**：DELETE语句存在数据安全风险，整理时必须：

1. **保留DELETE语句**：不要自动移除或转换
2. **确认条件完整性**：检查WHERE条件是否完整、是否有误
3. **向用户提示**：发现DELETE语句时，提醒用户确认删除条件
4. **添加安全注释**：在DELETE语句前标注风险提示

### 示例

```sql
-- ----------------------------
-- dcmc_temp_data：清理临时数据（请确认删除条件）
-- ----------------------------
DELETE FROM `udcp_uim`.`dcmc_temp_data`
WHERE `created_at` < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### 处理流程

1. **识别DELETE语句**：提取WHERE条件
2. **向用户展示**：
   ```
   发现DELETE语句：
     表：udcp_uim.dcmc_temp_data
     删除条件：created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
   
   请确认：删除条件是否正确？
   ```
3. **用户确认后保留**：添加注释说明

## 整理步骤

1. **分析现有结构**：读取SQL文件，识别所有操作类型
2. **提取建表语句**：收集所有 `CREATE TABLE`，按功能分组
3. **提取修改语句**：收集所有 `ALTER TABLE`，按表名分组
4. **提取索引语句**：收集所有 `CREATE INDEX`
5. **处理数据操作语句**：
   - **INSERT语句**：
     - 包含`id`字段：直接使用 INSERT IGNORE
     - 不包含`id`字段：向用户确认条件后转换
   - **UPDATE语句**：按表名分组，统一排版格式
   - **DELETE语句**：保留原语句，向用户确认删除条件
6. **重写文件**：按Section顺序重新组织所有语句

## 注意事项

- 移除 `DROP TABLE` 语句，改用 `CREATE TABLE IF NOT EXISTS`
- 移除 `TRUNCATE` 语句，保护已有数据
- 移除 `DELETE FROM` + `INSERT` 组合，改用幂等插入方式
- 统一使用 `NOW()` 代替具体时间戳
- 每个Section用清晰的注释分隔
- 同类型操作集中在一起，便于维护
- **必须与用户交互确认**不包含`id`的INSERT语句的插入条件
