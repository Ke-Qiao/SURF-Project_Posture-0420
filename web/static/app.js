const modeButtons = Array.from(document.querySelectorAll(".mode-button"));
const panels = {
  webcam: document.querySelector("#webcamPanel"),
  image: document.querySelector("#imagePanel"),
  video: document.querySelector("#videoPanel"),
  batch: document.querySelector("#batchPanel"),
  review: document.querySelector("#reviewPanel"),
};

const labels = {
  webcam: "Webcam",
  image: "Image",
  video: "Video",
  batch: "Batch",
  review: "Review Dataset",
};

const statusBadge = document.querySelector("#statusBadge");
const modeLabel = document.querySelector("#modeLabel");
const preview = document.querySelector("#previewImage");
const previewVideo = document.querySelector("#previewVideo");
const referenceCanvas = document.querySelector("#referenceCanvas");
const emptyState = document.querySelector("#emptyState");
const postureValue = document.querySelector("#postureValue");
const scoreValue = document.querySelector("#scoreValue");
const sideValue = document.querySelector("#sideValue");
const angleList = document.querySelector("#angleList");
const profilePartList = document.querySelector("#profilePartList");
const referenceDeltaList = document.querySelector("#referenceDeltaList");
const adviceList = document.querySelector("#adviceList");
const footerPosture = document.querySelector("#footerPosture");
const footerMeta = document.querySelector("#footerMeta");
const footerAngles = document.querySelector("#footerAngles");
const footerAdvice = document.querySelector("#footerAdvice");
const imageInput = document.querySelector("#imageInput");
const videoInput = document.querySelector("#videoInput");
const batchInput = document.querySelector("#batchInput");
const reviewGoodInput = document.querySelector("#reviewGoodInput");
const reviewBadInput = document.querySelector("#reviewBadInput");
const teacherSource = document.querySelector("#teacherSource");
const analyzeBatchButton = document.querySelector("#analyzeBatch");
const reviewDatasetButton = document.querySelector("#reviewDataset");
const downloadBatch = document.querySelector("#downloadBatch");
const downloadReview = document.querySelector("#downloadReview");
const downloadEvidence = document.querySelector("#downloadEvidence");
const captureWebcamButton = document.querySelector("#captureWebcamSet");
const webcamCaptureStatus = document.querySelector("#webcamCaptureStatus");
const startPhoneCameraButton = document.querySelector("#startPhoneCamera");
const collectorInput = document.querySelector("#collectorInput");
const subjectInput = document.querySelector("#subjectInput");
const postureLabel = document.querySelector("#postureLabel");
const captureNotes = document.querySelector("#captureNotes");
const setReferenceButton = document.querySelector("#setReference");
const editReferenceButton = document.querySelector("#editReference");
const toggleReferenceButton = document.querySelector("#toggleReference");
const resetReferenceButton = document.querySelector("#resetReference");
const referenceStatus = document.querySelector("#referenceStatus");
const referenceCtx = referenceCanvas.getContext("2d");
const referencePointNames = ["ear", "shoulder", "hip", "knee", "ankle"];
const referenceSegmentAngleNames = [
  ["ear_shoulder", "E-S", "ear", "shoulder"],
  ["shoulder_hip", "S-H", "shoulder", "hip"],
  ["hip_knee", "H-K", "hip", "knee"],
  ["knee_ankle", "K-A", "knee", "ankle"],
];
const fixedReferenceSource = "fixed-good-posture-v1";
const customReferenceSource = "custom-current-pose";
const referenceStorageKey = "surfPostureReferenceSkeleton";
const referenceModes = {
  fixed: "fixed",
  custom: "custom",
};
let selectedMediaUrl = "";
let activeStreamController = null;
let activeMode = "webcam";
let latestResult = null;
let latestFrameDataUrl = "";
let latestSourceName = "";
let webcamCaptureDownloadUrl = "";
let referenceMode = referenceModes.fixed;
let customReferenceSkeleton = loadCustomReferenceSkeleton();
let referenceSkeleton = null;
let referenceVisible = true;
let referenceEditing = false;
let draggingReferencePoint = "";
let browserCameraStream = null;
let browserCameraTimer = null;
let browserCameraUploadPromise = null;
const browserCameraVideo = document.createElement("video");
const browserCameraCanvas = document.createElement("canvas");
const browserCameraIntervalMs = 1400;

browserCameraVideo.muted = true;
browserCameraVideo.playsInline = true;

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

document.querySelector("#startWebcam").addEventListener("click", startWebcam);
startPhoneCameraButton.addEventListener("click", startPhoneCamera);
document.querySelector("#stopWebcam").addEventListener("click", stopPreview);
document.querySelector("#analyzeImage").addEventListener("click", analyzeImage);
document.querySelector("#playVideo").addEventListener("click", analyzeVideo);
analyzeBatchButton.addEventListener("click", analyzeBatch);
reviewDatasetButton.addEventListener("click", reviewDataset);
captureWebcamButton.addEventListener("click", captureWebcamSet);
downloadEvidence.addEventListener("click", downloadCurrentEvidence);
imageInput.addEventListener("change", previewSelectedImage);
videoInput.addEventListener("change", previewSelectedVideo);
setReferenceButton.addEventListener("click", setReferenceFromCurrentPose);
editReferenceButton.addEventListener("click", toggleReferenceEditing);
toggleReferenceButton.addEventListener("click", toggleReferenceVisibility);
resetReferenceButton.addEventListener("click", resetReferenceSkeleton);
referenceCanvas.addEventListener("pointerdown", startReferenceDrag);
referenceCanvas.addEventListener("pointermove", dragReferencePoint);
referenceCanvas.addEventListener("pointerup", stopReferenceDrag);
referenceCanvas.addEventListener("pointercancel", stopReferenceDrag);
preview.addEventListener("load", drawReferenceOverlay);
previewVideo.addEventListener("loadedmetadata", drawReferenceOverlay);
window.addEventListener("resize", drawReferenceOverlay);
updateReferenceStatus();

function setMode(mode) {
  activeMode = mode;
  modeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  Object.entries(panels).forEach(([key, panel]) => {
    panel.classList.toggle("active", key === mode);
  });
  modeLabel.textContent = labels[mode];
  stopPreview();
  resetMetrics();
}

function startWebcam() {
  stopActiveStream();
  stopBrowserCameraStream();
  clearSelectedMediaUrl();
  latestSourceName = "computer-webcam";
  resetMetrics("Starting camera");
  setStatus("Camera", "good");
  activeStreamController = new AbortController();
  readFrameStream(`/stream/webcam-json?ts=${Date.now()}`, activeStreamController.signal, "Camera");
}

async function startPhoneCamera() {
  stopActiveStream();
  stopBrowserCameraStream();
  clearSelectedMediaUrl();
  latestSourceName = "phone-camera";
  resetMetrics("Starting phone camera");
  setStatus("Phone camera");

  if (!window.isSecureContext) {
    showError("Phone camera requires HTTPS or localhost. Use the Image/Batch upload path on HTTP LAN, or add HTTPS for live phone camera.");
    setStatus("HTTPS required", "bad");
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showError("This browser does not expose camera access to the page.");
    setStatus("Camera blocked", "bad");
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: {ideal: "environment"},
        width: {ideal: 1280},
        height: {ideal: 720},
      },
    });
    browserCameraStream = stream;
    browserCameraVideo.srcObject = stream;
    previewVideo.srcObject = stream;
    previewVideo.removeAttribute("src");
    previewVideo.muted = true;
    previewVideo.playsInline = true;
    previewVideo.classList.add("active");
    preview.classList.remove("active");
    emptyState.style.display = "none";
    await Promise.all([browserCameraVideo.play(), previewVideo.play()]);
    setStatus("Phone camera", "good");
    await analyzeBrowserCameraFrame(true);
    browserCameraTimer = window.setInterval(() => {
      analyzeBrowserCameraFrame(false);
    }, browserCameraIntervalMs);
  } catch (error) {
    stopBrowserCameraStream();
    setStatus("Camera blocked", "bad");
    showError(`Phone camera could not start. Browser permission or HTTPS may be blocking it. Detail: ${error.message}`);
  }
}

function stopPreview() {
  stopActiveStream();
  stopBrowserCameraStream();
  clearSelectedMediaUrl();
  latestFrameDataUrl = "";
  refreshEvidenceButton();
  preview.removeAttribute("src");
  previewVideo.removeAttribute("src");
  previewVideo.srcObject = null;
  previewVideo.pause();
  preview.classList.remove("active");
  previewVideo.classList.remove("active");
  emptyState.style.display = "block";
  drawReferenceOverlay();
  setStatus("Ready");
}

async function analyzeBrowserCameraFrame(force) {
  if (!browserCameraStream || browserCameraVideo.readyState < 2) {
    return null;
  }
  if (browserCameraUploadPromise) {
    return force ? browserCameraUploadPromise : null;
  }

  browserCameraUploadPromise = (async () => {
    const image = browserCameraFrameDataUrl();
    const response = await fetch("/api/browser-camera-frame", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({image}),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Phone camera analysis failed.");
    }
    showImage(payload.image);
    renderMetrics(payload.result);
    setStatus(payload.result.detected ? "Phone camera" : "No detection", payload.result.detected ? "good" : "bad");
    return payload;
  })();

  try {
    return await browserCameraUploadPromise;
  } catch (error) {
    setStatus("Camera error", "bad");
    showError(error.message);
    return null;
  } finally {
    browserCameraUploadPromise = null;
  }
}

function browserCameraFrameDataUrl() {
  const width = browserCameraVideo.videoWidth;
  const height = browserCameraVideo.videoHeight;
  if (!width || !height) {
    throw new Error("Phone camera frame is not ready.");
  }
  browserCameraCanvas.width = width;
  browserCameraCanvas.height = height;
  const ctx = browserCameraCanvas.getContext("2d");
  ctx.drawImage(browserCameraVideo, 0, 0, width, height);
  return browserCameraCanvas.toDataURL("image/jpeg", 0.88);
}

function stopBrowserCameraStream() {
  if (browserCameraTimer) {
    window.clearInterval(browserCameraTimer);
    browserCameraTimer = null;
  }
  if (browserCameraStream) {
    browserCameraStream.getTracks().forEach((track) => track.stop());
    browserCameraStream = null;
  }
  browserCameraVideo.pause();
  browserCameraVideo.srcObject = null;
  if (previewVideo.srcObject) {
    previewVideo.pause();
    previewVideo.srcObject = null;
  }
}

async function readFrameStream(url, signal, statusLabel) {
  try {
    const response = await fetch(url, { signal });
    if (!response.ok || !response.body) {
      throw new Error(`${statusLabel} stream could not start.`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) {
          continue;
        }
        const payload = JSON.parse(line);
        if (payload.error) {
          throw new Error(payload.error);
        }
        showImage(payload.image);
        renderMetrics(payload.result);
        setStatus(payload.result.detected ? statusLabel : "No detection", payload.result.detected ? "good" : "bad");
      }
    }
  } catch (error) {
    if (signal.aborted) {
      return;
    }
    stopPreview();
    setStatus("Error", "bad");
    showError(error.message);
  }
}

async function analyzeImage() {
  const file = imageInput.files[0];
  if (!file) {
    setStatus("Choose image", "bad");
    return;
  }

  const form = new FormData();
  form.append("file", file);
  setStatus("Analyzing");
  latestSourceName = file.name;

  try {
    const response = await fetch("/api/analyze-image", {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Image analysis failed.");
    }
    clearSelectedMediaUrl();
    showImage(payload.image);
    renderMetrics(payload.result);
    setStatus(payload.result.detected ? "Done" : "No detection", payload.result.detected ? "good" : "bad");
  } catch (error) {
    stopPreview();
    setStatus("Error", "bad");
    showError(error.message);
  }
}

async function analyzeVideo() {
  const file = videoInput.files[0];
  if (!file) {
    setStatus("Choose video", "bad");
    return;
  }

  const form = new FormData();
  form.append("file", file);
  setStatus("Loading");
  latestSourceName = file.name;

  try {
    const response = await fetch("/api/load-video", {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Video analysis failed.");
    }
    clearSelectedMediaUrl();
    resetMetrics("Video overlay");
    setStatus("Video", "good");
    activeStreamController = new AbortController();
    const streamUrl = payload.json_stream_url || payload.stream_url.replace("/stream/video/", "/stream/video-json/");
    readFrameStream(`${streamUrl}?ts=${Date.now()}`, activeStreamController.signal, "Video");
  } catch (error) {
    stopPreview();
    setStatus("Error", "bad");
    showError(error.message);
  }
}

function previewSelectedImage() {
  const file = imageInput.files[0];
  if (!file) {
    return;
  }
  clearSelectedMediaUrl();
  selectedMediaUrl = URL.createObjectURL(file);
  latestSourceName = file.name;
  showImage(selectedMediaUrl);
  resetMetrics("Image selected");
  setStatus("Selected", "good");
}

function previewSelectedVideo() {
  const file = videoInput.files[0];
  if (!file) {
    return;
  }
  clearSelectedMediaUrl();
  selectedMediaUrl = URL.createObjectURL(file);
  latestSourceName = file.name;
  showVideo(selectedMediaUrl);
  resetMetrics("Video selected");
  setStatus("Selected", "good");
}

function showImage(url) {
  preview.src = url;
  if (url.startsWith("data:image/")) {
    latestFrameDataUrl = url;
    refreshEvidenceButton();
  }
  preview.classList.add("active");
  if (!browserCameraStream) {
    previewVideo.pause();
    previewVideo.removeAttribute("src");
    previewVideo.srcObject = null;
  }
  previewVideo.classList.remove("active");
  emptyState.style.display = "none";
  requestAnimationFrame(drawReferenceOverlay);
}

function showVideo(url) {
  latestFrameDataUrl = "";
  refreshEvidenceButton();
  preview.removeAttribute("src");
  preview.classList.remove("active");
  previewVideo.srcObject = null;
  previewVideo.src = url;
  previewVideo.classList.add("active");
  emptyState.style.display = "none";
  requestAnimationFrame(drawReferenceOverlay);
}

function clearSelectedMediaUrl() {
  if (selectedMediaUrl) {
    URL.revokeObjectURL(selectedMediaUrl);
    selectedMediaUrl = "";
  }
}

function setStatus(text, kind = "") {
  statusBadge.textContent = text;
  statusBadge.classList.toggle("good", kind === "good");
  statusBadge.classList.toggle("bad", kind === "bad");
}

function resetMetrics(message = "") {
  latestResult = null;
  syncActiveReference();
  latestFrameDataUrl = "";
  refreshEvidenceButton();
  resetBatchDownload();
  postureValue.classList.remove("error-text");
  postureValue.textContent = message || "-";
  scoreValue.textContent = "-";
  sideValue.textContent = "-";
  angleList.innerHTML = "";
  profilePartList.innerHTML = "";
  referenceDeltaList.innerHTML = "";
  adviceList.innerHTML = "";
  footerPosture.className = "";
  footerPosture.textContent = message || "Waiting for input";
  footerMeta.textContent = "Score - / Side -";
  footerAngles.innerHTML = "";
  footerAdvice.textContent = "";
}

function showError(message) {
  latestResult = null;
  syncActiveReference();
  refreshEvidenceButton();
  resetBatchDownload();
  postureValue.textContent = "Error";
  postureValue.classList.add("error-text");
  scoreValue.textContent = "-";
  sideValue.textContent = "-";
  angleList.innerHTML = "";
  profilePartList.innerHTML = "";
  referenceDeltaList.innerHTML = "";
  adviceList.innerHTML = "";
  footerPosture.textContent = "Error";
  footerPosture.className = "error-text";
  footerMeta.textContent = "Score - / Side -";
  footerAngles.innerHTML = "";
  footerAdvice.textContent = message;

  const item = document.createElement("div");
  item.className = "advice-item error-item";
  item.textContent = message;
  adviceList.appendChild(item);
}

async function analyzeBatch() {
  const files = Array.from(batchInput.files || []);
  const source = teacherSource.value;
  if (!source && files.length === 0) {
    setStatus("Choose batch", "bad");
    return;
  }

  stopActiveStream();
  clearSelectedMediaUrl();
  preview.removeAttribute("src");
  previewVideo.removeAttribute("src");
  preview.classList.remove("active");
  previewVideo.classList.remove("active");
  emptyState.style.display = "block";
  resetMetrics("Processing batch");
  setStatus("Batch running");

  const form = new FormData();
  form.append("teacher_source", source);
  files.forEach((file) => form.append("files", file));

  try {
    const response = await fetch("/api/batch-analyze", {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Batch analysis failed.");
    }
    renderBatchSummary(payload);
    setStatus("Batch done", "good");
  } catch (error) {
    setStatus("Error", "bad");
    showError(error.message);
  }
}

async function reviewDataset() {
  const goodFiles = Array.from(reviewGoodInput.files || []);
  const badFiles = Array.from(reviewBadInput.files || []);
  if (goodFiles.length === 0 && badFiles.length === 0) {
    setStatus("Choose review", "bad");
    return;
  }

  stopActiveStream();
  clearSelectedMediaUrl();
  preview.removeAttribute("src");
  previewVideo.removeAttribute("src");
  preview.classList.remove("active");
  previewVideo.classList.remove("active");
  emptyState.style.display = "block";
  resetMetrics("Reviewing dataset");
  setStatus("Review running");

  const form = new FormData();
  goodFiles.forEach((file) => form.append("good_files", file));
  badFiles.forEach((file) => form.append("bad_files", file));

  try {
    const response = await fetch("/api/review-dataset", {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Dataset review failed.");
    }
    renderReviewSummary(payload);
    setStatus("Review done", "good");
  } catch (error) {
    setStatus("Error", "bad");
    showError(error.message);
  }
}

async function captureWebcamSet() {
  if (webcamCaptureDownloadUrl) {
    window.location.href = webcamCaptureDownloadUrl;
    setTimeout(resetWebcamCaptureSet, 600);
    return;
  }

  let metadata = collectionMetadata();
  if (!metadata.ok) {
    setStatus("Missing fields", "bad");
    webcamCaptureStatus.textContent = metadata.error;
    return;
  }

  captureWebcamButton.disabled = true;
  try {
    for (let remaining = 3; remaining > 0; remaining -= 1) {
      webcamCaptureStatus.textContent = `Capturing in ${remaining}s`;
      setStatus(`Capture ${remaining}s`);
      await delay(1000);
    }
    if (browserCameraStream) {
      const payload = await analyzeBrowserCameraFrame(true);
      if (!payload) {
        throw new Error("Phone camera frame is not ready for capture.");
      }
      metadata = collectionMetadata();
      if (!metadata.ok) {
        throw new Error(metadata.error);
      }
    }

    const response = await fetch("/api/webcam-capture", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(metadata.payload),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Webcam capture failed.");
    }

    updateWebcamCaptureUi(payload);
    if (payload.ready) {
      setStatus("ZIP ready", "good");
    } else {
      setStatus("Captured", "good");
    }
  } catch (error) {
    setStatus("Capture error", "bad");
    webcamCaptureStatus.textContent = error.message;
  } finally {
    captureWebcamButton.disabled = false;
  }
}

function renderMetrics(result) {
  const advice = result.advice || [];
  const angles = result.angles || [];
  const segmentAngles = result.segment_angles || [];
  latestResult = result;
  syncActiveReference();
  refreshEvidenceButton();
  drawReferenceOverlay();

  postureValue.classList.remove("error-text");
  postureValue.textContent = result.posture || "-";
  scoreValue.textContent = result.detected && typeof result.score === "number" ? `${result.score}/100` : "-";
  sideValue.textContent = result.side || "-";
  angleList.innerHTML = "";
  profilePartList.innerHTML = "";
  referenceDeltaList.innerHTML = "";
  adviceList.innerHTML = "";
  footerAngles.innerHTML = "";
  footerAdvice.textContent = "";

  if (!result.detected) {
    footerPosture.textContent = "No detection";
    footerPosture.className = "bad";
    footerMeta.textContent = "Score - / Side -";
    renderProfileParts(result);
    renderReferenceDiffs(result);
    return;
  }

  if (result.view_valid === false) {
    postureValue.textContent = result.posture || "Side view required";
    scoreValue.textContent = "-";
    sideValue.textContent = result.view || "-";
    footerPosture.textContent = result.posture || "Side view required";
    footerPosture.className = "bad";
    footerMeta.textContent = result.message || "Turn sideways before scoring";
    footerAdvice.textContent = advice.slice(0, 2).join(" | ");
    advice.forEach((adviceText) => {
      const item = document.createElement("div");
      item.className = "advice-item";
      item.textContent = adviceText;
      adviceList.appendChild(item);
    });
    renderProfileParts(result);
    renderReferenceDiffs(result);
    return;
  }

  if (result.profile_complete === false) {
    postureValue.textContent = "Incomplete profile";
    scoreValue.textContent = "-";
    sideValue.textContent = result.side || "-";
    footerPosture.textContent = "Incomplete side profile";
    footerPosture.className = "bad";
    footerMeta.textContent = `Missing: ${missingProfileText(result)}`;
    footerAdvice.textContent = "Retake with the full side profile visible.";
    renderProfileParts(result);
    renderReferenceDiffs(result);
    return;
  }

  footerPosture.textContent = result.overall_good ? "Good Posture" : "Bad Posture";
  footerPosture.className = result.overall_good ? "good" : "bad";
  footerMeta.textContent = `Score ${result.score}/100 / Side ${result.side || "-"}`;

  segmentAngles.forEach((angle) => {
    const item = document.createElement("div");
    item.className = `angle-item ${angle.is_good ? "good" : "bad"}`;
    item.innerHTML = `
      <div class="angle-title">
        <span>${angle.label}</span>
        <span>${angle.angle} deg</span>
      </div>
      <div class="angle-detail">${angle.start}-${angle.end} vs reference / threshold ${angle.threshold} deg</div>
    `;
    angleList.appendChild(item);

    const footerItem = document.createElement("span");
    footerItem.className = `footer-angle ${angle.is_good ? "good" : "bad"}`;
    footerItem.textContent = `${angle.label}: ${angle.angle} deg`;
    footerAngles.appendChild(footerItem);
  });

  if (!segmentAngles.length) {
    angles.forEach((angle) => {
      const item = document.createElement("div");
      item.className = `angle-item ${angle.is_good ? "good" : "bad"}`;
      item.innerHTML = `
        <div class="angle-title">
          <span>${angle.label}</span>
          <span>${angle.angle} deg</span>
        </div>
        <div class="angle-detail">Deviation ${angle.deviation} deg / threshold ${angle.threshold} deg</div>
      `;
      angleList.appendChild(item);
    });
  }

  renderProfileParts(result);
  renderReferenceDiffs(result);

  footerAdvice.textContent = advice.slice(0, 2).join(" | ");

  advice.forEach((adviceText) => {
    const item = document.createElement("div");
    item.className = "advice-item";
    item.textContent = adviceText;
    adviceList.appendChild(item);
  });
}

function renderBatchSummary(payload) {
  const summary = payload.summary || {};
  const counts = summary.counts || {};
  const mediaCounts = summary.media_counts || {};
  const total = summary.total || 0;

  postureValue.classList.remove("error-text");
  postureValue.textContent = "Batch complete";
  scoreValue.textContent = `${total} files`;
  sideValue.textContent = "ZIP ready";
  angleList.innerHTML = "";
  profilePartList.innerHTML = "";
  referenceDeltaList.innerHTML = "";
  adviceList.innerHTML = "";
  footerAngles.innerHTML = "";
  footerAdvice.textContent = "Rule-based auto suggestion; review edge cases manually.";
  footerPosture.textContent = "Batch complete";
  footerPosture.className = "good";
  footerMeta.textContent = `Images ${mediaCounts.image || 0} / Videos ${mediaCounts.video || 0}`;

  [
    ["Standing", counts.standing || 0, "good"],
    ["Sitting", counts.sitting || 0, ""],
    ["Incomplete", counts.incomplete || 0, "bad"],
  ].forEach(([label, value, kind]) => {
    const item = document.createElement("div");
    item.className = `angle-item ${kind}`;
    item.innerHTML = `
      <div class="angle-title">
        <span>${label}</span>
        <span>${value}</span>
      </div>
      <div class="angle-detail">Rule-based batch classification</div>
    `;
    angleList.appendChild(item);

    const footerItem = document.createElement("span");
    footerItem.className = `footer-angle ${kind || "good"}`;
    footerItem.textContent = `${label}: ${value}`;
    footerAngles.appendChild(footerItem);
  });

  const note = document.createElement("div");
  note.className = "advice-item";
  note.textContent = "Export includes standing/sitting/incomplete folders, annotated samples, CSV, and summary.md.";
  adviceList.appendChild(note);

  downloadBatch.href = payload.download_url;
  downloadBatch.hidden = false;
}

function renderReviewSummary(payload) {
  const summary = payload.summary || {};
  const matrix = summary.confusion_matrix || {};
  const total = summary.total || 0;
  const evaluated = summary.evaluated || 0;
  const needsReview = summary.needs_review || 0;

  postureValue.classList.remove("error-text");
  postureValue.textContent = "Review complete";
  scoreValue.textContent = `${evaluated}/${total} evaluated`;
  sideValue.textContent = `F1 ${formatMetric(summary.f1)}`;
  angleList.innerHTML = "";
  profilePartList.innerHTML = "";
  referenceDeltaList.innerHTML = "";
  adviceList.innerHTML = "";
  footerAngles.innerHTML = "";
  footerAdvice.textContent = "mAP is not computed until ground-truth keypoint/box labels and model outputs exist.";
  footerPosture.textContent = "Dataset review complete";
  footerPosture.className = "good";
  footerMeta.textContent = `Positive label: ${summary.positive_label || "bad"} / Needs review ${needsReview}`;

  [
    ["Accuracy", formatMetric(summary.accuracy), "good", "Correct predictions among evaluated good/bad rows"],
    ["Precision", formatMetric(summary.precision), "good", "Bad-posture precision in this baseline review"],
    ["Recall", formatMetric(summary.recall), "good", "Bad-posture recall in this baseline review"],
    ["F1", formatMetric(summary.f1), "good", "Harmonic mean of precision and recall"],
    ["Needs Review", needsReview, needsReview ? "bad" : "good", "Unscored rows such as no detection, front view, or incomplete profile"],
    ["mAP", "N/A", "", "Requires ground-truth boxes/keypoints and trained detector outputs"],
  ].forEach(([label, value, kind, detail]) => {
    const item = document.createElement("div");
    item.className = `angle-item ${kind}`;
    item.innerHTML = `
      <div class="angle-title">
        <span>${label}</span>
        <span>${value}</span>
      </div>
      <div class="angle-detail">${detail}</div>
    `;
    angleList.appendChild(item);

    const footerItem = document.createElement("span");
    footerItem.className = `footer-angle ${kind || "good"}`;
    footerItem.textContent = `${label}: ${value}`;
    footerAngles.appendChild(footerItem);
  });

  const confusion = document.createElement("div");
  confusion.className = "advice-item";
  confusion.textContent = `Confusion matrix: TP ${matrix.tp || 0}, FP ${matrix.fp || 0}, TN ${matrix.tn || 0}, FN ${matrix.fn || 0}.`;
  adviceList.appendChild(confusion);

  const note = document.createElement("div");
  note.className = "advice-item";
  note.textContent = "ZIP includes original images, annotated images, review_report.csv, metrics.json, and summary.md.";
  adviceList.appendChild(note);

  downloadReview.href = payload.download_url;
  downloadReview.hidden = false;
}

function stopActiveStream() {
  if (activeStreamController) {
    activeStreamController.abort();
    activeStreamController = null;
  }
}

function resetBatchDownload() {
  downloadBatch.hidden = true;
  downloadBatch.removeAttribute("href");
  downloadReview.hidden = true;
  downloadReview.removeAttribute("href");
}

function updateWebcamCaptureUi(payload) {
  webcamCaptureStatus.textContent = `${payload.count}/${payload.target} captured`;
  if (payload.ready && payload.download_url) {
    webcamCaptureDownloadUrl = payload.download_url;
    captureWebcamButton.textContent = "Download capture ZIP";
    webcamCaptureStatus.textContent = `${payload.count}/${payload.target} captured - ready to download`;
  }
}

function collectionMetadata() {
  const collector = collectorInput.value.trim();
  const subjectId = subjectInput.value.trim();
  const label = postureLabel.value.trim();

  if (!collector) {
    return {ok: false, error: "Collector is required."};
  }
  if (!subjectId) {
    return {ok: false, error: "Subject ID is required."};
  }
  if (!label) {
    return {ok: false, error: "Choose good or bad posture."};
  }
  syncActiveReference();
  if (!referenceComplete(referenceSkeleton)) {
    return {ok: false, error: "Fixed reference waiting for a detected side pose."};
  }
  if (!latestResult || latestResult.profile_complete === false) {
    return {ok: false, error: `Missing profile parts: ${missingProfileText(latestResult)}`};
  }

  return {
    ok: true,
    payload: {
      collector,
      subject_id: subjectId,
      label,
      notes: captureNotes.value.trim(),
      source: browserCameraStream ? "phone-camera" : "computer-webcam",
      reference: referenceSkeleton,
    },
  };
}

async function resetWebcamCaptureSet() {
  webcamCaptureDownloadUrl = "";
  captureWebcamButton.textContent = "Capture / Download";
  webcamCaptureStatus.textContent = "0/10 captured";
  try {
    await fetch("/api/webcam-captures-reset", { method: "POST" });
  } catch (error) {
    setStatus("Reset skipped", "bad");
  }
}

function renderProfileParts(result) {
  profilePartList.innerHTML = "";
  const parts = result && Array.isArray(result.profile_parts) ? result.profile_parts : [];
  if (!parts.length) {
    return;
  }

  parts.forEach((part) => {
    const item = document.createElement("div");
    item.className = `angle-item ${part.visible ? "good" : "bad"}`;
    item.innerHTML = `
      <div class="angle-title">
        <span>${part.name}</span>
        <span>${part.visible ? "visible" : "missing"}</span>
      </div>
      <div class="angle-detail">Proxy ${part.proxy} / visibility ${part.visibility}</div>
    `;
    profilePartList.appendChild(item);
  });
}

function missingProfileText(result) {
  const missing = result && Array.isArray(result.missing_profile_parts)
    ? result.missing_profile_parts
    : [];
  return missing.length ? missing.join(", ") : "required body profile";
}

function setReferenceFromCurrentPose() {
  const keypoints = latestResult && Array.isArray(latestResult.keypoints) ? latestResult.keypoints : [];
  if (!latestResult || !latestResult.detected || latestResult.view_valid === false || keypoints.length < 5) {
    setStatus("No side pose", "bad");
    referenceStatus.textContent = "Use a detected side-view pose first.";
    return;
  }

  const points = {};
  keypoints.forEach((point) => {
    if (referencePointNames.includes(point.name)) {
      points[point.name] = {x: point.x, y: point.y};
    }
  });

  if (!referenceComplete({points})) {
    setStatus("Reference failed", "bad");
    referenceStatus.textContent = "Current pose is missing required points.";
    return;
  }

  customReferenceSkeleton = {
    points,
    angles: calculateReferenceAngles(points),
    segment_angles: calculateReferenceSegmentAngles(points),
    source: customReferenceSource,
    updated_at: new Date().toISOString(),
  };
  referenceMode = referenceModes.custom;
  referenceSkeleton = customReferenceSkeleton;
  saveCustomReferenceSkeleton();
  referenceVisible = true;
  referenceEditing = false;
  updateReferenceStatus();
  renderReferenceDiffs(latestResult);
  drawReferenceOverlay();
  setStatus("Reference set", "good");
}

function toggleReferenceEditing() {
  if (referenceMode !== referenceModes.custom) {
    setStatus("Fixed reference", "bad");
    referenceStatus.textContent = "Fixed reference line cannot be edited.";
    return;
  }
  if (!referenceComplete(customReferenceSkeleton)) {
    setStatus("No custom reference", "bad");
    referenceStatus.textContent = "Use current pose as custom reference before editing.";
    return;
  }
  referenceEditing = !referenceEditing;
  referenceVisible = true;
  updateReferenceStatus();
  drawReferenceOverlay();
}

function toggleReferenceVisibility() {
  referenceVisible = !referenceVisible;
  updateReferenceStatus();
  drawReferenceOverlay();
}

function resetReferenceSkeleton() {
  referenceMode = referenceModes.fixed;
  customReferenceSkeleton = null;
  syncActiveReference();
  referenceEditing = false;
  draggingReferencePoint = "";
  localStorage.removeItem(referenceStorageKey);
  updateReferenceStatus();
  renderReferenceDiffs(latestResult);
  drawReferenceOverlay();
  setStatus("Fixed reference", "good");
}

function loadCustomReferenceSkeleton() {
  try {
    const raw = localStorage.getItem(referenceStorageKey);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    if (!referenceComplete(parsed)) {
      return null;
    }
    parsed.angles = parsed.angles || calculateReferenceAngles(parsed.points);
    parsed.segment_angles = parsed.segment_angles || calculateReferenceSegmentAngles(parsed.points);
    parsed.source = customReferenceSource;
    return parsed;
  } catch (error) {
    return null;
  }
}

function saveCustomReferenceSkeleton() {
  if (referenceComplete(customReferenceSkeleton)) {
    localStorage.setItem(referenceStorageKey, JSON.stringify(customReferenceSkeleton));
  }
}

function syncActiveReference() {
  if (referenceMode === referenceModes.custom) {
    referenceSkeleton = customReferenceSkeleton;
  } else {
    referenceEditing = false;
    referenceSkeleton = buildFixedReferenceSkeleton(latestResult);
  }
  updateReferenceStatus();
}

function buildFixedReferenceSkeleton(result) {
  const current = keypointsByName(result);
  if (!current) {
    return null;
  }

  const x = referenceLineX(current);

  const points = {};
  referencePointNames.forEach((name) => {
    points[name] = {
      x,
      y: clamp(current[name].y, 0.03, 0.97),
    };
  });

  referencePointNames.forEach((name) => {
    points[name].x = roundCoordinate(points[name].x);
    points[name].y = roundCoordinate(points[name].y);
  });

  return {
    points,
    angles: {
      ear_shoulder_hip: 180,
      shoulder_hip_knee: 180,
      hip_knee_ankle: 180,
    },
    segment_angles: {
      ear_shoulder: 0,
      shoulder_hip: 0,
      hip_knee: 0,
      knee_ankle: 0,
    },
    source: fixedReferenceSource,
    updated_at: new Date().toISOString(),
  };
}

function referenceLineX(points) {
  const values = ["shoulder", "hip", "knee", "ankle"]
    .map((name) => points[name] && points[name].x)
    .filter((value) => Number.isFinite(value))
    .sort((a, b) => a - b);
  if (!values.length) {
    return 0.5;
  }
  const mid = Math.floor(values.length / 2);
  const x = values.length % 2
    ? values[mid]
    : (values[mid - 1] + values[mid]) / 2;
  return clamp(x, 0.05, 0.95);
}

function keypointsByName(result) {
  const keypoints = result && Array.isArray(result.keypoints) ? result.keypoints : [];
  const points = {};
  keypoints.forEach((point) => {
    if (referencePointNames.includes(point.name) && Number.isFinite(point.x) && Number.isFinite(point.y)) {
      points[point.name] = {x: point.x, y: point.y};
    }
  });
  return referencePointNames.every((name) => points[name]) ? points : null;
}

function referenceComplete(reference) {
  const points = reference && reference.points ? reference.points : {};
  return referencePointNames.every((name) => {
    const point = points[name];
    return point && Number.isFinite(point.x) && Number.isFinite(point.y);
  });
}

function updateReferenceStatus() {
  const hasReference = referenceComplete(referenceSkeleton);
  if (referenceMode === referenceModes.custom) {
    referenceStatus.textContent = hasReference
      ? `Custom reference ${referenceEditing ? "editing" : "ready"}`
      : "No custom reference set";
  } else {
    referenceStatus.textContent = hasReference
      ? "Fixed reference line"
      : "Reference waiting for pose";
  }
  editReferenceButton.disabled = referenceMode !== referenceModes.custom;
  editReferenceButton.textContent = referenceEditing ? "Finish editing" : "Edit reference";
  toggleReferenceButton.textContent = referenceVisible ? "Hide reference" : "Show reference";
  referenceCanvas.classList.toggle("editing", referenceEditing && hasReference && referenceVisible);
}

function drawReferenceOverlay() {
  const rect = referenceCanvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(rect.width));
  const height = Math.max(1, Math.round(rect.height));
  if (referenceCanvas.width !== width || referenceCanvas.height !== height) {
    referenceCanvas.width = width;
    referenceCanvas.height = height;
  }
  referenceCtx.clearRect(0, 0, referenceCanvas.width, referenceCanvas.height);

  if (!referenceVisible || !referenceComplete(referenceSkeleton)) {
    return;
  }

  const mediaBox = currentMediaBox();
  const referencePointsByName = {};
  referencePointNames.forEach((name) => {
    referencePointsByName[name] = normalizedToCanvas(referenceSkeleton.points[name], mediaBox);
  });
  const points = referencePointNames.map((name) => referencePointsByName[name]);
  const currentPointsByName = keypointsByName(latestResult);
  const currentCanvasPointsByName = {};
  if (currentPointsByName) {
    referencePointNames.forEach((name) => {
      currentCanvasPointsByName[name] = normalizedToCanvas(currentPointsByName[name], mediaBox);
    });
  }

  referenceCtx.lineWidth = 4;
  referenceCtx.strokeStyle = "#22a447";
  referenceCtx.fillStyle = "#22a447";
  referenceCtx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) {
      referenceCtx.moveTo(point.x, point.y);
    } else {
      referenceCtx.lineTo(point.x, point.y);
    }
  });
  referenceCtx.stroke();

  points.forEach((point, index) => {
    referenceCtx.beginPath();
    referenceCtx.arc(point.x, point.y, referenceEditing ? 9 : 6, 0, Math.PI * 2);
    referenceCtx.fill();
    referenceCtx.lineWidth = 2;
    referenceCtx.strokeStyle = "#ffffff";
    referenceCtx.stroke();
    if (referenceEditing) {
      referenceCtx.fillStyle = "#ffffff";
      referenceCtx.font = "12px system-ui, sans-serif";
      referenceCtx.fillText(referencePointNames[index], point.x + 11, point.y - 8);
      referenceCtx.fillStyle = "#22a447";
    }
  });

  if (currentPointsByName) {
    const currentGood = latestResult && latestResult.overall_good;
    const currentColor = currentGood ? "#22a447" : "#d22b2b";
    referenceCtx.lineWidth = 4;
    referenceCtx.strokeStyle = currentColor;
    referenceCtx.fillStyle = currentColor;

    referenceSegmentAngleNames.forEach(([, , startName, endName]) => {
      const start = currentCanvasPointsByName[startName];
      const end = referencePointsByName[endName];
      if (!start || !end) {
        return;
      }
      referenceCtx.beginPath();
      referenceCtx.moveTo(start.x, start.y);
      referenceCtx.lineTo(end.x, end.y);
      referenceCtx.stroke();
    });

    referencePointNames.forEach((name) => {
      const point = currentCanvasPointsByName[name];
      if (!point) {
        return;
      }
      referenceCtx.beginPath();
      referenceCtx.arc(point.x, point.y, currentGood ? 5 : 7, 0, Math.PI * 2);
      referenceCtx.fill();
      referenceCtx.lineWidth = 2;
      referenceCtx.strokeStyle = "#ffffff";
      referenceCtx.stroke();
      referenceCtx.fillStyle = currentColor;
      referenceCtx.strokeStyle = currentColor;
    });

    drawSegmentAngleLabels(currentCanvasPointsByName, referencePointsByName, currentColor);
  }
}

function drawSegmentAngleLabels(currentPointsByName, referencePointsByName, color) {
  const segmentAngles = latestResult && Array.isArray(latestResult.segment_angles)
    ? latestResult.segment_angles
    : [];
  if (!segmentAngles.length) {
    return;
  }
  referenceCtx.font = "12px system-ui, sans-serif";
  referenceCtx.fillStyle = color;
  const angleByName = {};
  segmentAngles.forEach((angle) => {
    angleByName[angle.name] = angle;
  });
  referenceSegmentAngleNames.forEach(([name, label, startName, endName]) => {
    const angle = angleByName[name];
    const start = currentPointsByName[startName];
    const end = referencePointsByName[endName];
    if (!start || !end) {
      return;
    }
    const x = (start.x + end.x) / 2 + 8;
    const y = (start.y + end.y) / 2 - 6;
    const value = angle ? angle.angle : "-";
    referenceCtx.fillText(`${label} ${value} deg`, x, y);
  });
}

function currentMediaBox() {
  const canvasRect = referenceCanvas.getBoundingClientRect();
  const media = preview.classList.contains("active") ? preview : previewVideo.classList.contains("active") ? previewVideo : null;
  if (!media) {
    return {x: 0, y: 0, width: canvasRect.width, height: canvasRect.height};
  }

  const mediaRect = media.getBoundingClientRect();
  if (!mediaRect.width || !mediaRect.height) {
    return {x: 0, y: 0, width: canvasRect.width, height: canvasRect.height};
  }

  return {
    x: mediaRect.left - canvasRect.left,
    y: mediaRect.top - canvasRect.top,
    width: mediaRect.width,
    height: mediaRect.height,
  };
}

function normalizedToCanvas(point, mediaBox) {
  return {
    x: mediaBox.x + point.x * mediaBox.width,
    y: mediaBox.y + point.y * mediaBox.height,
  };
}

function canvasToNormalized(x, y, mediaBox) {
  return {
    x: clamp((x - mediaBox.x) / mediaBox.width, 0, 1),
    y: clamp((y - mediaBox.y) / mediaBox.height, 0, 1),
  };
}

function startReferenceDrag(event) {
  if (referenceMode !== referenceModes.custom || !referenceEditing || !referenceComplete(referenceSkeleton)) {
    return;
  }
  const point = nearestReferencePoint(event);
  if (!point) {
    return;
  }
  draggingReferencePoint = point;
  referenceCanvas.classList.add("dragging");
  referenceCanvas.setPointerCapture(event.pointerId);
  event.preventDefault();
}

function dragReferencePoint(event) {
  if (referenceMode !== referenceModes.custom || !draggingReferencePoint || !referenceComplete(referenceSkeleton)) {
    return;
  }
  const rect = referenceCanvas.getBoundingClientRect();
  const mediaBox = currentMediaBox();
  customReferenceSkeleton.points[draggingReferencePoint] = canvasToNormalized(
    event.clientX - rect.left,
    event.clientY - rect.top,
    mediaBox,
  );
  customReferenceSkeleton.angles = calculateReferenceAngles(customReferenceSkeleton.points);
  customReferenceSkeleton.segment_angles = calculateReferenceSegmentAngles(customReferenceSkeleton.points);
  customReferenceSkeleton.updated_at = new Date().toISOString();
  referenceSkeleton = customReferenceSkeleton;
  saveCustomReferenceSkeleton();
  renderReferenceDiffs(latestResult);
  drawReferenceOverlay();
}

function stopReferenceDrag(event) {
  if (draggingReferencePoint && event.pointerId !== undefined) {
    try {
      referenceCanvas.releasePointerCapture(event.pointerId);
    } catch (error) {
      // Pointer capture may already be released by the browser.
    }
  }
  draggingReferencePoint = "";
  referenceCanvas.classList.remove("dragging");
}

function nearestReferencePoint(event) {
  const rect = referenceCanvas.getBoundingClientRect();
  const mediaBox = currentMediaBox();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  let nearest = "";
  let nearestDistance = Infinity;
  referencePointNames.forEach((name) => {
    const point = normalizedToCanvas(referenceSkeleton.points[name], mediaBox);
    const distance = Math.hypot(point.x - x, point.y - y);
    if (distance < nearestDistance) {
      nearest = name;
      nearestDistance = distance;
    }
  });
  return nearestDistance <= 24 ? nearest : "";
}

function renderReferenceDiffs(result) {
  referenceDeltaList.innerHTML = "";
  if (!referenceComplete(referenceSkeleton)) {
    return;
  }
  referenceSkeleton.angles = referenceSkeleton.angles || calculateReferenceAngles(referenceSkeleton.points);
  referenceSkeleton.segment_angles = referenceSkeleton.segment_angles || calculateReferenceSegmentAngles(referenceSkeleton.points);

  const resultSegments = {};
  (result && result.segment_angles ? result.segment_angles : []).forEach((angle) => {
    resultSegments[angle.name] = angle.angle;
  });

  referenceSegmentAngleNames.forEach(([name, label]) => {
    const referenceAngle = referenceSkeleton.segment_angles[name] || 0;
    const resultAngle = resultSegments[name];
    const item = document.createElement("div");
    item.className = "angle-item good";
    const deltaText = Number.isFinite(resultAngle)
      ? `${(resultAngle - referenceAngle).toFixed(1)} deg`
      : "-";
    item.innerHTML = `
      <div class="angle-title">
        <span>${label} ref diff</span>
        <span>${deltaText}</span>
      </div>
      <div class="angle-detail">Reference ${referenceAngle.toFixed(1)} deg</div>
    `;
    referenceDeltaList.appendChild(item);
  });
}

function calculateReferenceAngles(points) {
  return {
    ear_shoulder_hip: roundAngle(angleAt(points.ear, points.shoulder, points.hip)),
    shoulder_hip_knee: roundAngle(angleAt(points.shoulder, points.hip, points.knee)),
    hip_knee_ankle: roundAngle(angleAt(points.hip, points.knee, points.ankle)),
  };
}

function calculateReferenceSegmentAngles(points) {
  return {
    ear_shoulder: roundAngle(verticalDeviation(points.ear, points.shoulder)),
    shoulder_hip: roundAngle(verticalDeviation(points.shoulder, points.hip)),
    hip_knee: roundAngle(verticalDeviation(points.hip, points.knee)),
    knee_ankle: roundAngle(verticalDeviation(points.knee, points.ankle)),
  };
}

function angleAt(a, b, c) {
  const ba = {x: a.x - b.x, y: a.y - b.y};
  const bc = {x: c.x - b.x, y: c.y - b.y};
  const dot = ba.x * bc.x + ba.y * bc.y;
  const magA = Math.hypot(ba.x, ba.y);
  const magC = Math.hypot(bc.x, bc.y);
  if (!magA || !magC) {
    return 0;
  }
  const cos = clamp(dot / (magA * magC), -1, 1);
  return Math.acos(cos) * 180 / Math.PI;
}

function verticalDeviation(a, b) {
  const dx = Math.abs(a.x - b.x);
  const dy = Math.abs(a.y - b.y);
  if (!dx && !dy) {
    return 0;
  }
  return Math.atan2(dx, dy) * 180 / Math.PI;
}

function roundAngle(value) {
  return Math.round(value * 10) / 10;
}

function roundCoordinate(value) {
  return Math.round(value * 1000000) / 1000000;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function formatMetric(value) {
  return Number.isFinite(value) ? value.toFixed(3) : "0.000";
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function refreshEvidenceButton() {
  downloadEvidence.disabled = !(latestResult && latestFrameDataUrl);
}

function downloadCurrentEvidence() {
  if (!latestResult || !latestFrameDataUrl) {
    setStatus("No evidence", "bad");
    return;
  }
  syncActiveReference();

  const evidence = {
    app: "surf-posture-demo",
    exported_at: new Date().toISOString(),
    mode: activeMode,
    source: latestSourceName || activeMode,
    result: latestResult,
    reference: referenceSkeleton,
    preview_image: latestFrameDataUrl,
  };
  const text = JSON.stringify(evidence, null, 2);
  const blob = new Blob([text], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const stamp = evidence.exported_at.replace(/[:.]/g, "-");
  link.href = url;
  link.download = `surf-posture-evidence-${activeMode}-${stamp}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  setStatus("Evidence saved", "good");
}
