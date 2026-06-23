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

Equivalent command-line form / 等价命令行写法：

```bash
SURF_WEB_HOST=0.0.0.0 ./start_web_demo.command
```

The script prints a `Phone URL`, for example:

```text
http://192.168.x.x:5050
```

Use this URL on a phone connected to the same Wi-Fi network.

脚本会显示 `Phone URL`，例如：

```text
http://192.168.x.x:5050
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

如果脚本打印出来的手机 IP 不是 Mac 的 Wi-Fi IP，可以手动指定：

```bash
SURF_PHONE_IP=192.168.2.3 ./start_phone_demo.command
```

For live phone camera collection, tap `Start phone camera` in the `Webcam`
panel. Most mobile browsers require HTTPS or another secure browser context
before allowing `getUserMedia()` camera access. If the phone browser blocks
camera access on an HTTP LAN URL, use `Image` or `Batch` upload as the fallback,
or add an HTTPS launch path before team-wide collection.

如果要直接调用手机摄像头，在手机页面的 `Webcam` 面板点击
`Start phone camera`。多数手机浏览器要求 HTTPS 或安全上下文才能允许
`getUserMedia()` 摄像头访问。如果手机浏览器拒绝 HTTP 局域网摄像头，
先使用 `Image` 或 `Batch` 上传作为备选方案，后续再补 HTTPS 启动路径。

### Startup environment variables / 启动环境变量

| Option | English | 中文 |
| --- | --- | --- |
| `SURF_WEB_PORT` | Sets the web server port. Default is `5050`. | 设置端口，默认 `5050`。 |
| `SURF_WEB_HOST` | Sets the network host. Use `127.0.0.1` for local-only, `0.0.0.0` for phone/LAN access. | 设置访问范围。`127.0.0.1` 仅本机，`0.0.0.0` 支持手机局域网访问。 |
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
6. Set or adjust the green reference skeleton.
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
6. 设置或调整绿色参考骨架。
7. 确认 Head、Neck、Shoulder、Hip、Buttock、Knees、Ankle 都显示 visible。
8. 点击 `Capture / Download`；平台倒计时 3 秒，分析当前手机帧，并保存到同一个 10 张 ZIP 队列。
9. 满 10 张后点击 `Download capture ZIP`。

### Capture requirements / 采集保存条件

The app blocks capture if any of the following is missing:

如果缺少以下任意条件，平台会拒绝保存：

- `Collector`
- `Subject ID`
- `True label`
- Green reference skeleton
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
| `mediapipe/` | Processed frames with MediaPipe skeleton and green reference skeleton. | 带 MediaPipe 骨架和绿色参考骨架的处理图。 |
| `manifest.csv` | Per-image metadata: collector, subject, label, prediction, score, visibility checklist, angles, notes. | 每张图的元数据：采集者、subject、标签、预测、分数、部位可见性、角度、备注。 |
| `reference.json` | Green reference skeleton used during collection. | 采集时使用的绿色参考骨架。 |
| `summary.md` | Human-readable export summary. | 人类可读的导出摘要。 |

---

## 4. Reference Skeleton Controls / 参考骨架控制

The green reference skeleton represents a good side-view posture baseline. It is
used for visual comparison and angle difference display.

绿色参考骨架代表 good side-view posture 的参考基准，用于视觉对比和角度差显示。

| Control | English | 中文 |
| --- | --- | --- |
| `Set reference from current pose` | Uses the current detected side-view pose to create the green reference skeleton. Requires a valid detected side view. | 用当前检测到的侧视姿态生成绿色参考骨架。需要当前画面是有效侧视。 |
| `Edit reference` | Enables dragging the five reference points: ear, shoulder, hip, knee, ankle. Button changes to `Finish editing` while editing. | 开启拖拽编辑 5 个参考点：ear、shoulder、hip、knee、ankle。编辑时按钮变为 `Finish editing`。 |
| `Hide reference` / `Show reference` | Toggles green reference skeleton visibility. | 显示或隐藏绿色参考骨架。 |
| `Reset reference` | Deletes the saved reference skeleton from the browser. | 删除浏览器中保存的参考骨架。 |
| `Reference ready` | Status shown when a reference exists. | 已有参考骨架时显示。 |
| `Reference editing` | Status shown while editing points. | 正在编辑参考骨架时显示。 |
| `No reference set` | Status shown before a reference is created. | 尚未设置参考骨架时显示。 |

The reference skeleton is saved in browser `localStorage`, so it can remain
available after refreshing the page on the same browser.

参考骨架保存在浏览器 `localStorage` 中，所以同一浏览器刷新页面后仍可恢复。

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

## 8. Viewer And Metrics / 预览区和指标区

### Viewer legend / 预览图例

| Legend | English | 中文 |
| --- | --- | --- |
| `Skeleton` | MediaPipe skeleton lines. | MediaPipe 骨架线。 |
| `Side points` | Highlighted side-view posture points. | 高亮的侧视姿态关键点。 |
| `Reference` | Green reference skeleton. | 绿色参考骨架。 |

### Right-side metrics / 右侧指标

| Field | English | 中文 |
| --- | --- | --- |
| `Posture` | `Good`, `Bad`, `No detection`, `Side view required`, or `Incomplete profile`. | 姿态结果：`Good`、`Bad`、`No detection`、`Side view required` 或 `Incomplete profile`。 |
| `Score` | Posture score from 0 to 100 when scoring is valid. | 有效评分时显示 0 到 100 的姿态分数。 |
| `Side` | Detected side, usually `left` or `right`; may show `front` when front view is detected. | 检测到的侧面，通常是 `left` 或 `right`；正面时可能显示 `front`。 |
| Angle cards | Forward Head, Trunk Lean, and Knee angle values and deviations. | 角度卡片：头前伸、躯干倾斜、膝盖角度及偏差。 |
| Profile checklist | Head, Neck, Shoulder, Hip, Buttock, Knees, Ankle visibility. | 部位可见性清单：Head、Neck、Shoulder、Hip、Buttock、Knees、Ankle。 |
| Reference diff cards | Difference between current pose angles and green reference angles. | 当前姿态角度与绿色参考骨架角度的差值。 |
| Advice cards | Corrective suggestions when posture is bad or capture is invalid. | 姿态不良或采集无效时的建议。 |

---

## 9. Download Evidence / 下载证据

| Button | English | 中文 |
| --- | --- | --- |
| `Download evidence` | Downloads a JSON record of the current mode, source, result, reference skeleton, and preview image. | 下载当前模式、来源、结果、参考骨架和预览图的 JSON 记录。 |

This is for meeting evidence only. It is not the same as the 10-photo webcam
dataset ZIP.

这个功能用于会议留档，不等同于 10 张照片的 webcam 数据集 ZIP。

---

## 10. Common Status And Errors / 常见状态和错误

| Message | English meaning | 中文含义 |
| --- | --- | --- |
| `Ready` | App is idle. | 平台空闲。 |
| `Camera` | Webcam stream is active. | 摄像头流正在运行。 |
| `No detection` | No person detected. | 未检测到人。 |
| `Side view required` | Front view or non-side view detected. | 检测到正面或非侧视，需要侧身。 |
| `Incomplete side profile` | A required body part is missing or low-confidence. | 必需身体部位缺失或置信度过低。 |
| `Missing profile parts: ...` | Capture blocked because the listed parts are missing. | 因列出的部位缺失而拒绝采集。 |
| `Set a green reference skeleton first.` | Capture blocked until reference skeleton exists. | 未设置绿色参考骨架，不能采集。 |
| `ZIP ready` | Ten valid webcam captures are ready for download. | 已采集满 10 张，可以下载 ZIP。 |
| `Capture error` | Capture request failed; read the status text for detail. | 采集失败，查看状态文字获取原因。 |

---

## 11. Recommended Collection Workflow / 推荐采集流程

English:

1. Start LAN mode if collecting by phone.
2. Fill `Collector`, `Subject ID`, and `True label`.
3. Ask the subject to stand sideways against a clean background.
4. Start `Start computer camera` on a laptop/desktop, or `Start phone camera`
   on a phone browser.
5. Set the green reference from a good side-view pose.
6. Edit reference points if needed.
7. Confirm all profile checklist parts are visible.
8. Capture 10 photos for one label.
9. Download ZIP.
10. Send the ZIP or cloud link to the teacher for approval.

中文：

1. 如果用手机采集，启动局域网模式。
2. 填写 `Collector`、`Subject ID` 和 `True label`。
3. 让被拍摄者在干净背景前侧身站立。
4. 在电脑上点击 `Start computer camera`，或在手机浏览器上点击
   `Start phone camera`。
5. 用一张 good side-view 姿态设置绿色参考骨架。
6. 必要时手动拖动参考点微调。
7. 确认所有 profile checklist 部位都显示 visible。
8. 针对一个标签采集 10 张照片。
9. 下载 ZIP。
10. 将 ZIP 或云盘链接发给老师审核。
