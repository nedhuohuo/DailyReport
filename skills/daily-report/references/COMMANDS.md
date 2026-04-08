# DailyReport 命令参考

## 命令总览

| 命令 | 功能 | 默认行为 | 参数 |
|------|------|---------|------|
| `/daily-report:dr_init` | 交互式初始化 | 配置工作区、扫描注册仓库、展示用户信息 | — |
| `/daily-report:dr_daily` | 生成日报 | 标准详细度 + diff 分析 | `--level=`、`--date=` |
| `/daily-report:dr_weekly` | 生成周报 | 粗略详细度 + 日报汇总 | `--level=`、`--diff` |
| `/daily-report:dr_monthly` | 生成月报 | 粗略详细度 + 周报日报汇总 | `--level=`、`--diff` |
| `/daily-report:dr_status` | 查看状态 | 展示配置和仓库信息 | — |

---

## /daily-report:dr_init

交互式初始化配置。首次使用时创建配置文件，后续使用时可新增仓库。

### 执行流程

1. **检查配置文件是否存在** `~/.config/dailyreport/config.json`
   - 不存在 → 首次初始化模式（收集全部配置）
   - 已存在 → 追加模式（仅扫描新增仓库）

2. **首次初始化时，交互式收集**：
   - 工作区根目录路径（必填）
   - Obsidian vault 目录路径（必填）
   - 默认详细度（可选，默认 standard）
   - 在写入配置前必须校验 vault 路径存在；若不存在，先询问是否创建

3. **扫描仓库**：
   ```bash
   SKILL_DIR="<skill 安装路径>"
   python3 "$SKILL_DIR/scripts/dr_scan.py" --workspace "<工作区路径>"
   ```
   追加模式使用 `--detect-new` 参数。

4. **展示扫描结果**：以表格展示发现的仓库及绑定的 Git 用户信息。用户确认后写入配置。

5. **创建输出目录**：
   ```
   <vault_dir>/<base_folder>/daily/
   <vault_dir>/<base_folder>/weekly/
   <vault_dir>/<base_folder>/monthly/
   ```

### 注意事项

- Git 用户信息为只读展示，修改需在仓库中执行 `git config` 后重新扫描
- 追加模式不会删除已注册的仓库，仅添加新发现的
- 如需删除已注册仓库，手动编辑 `config.json`

---

## /daily-report:dr_daily

生成指定日期的日报。

### 参数

| 参数 | 格式 | 默认值 | 说明 |
|------|------|--------|------|
| `--date` | YYYY-MM-DD | 今天 | 指定生成哪天的日报 |
| `--level` | brief/standard/detailed | standard | 详细度等级 |

### 执行流程

1. **加载配置**：读取 `config.json`，不存在则提示执行 `/daily-report:dr_init`
   - 若 `repositories` 为空，则回退到基于 `workspace_root` 的动态仓库发现
2. **调用分析脚本**（日报默认开启 diff）：
   ```bash
   python3 "$SKILL_DIR/scripts/dr_analyze.py" \
     --config ~/.config/dailyreport/config.json \
     --from <date> --to <date+1> --diff
   ```
3. **接收 JSON 分析数据**
4. **按详细度级别生成报告**：
   - `brief`：每仓库 2-3 行概要
   - `standard`：每仓库一段，关键变更说明
   - `detailed`：逐 commit 分析，关键代码变更引用
5. **写入文件**：`<vault>/DailyReport/daily/<YYYY-MM-DD>.md`
6. **展示结果**：输出文件路径和内容摘要

### 结果字段说明

日报 frontmatter 应包含以下结构化字段，便于 Dataview 统计：
- `repos_scanned`
- `repos_active`
- `commits_total`
- `authors`
- `groups`（存在分组信息时）

在 `standard` 和 `detailed` 模式下，无活动仓库应分为：
- 近 7 天活跃：显示仓库名和最后提交日期
- 90 天以上沉默：单独列出
- 其余无活动仓库：仅展示数量

### 输出示例路径

```
~/ObsidianVault/DailyReport/daily/2026-04-07.md
```

---

## /daily-report:dr_weekly

生成本周的周报。

### 参数

| 参数 | 格式 | 默认值 | 说明 |
|------|------|--------|------|
| `--level` | brief/standard/detailed | brief | 详细度等级 |
| `--diff` | flag | 不启用 | 启用 diff 分析补全 |

### 执行流程

1. **加载配置**
2. **计算本周范围**：ISO 周一 ~ 周日
3. **查找已有日报**：Glob 扫描 `daily/` 目录中该周日期的文件
4. **生成报告**：
   - **有日报 + 无 `--diff`**（默认路径）：读取日报内容汇总生成，**不调用 Python 脚本**，token 消耗最低
   - **有日报 + `--diff`**：读取日报 + 调用 `dr_analyze.py --diff` 获取一周 diff 数据补全
   - **无日报**：调用 `dr_analyze.py` 获取全量数据
5. **写入文件**：`<vault>/DailyReport/weekly/<YYYY>-W<WW>.md`

### 数据来源标注

生成的周报 frontmatter 中 `source` 字段标注数据来源：
- `daily-summary`：基于日报汇总
- `daily-summary+diff`：日报汇总 + diff 分析补全
- `diff-analysis`：直接 Git 分析

---

## /daily-report:dr_monthly

生成本月的月报。

### 参数

| 参数 | 格式 | 默认值 | 说明 |
|------|------|--------|------|
| `--level` | brief/standard/detailed | brief | 详细度等级 |
| `--diff` | flag | 不启用 | 启用 diff 统计分析 |

### 执行流程

1. **加载配置**
2. **计算本月范围**：月首 ~ 月末
3. **查找已有报告**：优先查找周报，其次日报
4. **生成报告**：
   - **有周报**（默认）：基于周报汇总。跨周部分补充日报
   - **无周报有日报**：基于日报汇总
   - **无任何报告**：调用 `dr_analyze.py` 获取全月数据
   - **`--diff` 启用时**：月报仅获取 `--stat-only` 统计，不获取完整 diff 内容
5. **写入文件**：`<vault>/DailyReport/monthly/<YYYY>-<MM>.md`

### 注意事项

- 月报默认基于周报+日报汇总，token 消耗极低
- `--diff` 模式仅获取统计，避免一个月的 diff 数据量过大

---

## /daily-report:dr_status

查看当前配置状态和已注册仓库信息。

### 执行流程

1. **读取配置文件**
2. **格式化展示**：
   - 工作区根目录
   - Obsidian vault 输出目录
   - 默认详细度
   - 已注册仓库列表（表格：名称、路径、Git 用户、注册时间）
   - 最近生成的报告文件（最近 5 个）
3. **配置不存在时**：提示用户执行 `/daily-report:dr_init`

---

## 脚本调用约定

所有 Python 脚本位于 Skill 目录下的 `scripts/` 子目录。

### 路径定位

```bash
SKILL_DIR="$(dirname "$(readlink -f ~/.agents/skills/daily-report/SKILL.md)" 2>/dev/null || dirname "$(readlink ~/.agents/skills/daily-report/SKILL.md)")"
```

### 脚本接口

| 脚本 | 输入 | 输出 | 用途 |
|------|------|------|------|
| `dr_scan.py` | `--workspace` | JSON (stdout) | 仓库扫描 |
| `dr_analyze.py` | `--config --from --to [--diff]` | JSON (stdout) | Git 分析 |

- 所有脚本通过命令行参数接收输入
- 正常输出为 JSON 格式到 stdout
- 错误信息输出到 stderr
- 非零退出码表示执行失败
