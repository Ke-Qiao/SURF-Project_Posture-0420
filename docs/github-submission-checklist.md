# GitHub 提交前检查清单

## 仓库设置

- 使用 private repository。
- 不 push 原始未审核人像数据。
- 不 push `.venv/`、`temp/`、ZIP 导出、模型权重或本地缓存。
- 保留老师提供的原始数据集在父目录，不移动、不重组。

## 代码检查

```bash
.venv/bin/python -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/private/tmp/surf-posture-pycache .venv/bin/python -m py_compile teacher_baseline.py main.py posture/*.py scripts/*.py web/*.py tests/*.py
node --check web/static/app.js
zsh -n start_web_demo.command
git diff --check
```

## Web 检查

- `/health` 返回 `week-02-mobile-camera-v1`。
- image、video、webcam、batch 四种模式仍可切换。
- Webcam 面板中 `Start computer camera` 和 `Start phone camera` 都显示出来。
- Webcam 采集缺少 collector、subject、label 或 reference 时会拒绝。
- Webcam 采集缺少 Head、Neck、Shoulder、Hip、Buttock、Knees、Ankle 任一项时会拒绝。
- `Set reference from current pose` 能生成绿色参考骨架。
- `Edit reference` 可以拖动 5 个参考点。
- 刷新页面后 reference 可以恢复。
- 满 10 张后 ZIP 可下载。
- ZIP 包含：
  - `original/`
  - `mediapipe/`
  - `manifest.csv`
  - `reference.json`
  - `summary.md`

## 数据检查

- `manifest.csv` 包含 collector、subject_id、true_label。
- `manifest.csv` 包含 profile_complete 和 missing_profile_parts。
- subject_id 不使用真实姓名。
- 图片必须先给老师审核。
- 只有审核通过的 clean side-view standing data 才上传 GitHub。

## 提交流程

```bash
git status --short
git add .
git commit -m "feat: prepare week 2 data collection platform"
```

本轮不 push。确认远端 private repo 地址和数据策略后再单独 push。
