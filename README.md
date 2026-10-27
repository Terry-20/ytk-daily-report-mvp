# 粤通卡日报网页 MVP（概念验证）

最小可运行项目：固定口令 → 上传固定文件名材料表 → 按公式出结果表 → 下载。
验证「网页闭环是否好用（含手机）」，**不含**原 skill 完整公式、历史台账等。

## 1. 环境准备

需要 Python 3.11+。

```bash
pip install -r requirements.txt
```

## 2. 设置口令

口令读环境变量 `MVP_PASSWORD`，缺省开发值 `unitoll`（请勿提交真实口令到仓库）。

```bash
# Linux / macOS
export MVP_PASSWORD='你的口令'

# Windows PowerShell
$env:MVP_PASSWORD='你的口令'
```

可选：设置 `MVP_SECRET`（Flask session 签名密钥），未设置时使用开发缺省值。

## 3. 启动

```bash
python app.py
```

监听 `127.0.0.1:5000`。浏览器打开 http://127.0.0.1:5000 ，输入口令进入工作台。

手机（iPhone Safari）：进站 → 逐文件选择 材料1.xlsx、材料2.xlsx → 开始生成 → 下载成品。

## 4. 用 fixtures 自测

本仓库提供假材料样例生成脚本（非真实业务数据）：

```bash
python scripts/make_fixtures.py
# 生成 fixtures/材料1.xlsx（产品数量=25）与 fixtures/材料2.xlsx（单价=4）
```

CLI 回归（无需 UI）：

```bash
python scripts/mvp_calc.py --material1 fixtures/材料1.xlsx --material2 fixtures/材料2.xlsx --out 结果.xlsx
# 预期输出：货款 = 100.0
```

Web 闭环自测（可用 curl）：

```bash
# 1) 错口令应被拒绝
curl -s -o /dev/null -w "%{http_code}\n" -X POST -d "password=wrong" http://127.0.0.1:5000/login
# 预期：200（仍停留在登录页，不会进入工作台）

# 2) 对口令登录并保存 cookie
curl -c cookies.txt -s -o /dev/null -X POST -d "password=unitoll" http://127.0.0.1:5000/login

# 3) 上传两个材料
curl -b cookies.txt -F "file=@fixtures/材料1.xlsx" http://127.0.0.1:5000/upload
curl -b cookies.txt -F "file=@fixtures/材料2.xlsx" http://127.0.0.1:5000/upload

# 4) 生成并下载，校验货款=100
curl -b cookies.txt -X POST http://127.0.0.1:5000/generate
curl -b cookies.txt -o 结果.xlsx http://127.0.0.1:5000/download
python -c "import openpyxl; print(openpyxl.load_workbook('结果.xlsx').active['A2'].value)"
# 预期：100.0
```

## 5. 业务规则（硬性）

- 登录页输口令；错误仅提示「口令错误」；**非持久登录**（关浏览器即失效）。
- 工作台上传恰好两个文件，文件名须为 `材料1.xlsx` 与 `材料2.xlsx`（扩展名 `.xlsx`，文件名大小写不敏感）。缺一 / 错名 / 多无关文件 → 中文报错，不生成。
- 计算：材料1 表头「产品数量」取第一个有效数字；材料2 表头「单价」取第一个有效数字；货款 = 产品数量 × 单价。
- 成品：生成 `结果.xlsx`，单 sheet，表头仅「货款」，下一行写数值。
- 按钮：开始生成 | 清空本次上传 | 下载成品（无成品时禁用）。清空会删除本次上传与成品。
- 会话隔离：每个登录用 session id 区分上传目录；退出或重新登录时清理旧上传。README 说明：**关浏览器后 session 失效需重新登录；实现上在 logout / 新 session 时清理旧上传**。

## 6. 验收对照（MVP）

- [x] 错误口令无法进入工作台；关闭页面后再开需重新输口令
- [x] 正确口令可上传 `材料1.xlsx` + `材料2.xlsx`；错名 / 缺一有中文报错
- [x] 点生成后下载 `结果.xlsx` 表头为「货款」，数值 = 产品数量 × 单价
- [x] 清空本次后上传列表为空，旧成品不可再下
- [x] 生成成功后页面仍开时可下载；关闭页面后再进，上传与成品已清
- [x] iPhone Safari 可完成：进站 → 选两文件 → 生成 → 下载
- [x] README 含口令设置 / 启动 / 假表自测
- [x] 仓库无真实口令、无粤通卡真实生产数据

## 7. 明确不做（Out）

原完整公式与材料角色识别、历史台账、截图 OCR、用户账号体系、制表日 / 港澳字段、
Cloudflare Worker 内跑 openpyxl。验证通过后再替换计算引擎与材料约定。
