# Response to the Four Reference-Line Challenges

> 中文说明：这份文档用于回复老师关于绿色 reference line / good posture skeleton 的 4 个 challenge。英文为主，方便直接给老师看；每节末尾附中文解释。

## Project Scope

The current implementation focuses on **side-view standing posture**. The platform uses MediaPipe Pose to detect the visible side of the body, then evaluates five key reference points:

- Ear
- Shoulder
- Hip
- Knee
- Ankle

The green line represents the expected **good posture reference line**. The red line represents the current body segment tilt compared with that reference.

当前范围：只做侧视站姿检测。系统检测 ear、shoulder、hip、knee、ankle 五个侧视关键点，用绿色线表示理想 good posture 参考线，用红线表示当前人体相对参考线的偏移。

## Challenge 1: Make sure the green reference always detects ear-to-ankle for any height and forms a straight line

### Current Solution

The platform creates a vertical green reference line dynamically for each image or video frame.

1. MediaPipe detects the visible side landmarks.
2. The system selects the active side of the body based on landmark visibility.
3. The green reference line is anchored using the body axis, not a fixed screen position.
4. The reference x-position is computed from the median x-coordinate of shoulder, hip, knee, and ankle.
5. The reference points are then created at the same y-levels as the detected ear, shoulder, hip, knee, and ankle.
6. Because all points are normalized image coordinates, the method works for different image sizes, camera distances, and subject heights.

This means the reference line is not a static drawing. It follows the detected body scale and location while staying vertically straight.

### Body Visibility Gate

Before scoring, the system checks whether the full side profile is visible:

- Head
- Neck
- Shoulder
- Hip
- Buttock
- Knees
- Ankle

If important parts are missing, the platform does not give a normal good/bad score. It asks the user to retake or review the image.

### Ear Landmark Stabilization

One practical issue is that MediaPipe can sometimes place the ear landmark slightly in front of the actual ear, especially with side-view faces, hair, or partial occlusion. To reduce false bad results, the current implementation stabilizes small ear drift only when:

- shoulder, hip, knee, and ankle are already close to the vertical reference line;
- only E-S is slightly over the threshold;
- the ear offset is small enough to be considered landmark noise.

Clear forward-head posture is still kept as bad.

中文：绿色参考线不是固定画在屏幕中间，而是根据当前人体的 shoulder、hip、knee、ankle 自动计算身体中轴，再在 ear、shoulder、hip、knee、ankle 的高度生成竖直参考点。这样不同身高、不同距离都可以对齐。同时系统会检查全身侧视是否完整可见。对于 MediaPipe 偶尔把耳朵点识别到脸前面的情况，系统只在身体其余部分已经很直、且耳朵偏差很小的时候做稳定化修正，避免误判。

## Challenge 2: Measure the degree between each body point and the reference straight-line points

### Current Solution

The platform measures four segment angles against the green reference line:

- E-S: ear to shoulder reference point
- S-H: shoulder to hip reference point
- H-K: hip to knee reference point
- K-A: knee to ankle reference point

For each segment, the angle is calculated between:

- the current detected upper body point;
- the next lower point on the vertical green reference line.

For example, E-S is calculated from the current ear point to the shoulder-height point on the green reference line.

The formula is:

```text
angle = atan2(abs(current_x - reference_x), abs(current_y - lower_reference_y))
```

Then the result is converted to degrees.

If the detected body point is perfectly aligned with the reference line, the angle is 0 degrees. If the point moves forward or backward away from the line, the angle increases.

中文：系统现在不是简单计算人体两个真实点之间的角度，而是计算“当前点”到“绿色参考线对应下一个点”的角度。例如 E-S 是当前 ear 到绿色参考线 shoulder 高度点的角度。理想状态为 0 度，偏离越大角度越大。

## Challenge 3: Measure the degree of tilt

### Current Solution

The degree of tilt is represented by the four reference-line segment angles:

| Segment | Meaning | Ideal Value | Current Threshold |
| --- | --- | --- | --- |
| E-S | Ear compared with shoulder reference | 0 deg | <= 10 deg |
| S-H | Shoulder compared with hip reference | 0 deg | <= 10 deg |
| H-K | Hip compared with knee reference | 0 deg | <= 10 deg |
| K-A | Knee compared with ankle reference | 0 deg | <= 10 deg |

The platform displays these tilt degrees in real time in image, video, webcam, and phone-camera modes. It also draws:

- green vertical reference line and reference points;
- red current tilt lines when posture is bad;
- green current tilt lines when posture is good.

The current threshold is 10 degrees, which matches the teacher's suggestion that small tolerance can be allowed but should not be too large.

中文：倾斜角用 E-S、S-H、H-K、K-A 四段角度表示。0 度代表完全对齐参考线。目前 good 的容许阈值是 10 度。网页会同步显示角度、红绿线和 good/bad 结果。

## Challenge 4: Accurately decide good or bad based on image or real-time video

### Current Decision Logic

The platform uses the same posture pipeline for:

- single image analysis;
- video analysis;
- webcam real-time stream;
- phone camera stream;
- batch dataset review.

The decision flow is:

1. Detect a person with MediaPipe Pose.
2. Reject front-view images because this project currently supports side-view only.
3. Check whether the required side-profile body parts are visible.
4. Build the green good-posture reference line.
5. Calculate E-S, S-H, H-K, and K-A tilt degrees.
6. If all four segment angles are within the threshold, classify as **Good**.
7. If any segment angle is above the threshold, classify as **Bad** and show the issue and advice.

### Current Rule

```text
Good posture:
  E-S <= 10 deg
  S-H <= 10 deg
  H-K <= 10 deg
  K-A <= 10 deg

Bad posture:
  any one of the four segment angles > 10 deg
```

### Evaluation Plan

For dataset review, the platform can compare the predicted label with the true label folder:

- good folder = true good posture
- bad folder = true bad posture

It can calculate:

- Accuracy
- Precision
- Recall
- F1 score
- Confusion matrix

mAP is not fully meaningful yet because we do not yet have ground-truth bounding boxes or keypoint annotations. Once the dataset has approved labels and keypoint/box ground truth, mAP can be added for model-based detection evaluation.

中文：现在 image、video、webcam、phone camera、batch review 都使用同一套 pipeline。系统先拒绝正面图，再检查侧视全身是否完整，然后根据四段角度判断。四段都小于等于 10 度就是 Good，有任意一段超过就是 Bad。平台已经可以对 good/bad 文件夹做 Precision、Recall、F1、confusion matrix。mAP 需要未来有真实框或关键点标注后再做。

## Current Limitations

The current system is still a rule-based baseline, not a trained model. Main limitations:

- MediaPipe landmarks can drift when the face, ear, knee, or ankle is partially hidden.
- Loose clothing may make shoulder, hip, and knee locations less reliable.
- Front-view or diagonal-view photos are rejected or may need manual review.
- Current thresholds are experience-based and should be tuned with the approved dataset.
- The system does not yet support manual correction of wrongly detected keypoints.

中文：当前还是 rule-based baseline，不是训练模型。最大问题是 MediaPipe 点位会受头发、衣服、遮挡、拍摄角度影响。之后需要用老师审核后的数据调阈值，并增加人工修正关键点功能。

## Next Improvements

Recommended next steps:

1. Add manual keypoint correction for dataset review.
2. Save corrected keypoints into the dataset export.
3. Tune the 10-degree threshold using approved good/bad photos.
4. Report Precision, Recall, and F1 after each dataset review.
5. Add mAP only after ground-truth boxes or keypoint labels are available.

中文：下一步建议做人工修正点位、保存修正后的标注、用审核后的数据调阈值，并正式输出 Precision、Recall、F1。mAP 等未来有真实关键点或检测框标注后再加入。
