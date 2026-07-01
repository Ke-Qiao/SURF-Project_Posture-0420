# SURF Posture Web Platform User Guide / SURF 姿态采集平台使用说明

This guide describes every visible option, input, and button in the local web
platform. It is written for Week 2 data collection and demo use.

本文档说明本地 Web 平台中每一个可见选项、输入框和按钮，适用于 Week 2 数据采集和演示。

---

## 1. Start The Platform / 启动平台

### Local computer only / 仅电脑本机访问

```bash
cd /Users/ke-qiao/Desktop/surf/posture-detection
./start_web_demo.command
```

Open the printed local URL, normally:

```text
http://127.0.0.1:5050
```

打开终端输出的本机地址，通常是：

```text
http://127.0.0.1:5050
```

### Phone collection on the same Wi-Fi / 同一 Wi-Fi 下手机采集

```bash
cd /Users/ke-qiao/Desktop/surf/posture-detection
./start_phone_demo.command
```

If the phone browser blocks `Start phone camera`, use HTTPS:

```bash
./start_phone_https_demo.command
```

如果手机浏览器拦截 `Start phone camera`，使用 HTTPS 启动：

```bash
./start_phone_https_demo.command
```

Equivalent command-line form / 等价命令行写法：

```bash
SURF_WEB_HOST=0.0.0.0 ./start_web_demo.command
```

The script prints a `Phone URL`, for example:

```text
http://192.168.x.x:5050
```

The HTTPS script prints a URL like:

```text
https://192.168.x.x:5443
```

Use this URL on a phone connected to the same Wi-Fi network.

脚本会显示 `Phone URL`，例如：

```text
http://192.168.x.x:5050
```

HTTPS 脚本会显示类似：

```text
https://192.168.x.x:5443
```

手机和电脑连接同一个 Wi-Fi 后，在手机浏览器中打开这个地址。

If the terminal says `Phone collection disabled`, the server is still local-only
and the phone cannot open it. Stop that terminal with `Ctrl+C`, then start
`start_phone_demo.command`.

如果终端显示 `Phone collection disabled`，说明服务仍然只监听本机，
手机无法打开。先在那个终端按 `Ctrl+C` 停止，再启动
`start_phone_demo.command`。

If the printed phone IP is not the Mac Wi-Fi IP, set it manually:

```bash
SURF_PHONE_IP=192.168.2.3 ./start_phone_demo.command
```

For HTTPS:

```bash
SURF_PHONE_IP=192.168.2.3 ./start_phone_https_demo.command
```

如果脚本打印出来的手机 IP 不是 Mac 的 Wi-Fi IP，可以手动指定：

```bash
SURF_PHONE_IP=192.168.2.3 ./start_phone_demo.command
```

HTTPS 模式：

```bash
SURF_PHONE_IP=192.168.2.3 ./start_phone_https_demo.command
```

For live phone camera collection, tap `Start phone camera` in the `Webcam`
panel. Most mobile browsers require HTTPS or another secure browser context
before allowing `getUserMedia()` camera access. If HTTP is blocked, use
`start_phone_https_demo.command`.

如果要直接调用手机摄像头，在手机页面的 `Webcam` 面板点击
`Start phone camera`。多数手机浏览器要求 HTTPS 或安全上下文才能允许
`getUserMedia()` 摄像头访问。如果 HTTP 被拦截，使用
`start_phone_https_demo.command`。

### HTTPS trust setup / HTTPS 信任设置

The HTTPS script creates local certificates in `temp/certs/`. They are local
only and ignored by Git. iPhone Safari usually needs the local CA to be trusted
before the page can use the camera.

HTTPS 脚本会在 `temp/certs/` 下生成本地证书。这些证书只保存在本机，
不会进入 Git。iPhone Safari 通常需要先信任本地 CA，网页才能调用摄像头。

English steps:

1. Run `./start_phone_https_demo.command`.
2. Read the printed `Local CA certificate for phone trust` path.
3. AirDrop that `.crt` file to the iPhone, or share it from Finder.
4. On iPhone, install the downloaded profile in Settings.
5. Go to Settings > General > About > Certificate Trust Settings.
6. Enable full trust for `SURF Posture Local CA`.
7. Open the printed HTTPS `Phone URL`.
8. Tap `Start phone camera` and allow camera permission.

中文步骤：

1. 运行 `./start_phone_https_demo.command`。
2. 查看终端打印的 `Local CA certificate for phone trust` 路径。
3. 把这个 `.crt` 文件通过 AirDrop 发到 iPhone，或从 Finder 分享到 iPhone。
4. 在 iPhone 设置中安装下载的描述文件。
5. 进入 设置 > 通用 > 关于本机 > 证书信任设置。
6. 打开 `SURF Posture Local CA` 的完全信任。
7. 打开终端打印的 HTTPS `Phone URL`。
8. 点击 `Start phone camera`，允许摄像头权限。

### HTTPS troubleshooting / HTTPS 排查

| Symptom | English fix | 中文处理 |
| --- | --- | --- |
| Phone cannot open the URL | Confirm the terminal says `Running on all addresses (0.0.0.0)` and use the printed `Phone URL`, not an old port. Make sure Mac and phone are on the same Wi-Fi. | 确认终端显示 `Running on all addresses (0.0.0.0)`，并使用本次终端打印的 `Phone URL`，不要用旧端口。确认 Mac 和手机在同一个 Wi-Fi。 |
| Printed IP is not the Mac Wi-Fi IP | Restart with `SURF_PHONE_IP=192.168.2.3 ./start_phone_https_demo.command`. | 用 `SURF_PHONE_IP=192.168.2.3 ./start_phone_https_demo.command` 重新启动。 |
| Browser says the page is not trusted | Install the printed `.crt` CA file and enable full trust for `SURF Posture Local CA`. Then close and reopen the browser tab. | 安装终端打印的 `.crt` CA 文件，并为 `SURF Posture Local CA` 打开完全信任，然后关闭并重新打开浏览器标签页。 |
| `Start phone camera` still fails | Check browser camera permission for the site. On iPhone Safari, use the `AA` / site settings menu or Settings > Safari > Camera. | 检查该网站的摄像头权限。iPhone Safari 可从地址栏 `AA` / 网站设置，或 设置 > Safari > 摄像头 中检查。 |
| Still blocked after trust setup | Restart the HTTPS script, reopen the HTTPS URL, and verify `/health` shows `"https": true`. Use `Image` or `Batch` upload as a fallback for the meeting if needed. | 重新启动 HTTPS 脚本，重新打开 HTTPS 地址，并确认 `/health` 显示 `"https": true`。如果会议前仍不稳定，先用 `Image` 或 `Batch` 上传作为备选。 |
| Mac firewall prompt appears | Allow incoming connections for Terminal/Python for this local demo. | 如果 Mac 防火墙弹窗，允许 Terminal/Python 的传入连接。 |

### Startup environment variables / 启动环境变量

| Option | English | 中文 |
| --- | --- | --- |
| `SURF_WEB_PORT` | Sets the web server port. Default is `5050`. | 设置端口，默认 `5050`。 |
| `SURF_WEB_HOST` | Sets the network host. Use `127.0.0.1` for local-only, `0.0.0.0` for phone/LAN access. | 设置访问范围。`127.0.0.1` 仅本机，`0.0.0.0` 支持手机局域网访问。 |
| `SURF_WEB_HTTPS=1` | Starts Flask with the generated local HTTPS certificate. | 使用生成的本地 HTTPS 证书启动 Flask。 |
| `SURF_PHONE_IP` | Overrides the phone URL IP printed by the startup script. Use this if auto-detection chooses a virtual network address. | 手动指定脚本打印的手机访问 IP。当自动识别到虚拟网卡地址时使用。 |
| `SURF_NO_OPEN=1` | Starts the server without opening a browser automatically. | 启动服务但不自动打开浏览器。 |

---

## 2. Page Layout / 页面布局

### Top bar / 顶部栏

| UI | English | 中文 |
| --- | --- | --- |
| `SURF Posture Demo` | Page title. | 页面标题。 |
| Status badge | Shows current app state, such as `Ready`, `Camera`, `Captured`, `Error`, or `ZIP ready`. | 显示当前状态，例如 `Ready`、`Camera`、`Captured`、`Error`、`ZIP ready`。 |

### Main mode tabs / 主模式切换

| Tab | English | 中文 |
| --- | --- | --- |
| `Webcam` | Live camera collection and detection. Main mode for Week 2 dataset collection. | 实时摄像头采集和检测，是 Week 2 数据采集主模式。 |
| `Image` | Upload one image, preview it, and analyze posture. | 上传单张图片，先预览，再分析姿态。 |
| `Video` | Upload one video, preview it, and analyze frames. | 上传一个视频，先预览，再逐帧分析。 |
| `Batch` | Analyze multiple images/videos or teacher image folders, then export a categorized ZIP. | 批量分析图片/视频或老师提供的数据集，并导出分类 ZIP。 |
| `Review` | Review labeled good/bad photos and export baseline metrics. | 审核已标注 good/bad 的照片，并导出 baseline 指标。 |

Switching tabs stops the current preview stream and resets the displayed metrics.

切换 tab 会停止当前预览流并重置指标显示。

---

## 3. Webcam Mode / Webcam 模式

This is the primary mode for collecting the 10 good posture and 10 bad posture
photos requested by the teacher.

这是采集老师要求的 10 张 good posture 和 10 张 bad posture 的主要模式。

### Required fields / 必填输入项

| Field | Required | English | 中文 |
| --- | --- | --- | --- |
| `Collector` | Yes | The person collecting the data. Use English name or pinyin, e.g. `fengshuo`. | 采集者。建议用英文名或拼音，例如 `fengshuo`。 |
| `Subject ID` | Yes | Anonymous subject identifier, e.g. `subject_001`. Do not use real names. | 匿名被拍摄者编号，例如 `subject_001`。不要使用真实姓名。 |
| `True label` | Yes | Manual label for the photo set. Choose `Good posture` or `Bad posture`. | 人工真实标签。选择 `Good posture` 或 `Bad posture`。 |
| `Notes` | No | Optional notes, such as lighting, clothing, or retake reason. | 可选备注，例如光线、衣服、重拍原因。 |

### True label options / True label 选项

| Option | English | 中文 |
| --- | --- | --- |
| `Choose good/bad` | Empty placeholder. Collection is blocked until a real label is selected. | 空占位符。未选择真实标签时不能采集。 |
| `Good posture` | Use when the subject is intentionally standing with corrected/healthy posture. | 被拍摄者保持较好、较正的站姿时选择。 |
| `Bad posture` | Use when the subject is intentionally showing poor posture, such as forward head or slouching. | 被拍摄者展示不良站姿，例如头前伸、含胸、前倾时选择。 |

### Webcam buttons / Webcam 按钮

| Button | English | 中文 |
| --- | --- | --- |
| `Start computer camera` | Starts the laptop/desktop camera through the Flask server and streams analyzed frames. | 通过 Flask 后端调用电脑摄像头并显示实时分析画面。 |
| `Start phone camera` | Starts the phone browser camera, uploads sampled frames to the server for analysis, and keeps the same metrics/footer display. Requires browser camera permission and usually HTTPS on phones. | 调用手机浏览器摄像头，将抽样帧上传到后端分析，并复用右侧指标和 footer。需要浏览器摄像头权限；手机通常还要求 HTTPS。 |
| `Stop` | Stops the active webcam stream and clears preview. | 停止摄像头流并清空预览。 |
| `Capture / Download` | If fewer than 10 captures exist, waits 3 seconds and captures one frame. Once 10 captures are ready, downloads the ZIP. | 未满 10 张时，倒计时 3 秒后采集一张；满 10 张后点击会下载 ZIP。 |
| `0/10 captured` status | Shows current capture count. Changes to `ready to download` when the ZIP is ready. | 显示当前已采集张数；ZIP 准备好后显示 ready to download。 |

### Phone camera workflow / 手机摄像头流程

1. Start the server with `./start_phone_demo.command`.
2. Open the printed `Phone URL` on the phone.
3. Fill `Collector`, `Subject ID`, `True label`, and optional `Notes`.
4. Tap `Start phone camera` and allow browser camera permission.
5. Wait until the preview shows skeleton/metrics, not just the raw camera feed.
6. Wait until the green ear-to-ankle reference line appears.
7. Confirm the profile checklist shows Head, Neck, Shoulder, Hip, Buttock,
   Knees, and Ankle as visible.
8. Tap `Capture / Download`; the app waits 3 seconds, analyzes the current
   phone frame, and saves it into the same 10-photo ZIP queue.
9. After 10 valid captures, tap `Download capture ZIP`.

中文流程：

1. 用 `./start_phone_demo.command` 启动服务。
2. 在手机浏览器打开终端显示的 `Phone URL`。
3. 填写 `Collector`、`Subject ID`、`True label` 和可选 `Notes`。
4. 点击 `Start phone camera`，允许浏览器摄像头权限。
5. 等页面出现骨骼和指标后再采集，不要只看原始相机画面。
6. 等绿色 ear-to-ankle reference line 出现。
7. 确认 Head、Neck、Shoulder、Hip、Buttock、Knees、Ankle 都显示 visible。
8. 点击 `Capture / Download`；平台倒计时 3 秒，分析当前手机帧，并保存到同一个 10 张 ZIP 队列。
9. 满 10 张后点击 `Download capture ZIP`。

### Capture requirements / 采集保存条件

The app blocks capture if any of the following is missing:

如果缺少以下任意条件，平台会拒绝保存：

- `Collector`
- `Subject ID`
- `True label`
- Fixed green reference line generated from the active detected pose
- Active webcam frame
- Complete side profile

The complete side profile checklist includes:

完整侧身轮廓 checklist 包括：

| Required part | MediaPipe proxy used by the app | 中文说明 |
| --- | --- | --- |
| `Head` | Ear landmark | 用耳朵关键点代理头部。 |
| `Neck` | Ear-shoulder segment | MediaPipe 没有 neck 点，用耳朵到肩膀这一段代理。 |
| `Shoulder` | Shoulder landmark | 肩膀关键点。 |
| `Hip` | Hip landmark | 髋部关键点。 |
| `Buttock` | Hip landmark proxy | MediaPipe 没有 buttock 点，用 hip 点代理。 |
| `Knees` | Knee landmark | 膝盖关键点。 |
| `Ankle` | Ankle landmark | 脚踝关键点。 |

If one part is missing, the right panel shows `missing`, and the footer shows
`Incomplete side profile`.

如果某个部位缺失，右侧面板会显示 `missing`，底部会显示 `Incomplete side profile`。

### Webcam ZIP output / Webcam ZIP 输出内容

After 10 valid captures, the downloaded ZIP contains:

采集满 10 张后，下载的 ZIP 包含：

```text
original/
mediapipe/
manifest.csv
reference.json
summary.md
```

| File/Folder | English | 中文 |
| --- | --- | --- |
| `original/` | Original webcam frames. | 原始摄像头图片。 |
| `mediapipe/` | Processed frames with MediaPipe skeleton, green reference line, and current body line. | 带 MediaPipe 骨架、绿色参考线和当前身体线的处理图。 |
| `manifest.csv` | Per-image metadata: collector, subject, label, prediction, score, visibility checklist, E-S/S-H/H-K/K-A segment angles, notes. | 每张图的元数据：采集者、subject、标签、预测、分数、部位可见性、E-S/S-H/H-K/K-A 分段角度、备注。 |
| `reference.json` | Green reference skeleton used during collection. Default source is `fixed-good-posture-v1`. | 采集时使用的绿色参考骨架。默认 source 是 `fixed-good-posture-v1`。 |
| `summary.md` | Human-readable export summary. | 人类可读的导出摘要。 |

---

## 4. Reference Skeleton Controls / 参考骨架控制

The green reference skeleton defaults to a fixed good side-view posture
baseline. It uses the current detected ear, shoulder, hip, knee, and ankle
heights, then places those reference points on a straight vertical line through
the ankle.

绿色参考骨架默认是固定 good side-view posture 基准。它使用当前检测到的 ear、
shoulder、hip、knee、ankle 的高度，再把这些 reference points 放到经过 ankle
的垂直直线上。

The main posture decision follows the teacher's reference-line rule:

主姿态判断遵循老师的 reference-line 规则：

| Segment | English | 中文 |
| --- | --- | --- |
| `E-S` | Ear to shoulder deviation from the green vertical reference. | ear 到 shoulder 这一段相对绿色垂直参考线的偏移角。 |
| `S-H` | Shoulder to hip deviation from the green vertical reference. | shoulder 到 hip 这一段相对绿色垂直参考线的偏移角。 |
| `H-K` | Hip to knee deviation from the green vertical reference. | hip 到 knee 这一段相对绿色垂直参考线的偏移角。 |
| `K-A` | Knee to ankle deviation from the green vertical reference. | knee 到 ankle 这一段相对绿色垂直参考线的偏移角。 |

Ideal good posture is `0 deg`. The current baseline accepts up to `10 deg` per
segment. If any segment is above the threshold, the result is bad.

理想 good posture 是 `0 deg`。当前 baseline 每一段最多允许 `10 deg`。任意一段超过
阈值，就判定为 bad。

| Control | English | 中文 |
| --- | --- | --- |
| `Use current pose as custom reference` | Optional debug/demo override. Uses the current detected side-view pose as a custom reference. | 可选调试/演示覆盖项。用当前检测到的侧视姿态作为自定义参考骨架。 |
| `Edit reference` | Enabled only after using a custom reference. Allows dragging ear, shoulder, hip, knee, ankle. | 仅在使用自定义参考骨架后可用，可拖动 ear、shoulder、hip、knee、ankle。 |
| `Hide reference` / `Show reference` | Toggles green reference skeleton visibility. | 显示或隐藏绿色参考骨架。 |
| `Reset to fixed good skeleton` | Returns to the default fixed good-posture skeleton and clears the custom reference. | 恢复默认固定 good-posture skeleton，并清除自定义参考。 |
| `Fixed good skeleton` | Status shown when the fixed reference is aligned to the current detected pose. | 固定参考骨架已根据当前检测姿态对齐。 |
| `Fixed reference waiting for pose` | Status shown before a valid pose is available. | 还没有有效姿态时显示。 |
| `Custom reference ready` | Status shown when a custom reference exists. | 已有自定义参考骨架时显示。 |

Only custom references are saved in browser `localStorage`. The fixed good
skeleton is the default and is regenerated from the current detected pose.

只有自定义参考骨架会保存在浏览器 `localStorage` 中。固定 good skeleton 是默认项，
会根据当前检测姿态重新生成。

---

## 5. Image Mode / Image 模式

Use this mode to analyze one still image.

用于分析单张图片。

| UI | English | 中文 |
| --- | --- | --- |
| `Choose image` | Opens file picker for one image. The image is previewed immediately after selection. | 打开文件选择器选择一张图片。选择后会立即预览。 |
| `Analyze image` | Sends the selected image to the backend for MediaPipe posture analysis. | 将图片发送到后端进行 MediaPipe 姿态分析。 |

Accepted file types are browser-supported image formats, such as `.jpg`,
`.jpeg`, `.png`, `.bmp`, and `.webp`.

支持常见图片格式，例如 `.jpg`、`.jpeg`、`.png`、`.bmp`、`.webp`。

---

## 6. Video Mode / Video 模式

Use this mode to analyze a video file frame by frame.

用于逐帧分析视频文件。

| UI | English | 中文 |
| --- | --- | --- |
| `Choose video` | Opens file picker for one video. The selected video is previewed immediately. | 打开文件选择器选择一个视频。选择后会立即预览。 |
| `Analyze video` | Uploads the video and streams analyzed frames back to the page. | 上传视频，并把分析后的帧流式显示回页面。 |

Supported extensions include `.mp4`, `.mov`, `.avi`, `.mkv`, and `.m4v`.

支持的视频扩展名包括 `.mp4`、`.mov`、`.avi`、`.mkv`、`.m4v`。

The right panel and footer update with the current analyzed frame, not a summary
of the whole video.

右侧面板和底部显示的是当前分析帧的结果，不是整段视频的汇总结果。

---

## 7. Batch Mode / Batch 模式

Use this mode to triage many files or teacher-provided images.

用于批量筛选文件或老师提供的数据集图片。

### Teacher image library / 老师图片库

| Option | English | 中文 |
| --- | --- | --- |
| `Do not include` | Do not include teacher images. Only uploaded files are analyzed. | 不包含老师图片，只分析上传文件。 |
| `All teacher images` | Analyze both teacher `train` and `val` image folders. | 分析老师数据集中的 `train` 和 `val` 图片。 |
| `Teacher train images` | Analyze only teacher `images/train`. | 只分析老师数据集 `images/train`。 |
| `Teacher val images` | Analyze only teacher `images/val`. | 只分析老师数据集 `images/val`。 |

### Batch file controls / 批量文件控件

| UI | English | 中文 |
| --- | --- | --- |
| `Choose images/videos` | Select multiple local image/video files. | 选择多个本地图片或视频。 |
| `Analyze batch` | Runs rule-based batch classification. | 执行基于规则的批量分类。 |
| `Download batch ZIP` | Appears after batch analysis is complete. Downloads categorized output. | 批量分析完成后出现，用于下载分类结果 ZIP。 |

Batch categories:

批量分类结果：

| Category | English | 中文 |
| --- | --- | --- |
| `standing` | Likely usable standing posture media. | 可能可用的站姿数据。 |
| `sitting` | Sitting media; usually not used for current standing-posture training. | 坐姿数据；当前站姿项目通常不使用。 |
| `incomplete` | No person, missing body parts, or unclear standing/sitting geometry. | 没有人、身体不完整，或几何关系不清楚。 |

---

## 8. Review Dataset Mode / Review Dataset 模式

Use this mode after collecting good/bad photo candidates. It compares the
manual true label against the current rule-based posture prediction and exports
review files.

在采集 good/bad 候选照片后使用这个模式。它会把人工真实标签和当前基于规则的姿态预测进行比较，并导出审核文件。

### Review controls / Review 控件

| UI | English | 中文 |
| --- | --- | --- |
| `Choose good photos` | Select photos whose true label is good posture. | 选择真实标签为 good posture 的照片。 |
| `Choose bad photos` | Select photos whose true label is bad posture. | 选择真实标签为 bad posture 的照片。 |
| `Review dataset` | Runs the baseline review and computes metrics. | 运行 baseline 审核并计算指标。 |
| `Download review ZIP` | Appears after review is complete. Downloads the review export. | 审核完成后出现，用于下载审核 ZIP。 |

The review ZIP contains:

Review ZIP 包含：

```text
original/good/
original/bad/
annotated/good/
annotated/bad/
review_report.csv
metrics.json
summary.md
```

Metric meaning:

指标含义：

| Metric | English | 中文 |
| --- | --- | --- |
| `Accuracy` | Correct predictions among evaluated good/bad rows. | 在已评估 good/bad 样本中的正确率。 |
| `Precision` | Bad-posture precision. Positive label is `bad`. | bad posture 的精确率；正类为 `bad`。 |
| `Recall` | Bad-posture recall. Positive label is `bad`. | bad posture 的召回率；正类为 `bad`。 |
| `F1` | Harmonic mean of Precision and Recall. | Precision 和 Recall 的调和平均数。 |
| `Needs Review` | Rows not used in binary metrics, such as no detection, front view, or incomplete profile. | 未进入二分类指标的样本，例如未检测到人、正面图、身体不完整。 |
| `mAP` | Not computed in this baseline review. It requires ground-truth boxes/keypoints and model confidence outputs. | 当前 baseline 审核不计算。它需要真实框/关键点标注和模型置信度输出。 |

Use `review_report.csv` to decide which photos can be sent to the teacher for
approval and which photos need retake or manual inspection.

使用 `review_report.csv` 决定哪些照片可以发给老师审核，哪些照片需要重拍或人工检查。

---

## 9. Viewer And Metrics / 预览区和指标区

### Viewer legend / 预览图例

| Legend | English | 中文 |
| --- | --- | --- |
| `Skeleton` | MediaPipe skeleton lines. | MediaPipe 骨架线。 |
| `Current line` | Current detected body segment line. It turns red for bad posture. | 当前检测到的身体分段线。bad posture 时显示为红色。 |
| `Reference` | Green vertical reference line and points. | 绿色垂直参考线和参考点。 |

### Right-side metrics / 右侧指标

| Field | English | 中文 |
| --- | --- | --- |
| `Posture` | `Good`, `Bad`, `No detection`, `Side view required`, or `Incomplete profile`. | 姿态结果：`Good`、`Bad`、`No detection`、`Side view required` 或 `Incomplete profile`。 |
| `Score` | Posture score from 0 to 100 when scoring is valid. | 有效评分时显示 0 到 100 的姿态分数。 |
| `Side` | Detected side, usually `left` or `right`; may show `front` when front view is detected. | 检测到的侧面，通常是 `left` 或 `right`；正面时可能显示 `front`。 |
| Angle cards | E-S, S-H, H-K, and K-A segment deviations from the green reference line. | 角度卡片：E-S、S-H、H-K、K-A 相对绿色参考线的分段偏移角。 |
| Profile checklist | Head, Neck, Shoulder, Hip, Buttock, Knees, Ankle visibility. | 部位可见性清单：Head、Neck、Shoulder、Hip、Buttock、Knees、Ankle。 |
| Reference diff cards | Difference between current segment angles and the reference value, normally 0 deg. | 当前分段角度与参考值的差值，通常参考值为 0 度。 |
| Advice cards | Corrective suggestions when posture is bad or capture is invalid. | 姿态不良或采集无效时的建议。 |

---

## 10. Download Evidence / 下载证据

| Button | English | 中文 |
| --- | --- | --- |
| `Download evidence` | Downloads a JSON record of the current mode, source, result, reference skeleton, and preview image. | 下载当前模式、来源、结果、参考骨架和预览图的 JSON 记录。 |

This is for meeting evidence only. It is not the same as the 10-photo webcam
dataset ZIP.

这个功能用于会议留档，不等同于 10 张照片的 webcam 数据集 ZIP。

---

## 11. Common Status And Errors / 常见状态和错误

| Message | English meaning | 中文含义 |
| --- | --- | --- |
| `Ready` | App is idle. | 平台空闲。 |
| `Camera` | Webcam stream is active. | 摄像头流正在运行。 |
| `No detection` | No person detected. | 未检测到人。 |
| `Side view required` | Front view or non-side view detected. | 检测到正面或非侧视，需要侧身。 |
| `Incomplete side profile` | A required body part is missing or low-confidence. | 必需身体部位缺失或置信度过低。 |
| `Missing profile parts: ...` | Capture blocked because the listed parts are missing. | 因列出的部位缺失而拒绝采集。 |
| `Fixed reference waiting for a detected side pose.` | Capture blocked until a valid detected side pose can align the fixed skeleton. | 还没有有效侧视检测姿态，固定参考骨架无法对齐。 |
| `ZIP ready` | Ten valid webcam captures are ready for download. | 已采集满 10 张，可以下载 ZIP。 |
| `Capture error` | Capture request failed; read the status text for detail. | 采集失败，查看状态文字获取原因。 |
| `Review done` | Dataset review completed and review ZIP is ready. | 数据集审核完成，review ZIP 已准备好。 |

---

## 12. Recommended Collection Workflow / 推荐采集流程

English:

1. Start LAN mode if collecting by phone.
2. Fill `Collector`, `Subject ID`, and `True label`.
3. Ask the subject to stand sideways against a clean background.
4. Start `Start computer camera` on a laptop/desktop, or `Start phone camera`
   on a phone browser.
5. Wait until the green ear-to-ankle reference line appears.
6. Confirm all profile checklist parts are visible.
7. Capture 10 photos for one label.
8. Download ZIP.
9. Use `Review` mode to check the collected good/bad candidates.
10. Send the ZIP or cloud link to the teacher for approval.

中文：

1. 如果用手机采集，启动局域网模式。
2. 填写 `Collector`、`Subject ID` 和 `True label`。
3. 让被拍摄者在干净背景前侧身站立。
4. 在电脑上点击 `Start computer camera`，或在手机浏览器上点击
   `Start phone camera`。
5. 等绿色 ear-to-ankle reference line 出现。
6. 确认所有 profile checklist 部位都显示 visible。
7. 针对一个标签采集 10 张照片。
8. 下载 ZIP。
9. 使用 `Review` 模式检查已采集的 good/bad 候选照片。
10. 将 ZIP 或云盘链接发给老师审核。
