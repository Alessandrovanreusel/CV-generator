/* CV Generator Web UI — frontend logic */
(function () {
  "use strict";

  const form = document.getElementById("job-form");
  const submitBtn = document.getElementById("submit-btn");
  const tabs = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll(".panel");
  const progressSection = document.getElementById("progress-section");
  const resultSection = document.getElementById("result-section");
  const errorSection = document.getElementById("error-section");
  const fileDrop = document.getElementById("file-drop");
  const fileInput = document.getElementById("input-file");
  const fileName = document.getElementById("file-name");

  let activeTab = "text";
  let eventSource = null;
  let highestStep = 0;

  // Tab switching
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      if (tab.disabled) return;
      activeTab = tab.dataset.tab;
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      panels.forEach((p) => p.classList.remove("active"));
      document.getElementById("panel-" + activeTab).classList.add("active");
    });
  });

  // File drop zone
  fileDrop.addEventListener("dragover", (e) => {
    e.preventDefault();
    fileDrop.classList.add("dragover");
  });
  fileDrop.addEventListener("dragleave", () => {
    fileDrop.classList.remove("dragover");
  });
  fileDrop.addEventListener("drop", (e) => {
    e.preventDefault();
    fileDrop.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      fileName.textContent = e.dataTransfer.files[0].name;
    }
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      fileName.textContent = fileInput.files[0].name;
    }
  });

  // Form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append("mode", activeTab);

    if (activeTab === "text") {
      formData.append("text", document.getElementById("input-text").value);
    } else if (activeTab === "file") {
      if (fileInput.files.length === 0) {
        showError("Please select a file to upload.");
        return;
      }
      formData.append("file", fileInput.files[0]);
    } else if (activeTab === "url") {
      formData.append("url", document.getElementById("input-url").value);
    } else if (activeTab === "search") {
      formData.append("search", document.getElementById("input-search").value);
      formData.append("location", document.getElementById("input-location").value);
    }

    setProcessing(true);

    try {
      const response = await fetch("/api/jobs", {
        method: "POST",
        body: formData,
      });

      if (response.status === 503) {
        showError("Server is busy — please try again shortly.");
        setProcessing(false);
        return;
      }

      if (!response.ok) {
        const data = await response.json();
        showError(data.error || "Submission failed.");
        setProcessing(false);
        return;
      }

      const { job_id } = await response.json();
      showProgress();
      startSSE(job_id);
    } catch (err) {
      showError("Network error — check your connection and try again.");
      setProcessing(false);
    }
  });

  function startSSE(jobId) {
    highestStep = 0;
    eventSource = new EventSource("/api/jobs/" + jobId + "/events");

    eventSource.addEventListener("progress", (e) => {
      const data = JSON.parse(e.data);
      if (data.step > highestStep) {
        updateStepper(data.step);
        highestStep = data.step;
      }
    });

    eventSource.addEventListener("complete", (e) => {
      const data = JSON.parse(e.data);
      eventSource.close();
      eventSource = null;
      showResult(data.company, data.title, jobId);
    });

    // F25: Use named event "pipeline_error" to avoid conflict with native EventSource "error"
    eventSource.addEventListener("pipeline_error", (e) => {
      const data = JSON.parse(e.data);
      eventSource.close();
      eventSource = null;
      showError(data.message || "An error occurred during CV generation.");
    });
  }

  function updateStepper(currentStep) {
    const steps = document.querySelectorAll(".step");
    steps.forEach((step) => {
      const stepNum = parseInt(step.dataset.step, 10);
      step.classList.remove("active", "completed");
      if (stepNum < currentStep) {
        step.classList.add("completed");
        step.querySelector(".circle").textContent = "\u2713";
      } else if (stepNum === currentStep) {
        step.classList.add("active");
      }
    });
  }

  function showProgress() {
    form.classList.add("hidden");
    progressSection.classList.remove("hidden");
    resultSection.classList.add("hidden");
    errorSection.classList.add("hidden");
    // Reset stepper
    document.querySelectorAll(".step").forEach((step) => {
      step.classList.remove("active", "completed");
      step.querySelector(".circle").textContent = step.dataset.step;
    });
  }

  function showResult(company, title, jobId) {
    progressSection.classList.add("hidden");
    resultSection.classList.remove("hidden");
    document.getElementById("result-title").textContent = title || "Unknown";
    document.getElementById("result-company").textContent = company || "Unknown";
    document.getElementById("download-btn").href = "/api/jobs/" + jobId + "/download";
    setProcessing(false);
  }

  function showError(message) {
    form.classList.add("hidden");
    progressSection.classList.add("hidden");
    errorSection.classList.remove("hidden");
    document.getElementById("error-message").textContent = message;
    setProcessing(false);
  }

  function resetUI() {
    form.classList.remove("hidden");
    progressSection.classList.add("hidden");
    resultSection.classList.add("hidden");
    errorSection.classList.add("hidden");
    setProcessing(false);
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  }

  function setProcessing(processing) {
    submitBtn.disabled = processing;
    tabs.forEach((t) => (t.disabled = processing));
  }

  // Reset buttons
  document.getElementById("reset-btn").addEventListener("click", resetUI);
  document.getElementById("error-reset-btn").addEventListener("click", resetUI);
})();
