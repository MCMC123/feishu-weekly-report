# 飞书每周海运单价播报

这个脚本会读取飞书在线表格中 `报价日期-` 开头的最新工作表的 `AB4` 单元格，并向飞书群机器人发送：

```text
当前最新海运单价为：（在线表格的取值）元/kg
```

## 1. 准备配置

不要把真实密钥写进代码。请把下面这些环境变量配置到运行脚本的机器上：

```powershell
$env:FEISHU_APP_ID="cli_xxxxxxxxxxxxxxxx"
$env:FEISHU_APP_SECRET="替换成新的 APP_SECRET"
$env:FEISHU_SPREADSHEET_TOKEN="ZWkQsuOo7h0zywtIqTqcug9enTc"
$env:FEISHU_SHEET_TITLE=""
$env:FEISHU_SHEET_TITLE_PREFIX="报价日期-"
$env:FEISHU_CELL="AB4"
$env:FEISHU_BOT_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
$env:FEISHU_BOT_SECRET="替换成群机器人签名 secret"
```

你之前已经在聊天里发过 `APP_SECRET` 和机器人签名，建议在飞书后台重新生成一次，再配置新的值。

## 2. 本地测试

```powershell
python .\feishu_weekly_report.py
```

如果成功，群里会收到：

```text
当前最新海运单价为：xxx元/kg
```

## 3. 云端部署：GitHub Actions

项目里已经包含云端定时文件：

```text
.github/workflows/feishu-weekly-report.yml
```

它会在北京时间每周一 09:00 自动执行。也可以在 GitHub 页面手动点击 `Run workflow` 立即测试。

### 操作步骤

1. 把这个目录里的文件上传到一个 GitHub 仓库。

2. 进入仓库：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

添加这些 Secrets：

```text
FEISHU_APP_ID
FEISHU_APP_SECRET
FEISHU_SPREADSHEET_TOKEN
FEISHU_SHEET_TITLE
FEISHU_SHEET_TITLE_PREFIX
FEISHU_CELL
FEISHU_BOT_WEBHOOK
FEISHU_BOT_SECRET
```

对应值：

```text
FEISHU_SPREADSHEET_TOKEN=ZWkQsuOo7h0zywtIqTqcug9enTc
FEISHU_SHEET_TITLE=
FEISHU_SHEET_TITLE_PREFIX=报价日期-
FEISHU_CELL=AB4
```

`FEISHU_SHEET_TITLE` 留空时，脚本会自动选择 `FEISHU_SHEET_TITLE_PREFIX` 开头的最后一个工作表。比如本周是 `报价日期-5月第3周`，下周新增 `报价日期-5月第4周` 后，会自动读取第 4 周。

`FEISHU_APP_SECRET` 和 `FEISHU_BOT_SECRET` 建议使用重置后的新值。

3. 进入仓库：

```text
Actions -> Feishu weekly sea freight report -> Run workflow
```

手动跑一次，确认飞书群收到：

```text
当前最新海运单价为：xxx元/kg
```

之后它会自动在每周一北京时间 09:00 运行。

## 4. 本地或服务器定时发送

### Windows 任务计划程序

打开“任务计划程序”，创建基本任务：

- 触发器：每周，星期一，09:00
- 操作：启动程序
- 程序：`python`
- 参数：`C:\Users\123\Documents\Codex\2026-05-18\new-chat\feishu_weekly_report.py`
- 起始于：`C:\Users\123\Documents\Codex\2026-05-18\new-chat`

环境变量需要配置成系统或用户环境变量，否则任务计划程序里可能读不到。

### Linux cron

服务器时区如果是北京时间：

```cron
0 9 * * 1 /usr/bin/python3 /path/to/feishu_weekly_report.py
```

服务器如果是 UTC，则北京时间周一 9:00 是 UTC 周一 1:00：

```cron
0 1 * * 1 /usr/bin/python3 /path/to/feishu_weekly_report.py
```

## 5. 飞书权限检查

自建应用需要能读取这份在线表格，并开通电子表格读取相关权限。表格本身也要授权给应用，否则脚本会拿到 token 但读不到单元格。
