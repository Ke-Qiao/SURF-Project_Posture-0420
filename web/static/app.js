const modeButtons = Array.from(document.querySelectorAll(".mode-button"));
const panels = {
  webcam: document.querySelector("#webcamPanel"),
  image: document.querySelector("#imagePanel"),
  video: document.querySelector("#videoPanel"),
  batch: document.querySelector("#batchPanel"),
};

const labels = {
  webcam: "Webcam",
  image: "Image",
  video: "Video",
  batch: "Batch",
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
const teacherSource = document.querySelector("#teacherSource");
const analyzeBatchButton = document.querySelector("#analyzeBatch");
const downloadBatch = document.querySelector("#downloadBatch");
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
const referenceAngleNames = [
  ["ear_shoulder_hip", "Forward Head", "ear", "shoulder", "hip"],
  ["shoulder_hip_knee", "Trunk Lean", "shoulder", "hip", "knee"],
  ["hip_knee_ankle", "Knee", "hip", "knee", "ankle"],
];
const referenceStorageKey = "surfPostureReferenceSkeleton";
let selectedMediaUrl = "";
let activeStreamController = null;
let activeMode = "webcam";
let latestResult = null;
let latestFrameDataUrl = "";
let latestSourceName = "";
let webcamCaptureDownloadUrl = "";
let referenceSkeleton = loadReferenceSkeleton();
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

async function captureWebcamSet() {
  if (webcamCaptureDownloadUrl) {
    window.location.href = webcamCaptureDownloadUrl;
    setTimeout(resetWebcamCaptureSet, 600);
    return;
  }

  const metadata = collectionMetadata();
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
  latestResult = result;
  refreshEvidenceButton();

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

    const footerItem = document.createElement("span");
    footerItem.className = `footer-angle ${angle.is_good ? "good" : "bad"}`;
    footerItem.textContent = `${angle.label}: ${angle.angle} deg, dev ${angle.deviation} deg`;
    footerAngles.appendChild(footerItem);
  });

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

function stopActiveStream() {
  if (activeStreamController) {
    activeStreamController.abort();
    activeStreamController = null;
  }
}

function resetBatchDownload() {
  downloadBatch.hidden = true;
  downloadBatch.removeAttribute("href");
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
  if (!referenceComplete(referenceSkeleton)) {
    return {ok: false, error: "Set a green reference skeleton first."};
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

  referenceSkeleton = {
    points,
    angles: calculateReferenceAngles(points),
    source: "current-pose",
    updated_at: new Date().toISOString(),
  };
  saveReferenceSkeleton();
  referenceVisible = true;
  referenceEditing = false;
  updateReferenceStatus();
  renderReferenceDiffs(latestResult);
  drawReferenceOverlay();
  setStatus("Reference set", "good");
}

function toggleReferenceEditing() {
  if (!referenceComplete(referenceSkeleton)) {
    setStatus("No reference", "bad");
    referenceStatus.textContent = "Set a reference before editing.";
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
  referenceSkeleton = null;
  referenceEditing = false;
  draggingReferencePoint = "";
  localStorage.removeItem(referenceStorageKey);
  updateReferenceStatus();
  renderReferenceDiffs(latestResult);
  drawReferenceOverlay();
  setStatus("Reference reset");
}

function loadReferenceSkeleton() {
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
    return parsed;
  } catch (error) {
    return null;
  }
}

function saveReferenceSkeleton() {
  if (referenceComplete(referenceSkeleton)) {
    localStorage.setItem(referenceStorageKey, JSON.stringify(referenceSkeleton));
  }
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
  referenceStatus.textContent = hasReference
    ? `Reference ${referenceEditing ? "editing" : "ready"}`
    : "No reference set";
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
  const points = referencePointNames.map((name) => normalizedToCanvas(referenceSkeleton.points[name], mediaBox));

  referenceCtx.lineWidth = 3;
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
}

function currentMediaBox() {
  const canvasRect = referenceCanvas.getBoundingClientRect();
  const media = preview.classList.contains("active") ? preview : previewVideo.classList.contains("active") ? previewVideo : null;
  const mediaWidth = media === preview ? preview.naturalWidth : previewVideo.videoWidth;
  const mediaHeight = media === preview ? preview.naturalHeight : previewVideo.videoHeight;
  if (!media || !mediaWidth || !mediaHeight) {
    return {x: 0, y: 0, width: canvasRect.width, height: canvasRect.height};
  }
  const scale = Math.min(canvasRect.width / mediaWidth, canvasRect.height / mediaHeight);
  const width = mediaWidth * scale;
  const height = mediaHeight * scale;
  return {
    x: (canvasRect.width - width) / 2,
    y: (canvasRect.height - height) / 2,
    width,
    height,
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
  if (!referenceEditing || !referenceComplete(referenceSkeleton)) {
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
  if (!draggingReferencePoint || !referenceComplete(referenceSkeleton)) {
    return;
  }
  const rect = referenceCanvas.getBoundingClientRect();
  const mediaBox = currentMediaBox();
  referenceSkeleton.points[draggingReferencePoint] = canvasToNormalized(
    event.clientX - rect.left,
    event.clientY - rect.top,
    mediaBox,
  );
  referenceSkeleton.angles = calculateReferenceAngles(referenceSkeleton.points);
  referenceSkeleton.updated_at = new Date().toISOString();
  saveReferenceSkeleton();
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

  const resultAngles = {};
  (result && result.angles ? result.angles : []).forEach((angle) => {
    resultAngles[angle.name] = angle.angle;
  });

  referenceAngleNames.forEach(([name, label]) => {
    const referenceAngle = referenceSkeleton.angles[name];
    const resultAngle = resultAngles[name];
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

function roundAngle(value) {
  return Math.round(value * 10) / 10;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
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
