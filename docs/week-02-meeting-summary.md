# Week 2 会议纪要：数据采集平台与侧视数据清洗

## 核心结论

本周会议的重点从“跑通 baseline 和做初步 demo”转向“采集干净、可审核、可训练的数据”。老师明确要求项目先收窄到侧视、全身、站姿，并用 good posture / bad posture 两类数据支持后续训练和评估。

## 各成员汇报

### Yuqi Jiao

- 已完成环境配置、模型训练和实时演示流程。
- 训练约 30 轮，验证集准确率记录为约 92.4%。
- 系统尝试检测肩部和臀部关键点。
- 当前摄像头稳定性和关键点可见性仍有问题。
- 后续设想是在不良姿势持续一段时间后加入声音提醒。

老师反馈：继续改进，但必须确认模型实际检测到肩、髋等项目需要的关键点，而不是只检测到脸部。

### Tianxu / L

- 在 Mac 上遇到摄像头权限或兼容问题。
- 已使用老师提供的 images 和 labels 进行训练，并保存 best model。

老师反馈：Mac 需要给 Terminal、PyCharm、VS Code 或 Python 摄像头权限。更重要的是，不能直接用未清洗的老师数据集训练。

### Jiapeng Xuan

- 已跑通 MediaPipe 和 OpenCV。
- 将原始像素差判断改成关节角度判断。
- 增加滑动窗口平滑以减少数值抖动。
- 尝试用随机森林基于角度判断姿势。

老师反馈：角度方法方向正确，但需要一个固定的 good posture 参考骨架。老师提出绿色 L 型参考骨架，与当前检测到的人体骨架对比角度差。

### Yilan Sun

- 使用 YOLOv8 pose 框架训练自定义关键点模型。
- 训练 50 轮。
- Loss 从 6.9 降到 0.6。
- mAP 从 0.17 提升到 0.85。

老师反馈：训练结果不错，但因为数据集还未清洗，结果不能直接代表最终项目性能。清洗侧视站姿数据后再训练会更有意义。

### Fengshuo Zhang

- 展示了本地 Web 平台。
- 支持 image、video、webcam、batch。
- 支持将数据初步分成 standing、sitting、incomplete。
- Webcam 支持实时检测、3 秒倒计时采集、10 张图导出 ZIP。

老师反馈：这个 Web 可以作为项目结构基础，也可以作为团队手机采集数据的平台。下一步要加入绿色参考骨架，并让团队成员用它采集侧视 good/bad 姿势数据。

## 老师明确的项目范围

- 当前只做 side view。
- 当前只做 full-body standing posture。
- 不要把动作 pose、走路、跳跃、瑜伽、正面图混入训练数据。
- 数据必须能看到 ear、shoulder、hip、knee、ankle。
- 系统最终应指出哪个部位有问题，而不只是输出整体 good/bad。

## 本周任务

- 每位成员采集 5-6 位朋友或家人的侧视照片。
- 每位 subject 尽量采集 good posture 和 bad posture 对照。
- 使用稳定支架，不要手持晃动。
- 先将原始数据链接发给老师审核。
- 老师确认合格后，再上传到 GitHub 共享仓库。
- Fengshuo 负责准备 GitHub 仓库和数据采集平台。

## 后续工作流

```text
Web 平台采集
→ 导出本地 ZIP
→ 发给老师审核
→ 清洗后上传 private GitHub
→ 用 clean dataset 训练
→ 输出 mAP / Precision / Recall / F1
→ 集成实时检测系统
```
