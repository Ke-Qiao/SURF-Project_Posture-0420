# Week 2 数据采集规范

## 采集目标

采集可用于侧视站姿检测的数据。每张图片都应支持后续判断 good posture 或 bad posture，并能看到人体主要关键点。

## 拍摄要求

- 使用手机或相机，优先使用三脚架或稳定支撑。
- 拍摄对象侧身站立，身体从头到脚完整可见。
- 必须能看到 Head、Neck、Shoulder、Hip、Buttock、Knees、Ankle。
- 背景尽量干净，光线充足。
- 衣服应能看清肩、髋、膝、踝的大致轮廓。
- 相机保持水平，不要俯拍或仰拍过度。
- 每位 subject 尽量采集 good posture 和 bad posture 两类样本。

## 有效图片

- 侧视图。
- 全身站姿。
- 单人。
- Head、Neck、Shoulder、Hip、Buttock、Knees、Ankle 尽量可见。
- 姿势稳定，不在走路或运动中。

## 无效图片

- 正面图。
- 只有头部、半身或缺腿。
- 坐姿、走路、跑步、跳跃、瑜伽动作。
- 多人、宠物、遮挡严重或背景干扰很强。
- 关键点无法判断的模糊图片。

## Web 平台采集步骤

1. 启动 Web 平台。
2. 如需手机采集，双击或运行 `./start_phone_demo.command`。
   - 等价命令：`SURF_WEB_HOST=0.0.0.0 ./start_web_demo.command`。
   - 手机和电脑必须连接同一个 Wi-Fi。
   - 手机浏览器打开终端显示的 `Phone URL`。
   - 如果脚本打印的 IP 不是 Mac Wi-Fi IP，可以使用 `SURF_PHONE_IP=192.168.2.3 ./start_phone_demo.command` 手动指定。
   - 点击 `Start phone camera` 调用手机摄像头。
   - 注意：多数手机浏览器要求 HTTPS 或安全上下文才能允许实时摄像头。如果 HTTP 局域网 URL 被浏览器拒绝，使用 `./start_phone_https_demo.command`。
   - iPhone 上第一次使用 HTTPS 时，需要安装并完全信任终端打印的 `SURF Posture Local CA` 证书。
3. 在 Webcam 面板填写：
   - `Collector`
   - `Subject ID`
   - `True label`
   - `Notes` 可选
4. 让 subject 站成清楚侧视。
5. 点击 `Set reference from current pose` 设置绿色参考骨架。
6. 必要时点击 `Edit reference`，拖动 ear、shoulder、hip、knee、ankle。
7. 检查右侧 profile checklist：
   - Head
   - Neck
   - Shoulder
   - Hip
   - Buttock
   - Knees
   - Ankle
8. 如果任意部位显示 missing，重新调整相机或被拍摄者位置。
9. 点击 `Capture / Download`，每次等待 3 秒采集一张。
10. 满 10 张后下载 ZIP。

说明：MediaPipe 没有显式 neck 和 buttock 点。平台中 `Neck` 使用 ear-shoulder 段作为代理，`Buttock` 使用 hip 点作为代理。

## 审核流程

- 不要直接把未审核图片上传到 GitHub。
- 先把 ZIP 或云盘链接发给 Gomesh Nair 老师。
- 老师确认哪些图片有效后，再清理并上传 approved data。
- GitHub 仓库建议设为 private。

## 命名建议

- `collector`: 采集者英文名或拼音，例如 `fengshuo`
- `subject_id`: 不使用真实姓名，例如 `subject_001`
- `label`: `good` 或 `bad`

不要在文件名或 CSV 中写入真实姓名、手机号、学号等隐私信息。
