(function () {
  "use strict";

  var result = null;
  var recorder = null;
  var chunks = [];
  var micStarting = false;
  var stages = ["IDENTITY", "AUTHORITY", "THREAT", "URGENCY", "ISOLATION", "CREDENTIALS", "FINANCIAL", "CRITICAL"];
  var stageMap = {
    "IDENTITY_CLAIM": 0, "AUTHORITY_IMPERSONATION": 1, "FEAR_ESCALATION": 2,
    "URGENCY": 3, "ISOLATION": 4, "CREDENTIAL_EXTRACTION": 5,
    "FINANCIAL_EXTRACTION": 6, "CRITICAL": 7, "NORMAL": -1
  };
  var $ = function (id) { return document.getElementById(id); };

  function api(path, data) {
    return fetch(path, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    }).then(function (response) {
      return response.json().then(function (body) {
        if (!response.ok) { throw new Error(body.error || "Local analysis failed."); }
        return body;
      });
    });
  }

  function text(value) { return document.createTextNode(String(value || "")); }

  function setBusy(isBusy, label) {
    $("analyze-text").disabled = isBusy;
    $("analyze-text").textContent = isBusy ? (label || "Analyzing locally…") : "Analyze transcript →";
    $("audio-status").textContent = isBusy ? (label || "Analyzing locally…") : "";
  }

  function showError(message) {
    $("error-banner").hidden = !message;
    $("error-banner").textContent = message || "";
  }

  function formatTime(seconds) {
    seconds = Number(seconds || 0);
    var mins = Math.floor(seconds / 60);
    return String(mins).padStart(2, "0") + ":" + String(Math.floor(seconds % 60)).padStart(2, "0");
  }

  function levelClass(level) {
    return String(level || "LOW").toLowerCase();
  }

  function renderScenarios(items) {
    var grid = $("scenario-grid");
    grid.textContent = "";
    items.forEach(function (item) {
      var button = document.createElement("button");
      button.className = "scenario";
      button.type = "button";
      button.dataset.id = item.id;
      button.appendChild(text(item.name));
      var language = document.createElement("span");
      language.textContent = item.language.toUpperCase();
      button.appendChild(language);
      button.addEventListener("click", function () {
        Array.from(grid.children).forEach(function (child) { child.classList.remove("active"); });
        button.classList.add("active");
        setBusy(true, "Running full demo pipeline…");
        showError("");
        api("/api/analyze/scenario", {scenario_id: item.id}).then(function (data) {
          render(data);
        }).catch(function (error) {
          showError(error.message);
        }).finally(function () { setBusy(false); });
      });
      grid.appendChild(button);
    });
  }

  function renderComponents(components) {
    var names = [
      ["Language", components.language, 18],
      ["Tactics", components.tactics, 58],
      ["Progression", components.progression, 24],
      ["Narrative", components.narrative, 8],
      ["Voice", components.voice, 8]
    ];
    var target = $("component-bars");
    target.textContent = "";
    names.forEach(function (item) {
      var node = document.createElement("div");
      node.className = "component";
      var b = document.createElement("b"); b.textContent = String(item[1] || 0).replace(/\.0$/, "") + " pts";
      var span = document.createElement("span"); span.textContent = item[0].toUpperCase();
      var i = document.createElement("i"); i.style.setProperty("--value", Math.min(100, Number(item[1] || 0) / item[2] * 100) + "%");
      node.appendChild(b); node.appendChild(span); node.appendChild(i); target.appendChild(node);
    });
  }

  function renderStages(progression) {
    var target = $("stage-rail");
    target.textContent = "";
    var index = stageMap[progression.current_state] || -1;
    stages.forEach(function (stage, order) {
      var node = document.createElement("div");
      node.className = "stage" + (order <= index ? " active" : "") + (stage === "CRITICAL" ? " critical" : "");
      node.textContent = stage;
      target.appendChild(node);
    });
    $("state-title").textContent = String(progression.current_state || "NORMAL").replace(/_/g, " ");
    $("momentum-value").textContent = String(progression.momentum || 0).padStart(2, "0");
    $("momentum-fill").style.width = Math.max(3, Number(progression.momentum || 0)) + "%";
    var points = $("momentum-points");
    points.textContent = "";
    (progression.momentum_points || []).forEach(function (point) {
      var item = document.createElement("span");
      item.textContent = formatTime(point.time) + " ";
      var score = document.createElement("b"); score.textContent = point.score;
      item.appendChild(score);
      points.appendChild(item);
    });
  }

  function renderEvidence(reasons) {
    var target = $("evidence-list");
    target.textContent = "";
    reasons.forEach(function (reason) {
      var node = document.createElement("div"); node.className = "evidence";
      var title = document.createElement("b"); title.textContent = "✓ " + reason.title;
      var detail = document.createElement("p"); detail.textContent = reason.detail;
      node.appendChild(title); node.appendChild(detail);
      (reason.evidence || []).forEach(function (quote) {
        var chip = document.createElement("span"); chip.className = "quote"; chip.textContent = "“" + quote + "”";
        node.appendChild(chip);
      });
      target.appendChild(node);
    });
  }

  function renderNarrative(narrative) {
    narrative = narrative || {};
    var top = narrative.top_path;
    var ledger = $("narrative-ledger");
    ledger.textContent = "";
    if (!top) {
      $("playbook-title").textContent = "No active attack path";
      $("playbook-status").textContent = "TNG 1.0 · EVIDENCE LEDGER";
      $("narrative-summary").textContent = "No coherent high-risk behavioural chain is currently observed. SCAMTRACE will keep direct evidence visible if that changes.";
      $("counterfactual-text").textContent = "Independent verification through an official channel is always safer than trusting a number supplied during a call.";
      var empty = document.createElement("li");
      var emptyTitle = document.createElement("b"); emptyTitle.textContent = "Waiting for chain evidence";
      var emptyDetail = document.createElement("span"); emptyDetail.textContent = "This graph reports observed behaviour, not caller identity or criminality.";
      empty.appendChild(emptyTitle); empty.appendChild(emptyDetail); ledger.appendChild(empty);
      return;
    }
    $("playbook-title").textContent = top.name;
    $("playbook-status").textContent = "TNG 1.0 · " + String(top.maturity || "emerging").toUpperCase() + " · " + String(top.alignment_score || 0) + " ALIGNMENT";
    $("narrative-summary").textContent = top.summary || narrative.disclaimer || "A bounded behavioural playbook is aligned with observed evidence.";
    (top.matched_steps || []).forEach(function (step, index) {
      var item = document.createElement("li");
      var order = document.createElement("i"); order.textContent = String(index + 1).padStart(2, "0");
      var content = document.createElement("div");
      var title = document.createElement("b"); title.textContent = String(step.tactic || "EVIDENCE").replace(/_/g, " ");
      var detail = document.createElement("span"); detail.textContent = formatTime(step.time) + " · “" + String(step.phrase || "evidence") + "”";
      content.appendChild(title); content.appendChild(detail); item.appendChild(order); item.appendChild(content); ledger.appendChild(item);
    });
    if ((top.missing_steps || []).length) {
      var next = document.createElement("li"); next.className = "unobserved";
      var nextOrder = document.createElement("i"); nextOrder.textContent = "…";
      var nextContent = document.createElement("div");
      var nextTitle = document.createElement("b"); nextTitle.textContent = "Not observed";
      var nextDetail = document.createElement("span"); nextDetail.textContent = "The next playbook marker has not been observed: " + top.missing_steps.map(function (item) { return item.replace(/_/g, " "); }).join(" / ");
      nextContent.appendChild(nextTitle); nextContent.appendChild(nextDetail); next.appendChild(nextOrder); next.appendChild(nextContent); ledger.appendChild(next);
    }
    $("counterfactual-text").textContent = top.counterfactual || "Concern would reduce only after independent verification through an official channel.";
  }

  function renderIntervention(intervention, fallback) {
    intervention = intervention || {};
    $("warning-title").textContent = intervention.headline || "Clear, practical guidance";
    var list = $("recommendations"); list.textContent = "";
    var steps = intervention.steps || (fallback || []).map(function (item) { return {title: "Recommended action", action: item}; });
    steps.forEach(function (step) {
      var li = document.createElement("li");
      var content = document.createElement("span");
      var title = document.createElement("b"); title.textContent = step.title ? step.title + ": " : "";
      content.appendChild(title); content.appendChild(text(step.action || step)); li.appendChild(content); list.appendChild(li);
    });
    var script = $("intervention-script");
    script.hidden = !intervention.read_aloud;
    script.textContent = intervention.read_aloud ? "Safe response: “" + intervention.read_aloud + "”" : "";
  }

  function renderTimeline(items) {
    var target = $("timeline");
    target.textContent = "";
    if (!items || !items.length) {
      items = [{time: 0, state: "NORMAL", summary: "No escalation markers detected."}];
    }
    items.forEach(function (item) {
      var li = document.createElement("li");
      var time = document.createElement("time"); time.textContent = formatTime(item.time);
      var div = document.createElement("div");
      var title = document.createElement("b"); title.textContent = String(item.tactic || item.state || "EVENT").replace(/_/g, " ");
      var description = document.createElement("p"); description.textContent = item.summary || "";
      div.appendChild(title); div.appendChild(description);
      li.appendChild(time); li.appendChild(div); target.appendChild(li);
    });
  }

  function renderVoice(voice) {
    $("voice-label").textContent = String(voice.label || "uncertain").replace(/_/g, " ").toUpperCase();
    $("voice-score").textContent = (voice.synthetic_score === undefined ? "—" : Math.round(voice.synthetic_score));
    $("voice-model").textContent = voice.model || "No voice model";
    var target = $("voice-features"); target.textContent = "";
    Object.keys(voice.features || {}).slice(0, 4).forEach(function (key) {
      var chip = document.createElement("span");
      chip.textContent = key.replace(/_/g, " ") + ": " + voice.features[key];
      target.appendChild(chip);
    });
    if (voice.warning) {
      var warning = document.createElement("span"); warning.textContent = voice.warning;
      target.appendChild(warning);
    }
  }

  function renderPrivacy(values) {
    var target = $("privacy-details"); target.textContent = "";
    Object.keys(values || {}).forEach(function (key) {
      var node = document.createElement("div");
      var label = document.createElement("span"); label.textContent = key.replace(/_/g, " ");
      var value = document.createElement("b"); value.textContent = values[key];
      node.appendChild(label); node.appendChild(value); target.appendChild(node);
    });
  }

  function render(data) {
    result = data;
    var fusion = data.fusion;
    var klass = levelClass(fusion.level);
    $("score-value").textContent = fusion.score;
    $("score-ring").style.setProperty("--score", fusion.score);
    $("score-ring").style.setProperty("--ring-color", "var(--" + klass + ")");
    $("score-ring").className = "score-ring " + klass;
    $("threat-level").textContent = fusion.level;
    $("threat-level").className = "threat-level " + klass;
    $("threat-description").textContent = fusion.disclaimer;
    $("score-note").textContent = fusion.level === "LOW" ? "No high-risk social-engineering pattern is currently detected." : "Potential social-engineering indicators detected. Pause before acting.";
    $("source-tag").textContent = String(data.source || "LOCAL").replace(/_/g, " ");
    renderComponents(fusion.components);
    renderStages(data.progression);
    renderEvidence(fusion.reasons);
    renderNarrative(data.narrative);
    renderTimeline(data.progression.timeline);
    var categories = (data.attack_categories || []).slice(0, 3);
    $("transcript-language").textContent = (data.transcript.language || "auto").toUpperCase() + " · " + (categories.join(", ") || "NO CATEGORY");
    $("transcript-engine").textContent = data.transcript.engine || "LOCAL";
    $("transcript-output").textContent = data.transcript.text;
    var corrections = data.transcript.corrections || [];
    var correctionNote = $("transcript-corrections");
    correctionNote.hidden = !corrections.length;
    correctionNote.textContent = corrections.length
      ? "Local ASR term normalization: " + corrections.slice(0, 4).map(function (item) {
          return "“" + item.from + "” → “" + item.to + "”";
        }).join(" · ")
      : "";
    renderVoice(data.voice);
    renderPrivacy(data.privacy);
    renderIntervention(data.intervention, fusion.recommendations);
    $("download-report").disabled = false;
    $("feedback-actions").hidden = false;
    $("feedback-note").textContent = "Local memory only. No transcript is retained or used for automatic retraining.";
  }

  function readAudio(file) {
    if (!file) { return; }
    if (file.size > 25 * 1024 * 1024) { showError("Audio exceeds the 25 MB local safety limit."); return; }
    setBusy(true, "Transcribing with local ASR…");
    showError("");
    var reader = new FileReader();
    reader.onload = function () {
      var base64 = String(reader.result).split(",")[1];
      api("/api/analyze/audio", {audio_base64: base64, filename: file.name, language: $("language").value})
        .then(render).catch(function (error) { showError(error.message); }).finally(function () { setBusy(false); });
    };
    reader.onerror = function () { setBusy(false); showError("The audio file could not be read locally."); };
    reader.readAsDataURL(file);
  }

  function downloadReport() {
    if (!result) { return; }
    var includeSensitive = $("include-sensitive-report").checked;
    api("/api/report", {result: result, include_sensitive_evidence: includeSensitive}).then(function (report) {
      var blob = new Blob([JSON.stringify(report, null, 2)], {type: "application/json"});
      var link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = includeSensitive ? "scamtrace-incident-report-local-unredacted.json" : "scamtrace-incident-report-redacted.json";
      document.body.appendChild(link); link.click(); link.remove();
      URL.revokeObjectURL(link.href);
    }).catch(function (error) { showError(error.message); });
  }

  function submitFeedback(outcome) {
    if (!result) { return; }
    $("feedback-confirmed").disabled = true;
    $("feedback-false-alert").disabled = true;
    api("/api/feedback", {
      analysis_id: result.analysis_id,
      outcome: outcome,
      language: result.transcript.language,
      threat_level: result.fusion.level,
      threat_score: result.fusion.score
    }).then(function (receipt) {
      $("feedback-note").textContent = "Recorded locally for calibration review. " + receipt.storage;
    }).catch(function (error) {
      $("feedback-confirmed").disabled = false;
      $("feedback-false-alert").disabled = false;
      showError(error.message);
    });
  }

  function preferredRecorderMimeType() {
    var candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4;codecs=mp4a.40.2", "audio/mp4", "audio/ogg;codecs=opus"];
    return candidates.find(function (candidate) { return MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(candidate); }) || "";
  }

  function recorderFilename(mimeType) {
    if (/mp4|m4a/i.test(mimeType)) { return "microphone.m4a"; }
    if (/ogg/i.test(mimeType)) { return "microphone.ogg"; }
    return "microphone.webm";
  }

  function resetMicButton() {
    $("record-button").disabled = false;
    $("record-button").classList.remove("recording");
    $("record-button").innerHTML = "<span></span> Record microphone";
  }

  function setupMic() {
    $("record-button").addEventListener("click", function () {
      if (recorder && recorder.state === "recording") {
        $("record-button").disabled = true;
        $("mic-note").textContent = "Finalizing local recording…";
        recorder.stop();
        return;
      }
      if (micStarting) { return; }
      if (!navigator.mediaDevices || !window.MediaRecorder) {
        showError("This browser does not support microphone recording. Upload a file instead.");
        return;
      }
      micStarting = true;
      $("record-button").disabled = true;
      $("mic-note").textContent = "Requesting microphone permission…";
      showError("");
      navigator.mediaDevices.getUserMedia({audio: true}).then(function (stream) {
        chunks = [];
        var mimeType = preferredRecorderMimeType();
        try {
          recorder = mimeType ? new MediaRecorder(stream, {mimeType: mimeType}) : new MediaRecorder(stream);
        } catch (error) {
          stream.getTracks().forEach(function (track) { track.stop(); });
          throw new Error("Your browser could not start a compatible local audio recording.");
        }
        recorder.addEventListener("dataavailable", function (event) { if (event.data.size) { chunks.push(event.data); } });
        recorder.addEventListener("error", function () {
          stream.getTracks().forEach(function (track) { track.stop(); });
          recorder = null;
          resetMicButton();
          showError("Microphone recording failed. Please try again or upload an audio file.");
        });
        recorder.addEventListener("stop", function () {
          stream.getTracks().forEach(function (track) { track.stop(); });
          var recordedMime = recorder.mimeType || mimeType || "audio/webm";
          recorder = null;
          resetMicButton();
          if (!chunks.length) {
            showError("No microphone audio was captured. Check the selected microphone and try again.");
            return;
          }
          $("mic-note").textContent = "Recording captured locally. Starting local transcription…";
          readAudio(new File([new Blob(chunks, {type: recordedMime})], recorderFilename(recordedMime), {type: recordedMime}));
        });
        recorder.start(1000);
        micStarting = false;
        $("record-button").disabled = false;
        $("record-button").classList.add("recording");
        $("record-button").innerHTML = "<span></span> Stop & analyze";
        $("mic-note").textContent = "Recording locally — press Stop & analyze when finished.";
      }).catch(function (error) {
        micStarting = false;
        resetMicButton();
        var message = error && error.name === "NotAllowedError"
          ? "Microphone permission was not granted. Allow microphone access in the browser and retry."
          : (error && error.message) || "Microphone could not be started. Upload a file instead.";
        showError(message);
        $("mic-note").textContent = "Browser capture; analysis remains local.";
      });
    });
  }

  function boot() {
    $("transcript").addEventListener("input", function () { $("text-count").textContent = this.value.length + " / 50,000"; });
    $("analyze-text").addEventListener("click", function () {
      setBusy(true, "Analyzing locally…"); showError("");
      api("/api/analyze/text", {text: $("transcript").value, language: $("language").value})
        .then(render).catch(function (error) { showError(error.message); }).finally(function () { setBusy(false); });
    });
    $("browse-file").addEventListener("click", function () { $("audio-file").click(); });
    $("drop-zone").addEventListener("click", function () { $("audio-file").click(); });
    $("audio-file").addEventListener("change", function () { readAudio(this.files[0]); });
    ["dragenter", "dragover"].forEach(function (event) { $("drop-zone").addEventListener(event, function (e) { e.preventDefault(); $("drop-zone").classList.add("drag"); }); });
    ["dragleave", "drop"].forEach(function (event) { $("drop-zone").addEventListener(event, function (e) { e.preventDefault(); $("drop-zone").classList.remove("drag"); }); });
    $("drop-zone").addEventListener("drop", function (event) { readAudio(event.dataTransfer.files[0]); });
    $("download-report").addEventListener("click", downloadReport);
    $("include-sensitive-report").addEventListener("change", function () {
      $("download-report").textContent = this.checked ? "Export local unredacted report" : "Export redacted report";
    });
    $("feedback-confirmed").addEventListener("click", function () { submitFeedback("CONFIRMED_SCAM"); });
    $("feedback-false-alert").addEventListener("click", function () { submitFeedback("FALSE_ALERT"); });
    $("elder-mode").addEventListener("change", function () { document.body.classList.toggle("elder-mode", this.checked); });
    setupMic();
    fetch("/api/status").then(function (response) { return response.json(); }).then(function (status) {
      $("runtime-status").textContent = status.asr.available ? "LOCAL ASR READY" : "TEXT ENGINE READY";
      $("runtime-status").classList.add("ready");
      renderScenarios(status.demo_scenarios || []);
      renderPrivacy(status.privacy);
    }).catch(function () {
      $("runtime-status").textContent = "LOCAL RUNTIME UNAVAILABLE";
    });
  }
  document.addEventListener("DOMContentLoaded", boot);
}());
