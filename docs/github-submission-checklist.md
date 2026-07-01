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
zsh -n start_phone_demo.command
zsh -n start_phone_https_demo.command
git diff --check
```

## Web 检查

- `/health` 返回 `week-02-yolo-pose-labels-v1`。
- HTTPS 模式下 `/health` 返回 `"https": true`。
- image、video、webcam、batch、review 五种模式仍可切换。
- Webcam 面板中 `Start computer camera` 和 `Start phone camera` 都显示出来。
- Webcam 采集缺少 collector、subject 或 label 时会拒绝。
- Webcam 采集缺少 Head、Neck、Shoulder、Hip、Buttock、Knees、Ankle 任一项时会拒绝。
- 页面默认使用 `fixed-good-posture-v1` 绿色参考线。
- 右侧指标显示 E-S、S-H、H-K、K-A 四段 reference-line angle。
- 四段角度理想值为 0 deg，当前 good 阈值不超过 10 deg。
- `Use current pose as custom reference` 可以切换到自定义参考骨架。
- `Reset to fixed good skeleton` 可以恢复固定参考骨架。
- 满 10 张后 ZIP 可下载。
- ZIP 包含：
  - `original/`
  - `mediapipe/`
  - `pose_labels/`
  - `manifest.csv`
  - `reference.json`
  - `summary.md`
- Review 模式可以上传 good/bad 两组图片。
- Review 完成后显示 Accuracy、Precision、Recall、F1、Needs Review。
- Review ZIP 包含：
  - `original/good/`
  - `original/bad/`
  - `annotated/good/`
  - `annotated/bad/`
  - `pose_labels/good/`
  - `pose_labels/bad/`
  - `review_report.csv`
  - `metrics.json`
  - `summary.md`

## 数据检查

- `manifest.csv` 包含 collector、subject_id、true_label。
- `manifest.csv` 包含 profile_complete 和 missing_profile_parts。
- `review_report.csv` 包含 true_label、predicted_label、evaluation_status、correct。
- `pose_labels/` 中每张图片都有对应 YOLO-pose JSON，包含 ear、shoulder、hip、knee、ankle 五点像素坐标。
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
