# 测试说明

## 测试文件

- `test_api.py` - API接口自动化测试
- `test_ai_recommender.py` - AI推荐功能测试
- `test_task_failure.py` - 任务失败情况测试

## 运行测试

### 1. 测试特定任务失败情况

```bash
# 测试任务 task_1770615448 的失败情况
python3 tests/test_task_failure.py
```

### 2. 运行所有API测试

```bash
python3 tests/test_api.py
```

### 3. 运行AI推荐测试

```bash
python3 tests/test_ai_recommender.py
```

## 测试任务失败情况

`test_task_failure.py` 包含以下测试用例：

1. **test_get_failed_task_details** - 获取失败任务详情
2. **test_get_failed_task_logs** - 获取失败任务日志
3. **test_get_failed_task_data** - 获取失败任务数据
4. **test_failed_task_recovery** - 测试失败任务恢复机制
5. **test_task_failure_scenarios** - 测试各种失败场景
6. **test_task_error_handling** - 测试错误处理

## 测试特定任务

测试文件会自动测试任务 `task_1770615448` 的失败情况，包括：

- 任务状态验证
- 错误日志检查
- 数据提取情况
- 失败原因分析

## 注意事项

1. 运行测试前确保后端服务已启动（`http://localhost:6000`）
2. 测试会查询数据库，确保数据库连接正常
3. 某些测试可能会创建新任务，注意清理
