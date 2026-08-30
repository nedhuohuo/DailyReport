# Weekly Report Generation Mistakes - 2026-04-24

## What Went Wrong

1. **Used repository activity as report content**
   - The generated weekly report described which repositories changed instead of what work was completed.
   - Repository names, commit hashes, changed-file counts, and line deltas leaked into the human-facing weekly report.

2. **Ignored unregistered new repositories during analysis**
   - Newly detected repositories were only listed under `new_repos_detected`.
   - Their commits were not analyzed, so active work in `ModuleImInterview` and `IMInterviewModule` was omitted.

3. **Invented structure when requirement names were unknown**
   - The report tried to use repository names or empty headings as top-level work items.
   - Correct behavior: if requirement names cannot be confidently inferred, summarize task/function items directly.

4. **Overfit to Git metadata**
   - The report included commit IDs, file counts, and line deltas in `具体内容`.
   - Weekly reports should be written for humans: completed tasks, functions, status, next steps, and risks.

5. **Failed to aggregate many commits into themes**
   - `ModuleImInterview` had many related commits, but early output either missed them or risked listing them one by one.
   - Correct behavior: group commits into functional themes such as meeting-room capability, interview workflow, UI/interaction, and API/tooling.

## Root Causes

- The analysis pipeline treated configured repositories as the only source of reportable work.
- The renderer had no hard rule separating machine metrics from human report prose.
- The weekly template lacked a clear hierarchy: task/function first, Git details only as internal evidence.
- Tests validated shape and fields but not report-quality constraints.

## Rules Going Forward

1. Weekly report body must be task/function oriented.
2. Do not mention repository activity, commit hashes, file counts, or line deltas in the weekly report body.
3. Newly detected repositories must be analyzed for commits in the target period, while still being marked as newly detected metadata.
4. If requirement names are unknown, do not fabricate them; summarize concrete completed task items.
5. Multiple related commits must be grouped into a small number of work themes.
6. Git metadata may remain in frontmatter/JSON/debug output, but not in prose sections.

## Acceptance Checks

A generated weekly report should answer:

- What functions/tasks were completed this week?
- What is the status of each item?
- What follow-up is planned?
- Are there important newly detected modules to configure?

It should not primarily answer:

- Which repository changed?
- How many files changed?
- Which commit hash did it come from?
- How many insertions/deletions happened?

## Additional Issue: Interview Management Page Was Merged Away

### What Happened

The weekly report did not surface `面试管理页面建设与优化` as an independent work item. Related commits were scattered into broader buckets such as:

- `面试业务流程与管理功能开发`
- `面试相关界面与交互体验优化`

This hid a meaningful business-facing workstream: the interview management page.

### Evidence

Relevant commits included work on:

- 面试时间筛选功能和快速面试入口
- 面试列表时间过滤
- 快速面试创建逻辑
- 订单和客资内容区自定义 View 及数据模型
- 面试管理界面样式和图标资源
- 面试管理页面布局样式
- 面试简历操作栏自定义 View 及布局资源

### Root Cause

The grouping heuristic prioritized broad technical categories (`ui`, `layout`, `interview`) before preserving business surface areas. As a result, a coherent product page was split across generic buckets.

### Rule Added

When commits mention a user-facing page/screen/management surface, preserve that product surface as its own weekly report task before applying generic technical categories. For this project, `面试管理`, `面试列表`, `快速面试入口`, `订单/客资内容区`, and `简历操作栏` should group under `面试管理页面建设与优化` unless a clearer requirement name is available.


## Additional Issue: Diff Was Collected But Not Used

The weekly analysis ran with `--diff`, but the renderer still relied mainly on commit messages. This meant changed files such as `InterviewManageActivity`, `iminterview_activity_interview_manage.xml`, order/customer content views, and resume action views did not drive task grouping.

Rule: when diff data exists, changed file paths and code/layout semantics must drive weekly task grouping. Commit messages are only hints.

## Compounding Lesson: Write Many Facts, Then Merge Into Fewer Requirements

The weekly report started to look useful only after switching from commit-message summarization to a two-phase process:

1. **Expand from code diff**
   - Extract many concrete facts from changed paths, layouts, views, APIs, repositories, request/response models, adapters, dialogs, and resources.
   - At this stage, prefer over-collecting facts rather than prematurely summarizing.
   - Commit messages are hints; file paths and code semantics are stronger evidence.

2. **Compress into weekly-report items**
   - Merge facts into business-facing requirements, pages, or capabilities.
   - Keep independent product surfaces independent. Do not merge `面试管理页面` into generic `界面优化`.
   - Move low-value technical chores to `其他/支撑性调整`.

### Durable Workflow

For weekly reports, always use this pipeline:

```text
Git diff -> fact extraction -> detailed task list -> requirement/theme merge -> concise weekly report
```

### Quality Bar

A weekly report item is good when it explains a meaningful product/business capability, such as:

- 面试管理页面建设与优化
- 面试会议房间能力完善
- 面试邀请与分享链路完善
- 面试音视频与录制能力建设
- 面试基础接口与数据模型建设

A weak item is too technical or too small, such as:

- 代码格式化
- 新增资源引用
- 修改 1 个文件
- 某仓库有提交
- 移除脏数据（without clarifying what was cleaned）

### Review Checklist

Before accepting a generated weekly report, check:

- Does each main bullet map to a product/business capability?
- Are important pages/screens preserved as independent items?
- Are large items expanded into concrete sub-tasks?
- Are low-value chores moved to `其他`?
- Did the report avoid commit hashes, file counts, line deltas, and repository activity language?
