# 修复 email-validator 缺失问题

## 🔍 问题原因

`pydantic` 的 `EmailStr` 类型需要 `email-validator` 包，但 `requirements.txt` 中没有包含它。

## ✅ 解决方法

### 方法一：使用自动修复脚本（推荐）

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
./fix_email_validator.sh
```

### 方法二：手动安装

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate

# 安装 email-validator
pip install email-validator>=2.0.0

# 或者安装 pydantic[email]（包含 email-validator）
pip install "pydantic[email]"
```

## ✅ 已更新 requirements.txt

我已经更新了 `requirements.txt`，添加了 `email-validator>=2.0.0`。

以后重新安装依赖时会自动包含它。

## 🚀 修复后操作

修复完成后，重新启动后端服务：

```bash
cd "/Users/sixsevensconsubine/Desktop/阅心/backend"
source venv/bin/activate
uvicorn main:app --reload
```

应该可以正常启动了！
