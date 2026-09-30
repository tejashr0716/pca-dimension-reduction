/* Browser state and async HTTP only. PCA is always calculated on the server. */
(() => {
  "use strict";
  const byId = (id) => document.getElementById(id);
  const form = byId("analysis-form");
  const fileInput = byId("csv-file");
  const componentInput = byId("components");
  const controls = ["csv-file", "components", "run-button", "demo-button", "reset-button", "download-button"];
  const state = { file: null, payload: null, chart: null, view: "individual", busy: false };
  const fmt = InlineChartRuntime.formatValue;
  const uploadLimit = Number(form.dataset.uploadLimit);
  const theme = window.matchMedia("(prefers-color-scheme: dark)");

  function status(message) {
    byId("status").textContent = message;
  }

  function showError(message) {
    byId("error").textContent = message;
    byId("error").hidden = false;
    status("The request could not complete.");
  }

  function setBusy(busy) {
    state.busy = busy;
    controls.forEach((id) => { byId(id).disabled = busy; });
    form.setAttribute("aria-busy", String(busy));
    byId("run-button").textContent = busy ? "Processing…" : "Run PCA →";
  }

  function selectFile(file) {
    state.file = file || null;
    byId("selected-file").hidden = !file;
    byId("selected-file").textContent = file ? `${file.name} (${(file.size / 1_000_000).toFixed(2)} MB)` : "";
    byId("error").hidden = true;
    status(file ? "File selected. Choose your component count." : "Ready when you are.");
  }

  async function parseResponse(response) {
    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error("The server returned an unexpected response. It may be restarting; try again.");
    }
    if (!response.ok) {
      throw new Error(data.error?.message || "The request failed. Please try again.");
    }
    return data;
  }

  function validatePayload(data) {
    const values = [...(data.variance_by_component || []), ...(data.cumulative_variance_percent || [])];
    if (!data.analysis_id || !data.reduced_features || values.length !== data.reduced_features * 2 ||
        values.some((value) => !Number.isFinite(value) || value < 0 || value > 100.0000001)) {
      throw new Error("The server returned incomplete PCA metrics. Please run the analysis again.");
    }
  }

  async function analyzeSelectedFile() {
    if (!state.file) { showError("Choose a CSV file first."); return; }
    if (!/\.csv$/i.test(state.file.name)) { showError("Only .csv files are supported."); return; }
    if (state.file.size > uploadLimit) { showError("The file exceeds the 50 MB request limit."); return; }
    const raw = componentInput.value;
    if (!/^\d+$/.test(raw) || Number(raw) < 1 || Number(raw) > 500) {
      showError("Use a whole-number component count from 1 to 500."); return;
    }
    byId("error").hidden = true;
    setBusy(true);
    status("Validating, cleaning and standardizing the numeric features…");
    const body = new FormData();
    body.append("file", state.file);
    body.append("components", raw);
    try {
      const data = await parseResponse(await fetch("/api/analyze", { method: "POST", body }));
      validatePayload(data);
      state.payload = data;
      renderResults(data);
      status("Analysis complete. Your reduced CSV is ready.");
    } catch (error) {
      state.payload = null;
      byId("results").hidden = true;
      byId("empty-state").hidden = false;
      showError(error.message || "Could not reach the server. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  function makeTable(table, headers, rows, captionText) {
    table.replaceChildren();
    const caption = document.createElement("caption");
    caption.textContent = captionText;
    const head = document.createElement("thead");
    const heading = document.createElement("tr");
    headers.forEach((text) => {
      const cell = document.createElement("th");
      cell.scope = "col";
      cell.textContent = text;
      heading.append(cell);
    });
    head.append(heading);
    const body = document.createElement("tbody");
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      row.forEach((text, index) => {
        const cell = document.createElement(index === 0 ? "th" : "td");
        if (index === 0) cell.scope = "row";
        cell.textContent = text;
        tr.append(cell);
      });
      body.append(tr);
    });
    table.append(caption, head, body);
  }

  function renderResults(data) {
    byId("empty-state").hidden = true;
    byId("results").hidden = false;
    byId("result-file").textContent = data.filename;
    byId("input-features").textContent = fmt(data.numeric_features_used, "count");
    byId("output-features").textContent = fmt(data.reduced_features, "count");
    byId("variance-retained").textContent = fmt(data.explained_variance_percent, "percent");
    byId("rows-used").textContent = fmt(data.processed_rows, "count");
    byId("processing-time").textContent = fmt(data.processing_time_ms, "durationMs");
    byId("row-summary").textContent = `${fmt(data.processed_rows, "count")} of ${fmt(data.original_rows, "count")} rows retained after complete-case cleaning.`;
    byId("missing-cells").textContent = fmt(data.missing_cells, "count");
    byId("infinite-cells").textContent = fmt(data.infinite_cells, "count");
    byId("rows-dropped").textContent = fmt(data.dropped_rows, "count");
    const ignored = data.ignored_columns.length ? `Text/non-numeric columns skipped: ${data.ignored_columns.join(", ")}.` : "No non-numeric columns skipped.";
    const constant = data.constant_columns.length ? ` Constant columns removed: ${data.constant_columns.join(", ")}.` : " No constant columns removed.";
    byId("column-summary").textContent = ignored + constant;
    const columns = Array.from({ length: data.reduced_features }, (_, i) => `PC_${i + 1}`);
    const scoreFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 5 });
    makeTable(byId("preview-table"), ["Source row", ...columns],
      data.preview.map((row, i) => [fmt(data.preview_source_rows[i], "count"), ...columns.map((column) => scoreFormatter.format(row[column]))]),
      "PCA scores for the first complete rows; source row excludes the header.");
    makeTable(byId("variance-table"), ["Component", "Explained variance", "Cumulative"],
      data.variance_by_component.map((value, i) => [`PC ${i + 1}`, fmt(value, "percent"), fmt(data.cumulative_variance_percent[i], "percent")]),
      "Exact plotted observations, rounded to two decimal places.");
    const loadings = byId("loadings");
    loadings.replaceChildren();
    data.top_loadings.slice(0, 3).forEach((component) => {
      const row = document.createElement("div");
      row.className = "loading-row";
      const title = document.createElement("strong");
      title.textContent = component.component;
      row.append(title);
      component.features.forEach((feature) => {
        const item = document.createElement("span");
        item.textContent = `${feature.name}: ${feature.weight.toFixed(3)}`;
        row.append(item);
      });
      loadings.append(row);
    });
    renderChart();
  }

  function renderChart() {
    if (state.chart) { state.chart.destroy(); state.chart = null; }
    const data = state.payload;
    if (!data) return;
    const cumulative = state.view === "cumulative";
    const allValues = cumulative ? data.cumulative_variance_percent : data.variance_by_component;
    const values = allValues.slice(0, 20);
    const labels = values.map((_, i) => `PC ${i + 1}`);
    const measure = cumulative ? "Cumulative variance" : "Explained variance";
    byId("chart-context").textContent = values.length < allValues.length
      ? `Showing the first ${values.length} of ${allValues.length} components in PCA order. All values are in the table.`
      : `${measure} (%) by component, in descending eigenvalue order.`;
    const description = `${measure}: ` + labels.map((label, i) => `${label} ${fmt(values[i], "percent")}`).join("; ");
    byId("chart-summary").textContent = description;
    byId("variance-chart").setAttribute("aria-label", description);
    document.querySelectorAll("[data-view]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.view === state.view));
    });
    if (typeof Chart === "undefined") {
      byId("chart-fallback").hidden = false;
      byId("variance-details").open = true;
      return;
    }
    byId("chart-fallback").hidden = true;
    const css = getComputedStyle(document.documentElement);
    const color = css.getPropertyValue(cumulative ? "--purple" : "--blue").trim() || "#7fb4ec";
    const muted = css.getPropertyValue("--muted").trim() || "#59616c";
    const grid = css.getPropertyValue("--grid").trim() || "rgba(25,25,24,.08)";
    const border = css.getPropertyValue("--border-strong").trim() || "rgba(25,25,24,.2)";
    const range = cumulative
      ? InlineChartRuntime.axisRange(0, 100, { zero: true, floor: 0, cap: 100 })
      : InlineChartRuntime.axisRange(0, Math.max(...values), { zero: true });
    const plugins = [
      ...(cumulative ? [InlineChartRuntime.chartJs.crosshair] : []),
      InlineChartRuntime.chartJs.createAudit({ valueAxis: "y", valueKind: "percent" })
    ];
    const chart = new Chart(byId("variance-chart"), {
      type: cumulative ? "line" : "bar",
      plugins,
      data: {
        labels,
        datasets: [{
          label: measure, valueKind: "percent", data: values,
          backgroundColor: color, borderColor: color,
          borderRadius: 4, maxBarThickness: 24, borderWidth: cumulative ? 2 : 0,
          pointRadius: 3, pointHoverRadius: 4, pointBorderWidth: 0,
          pointBackgroundColor: color, fill: false, tension: 0, clip: 8
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        layout: { padding: { left: 0, right: 0, top: 0, bottom: 0 } },
        interaction: { mode: "index", intersect: false, axis: "x" },
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false, external: InlineChartRuntime.chartJs.createTooltip(String) }
        },
        scales: {
          y: {
            min: range.min, max: range.max,
            ticks: { stepSize: range.step, color: muted, font: { size: 13 },
              callback: (value) => fmt(value, "percent") },
            grid: { color: (context) => context.tick.value === 0 ? border : grid }
          },
          x: {
            grid: { display: false },
            ticks: { color: muted, font: { size: 13 }, autoSkip: labels.length > 12, maxRotation: 45 }
          }
        }
      }
    });
    InlineChartRuntime.chartJs.stabilize(chart);
    state.chart = chart;
  }

  fileInput.addEventListener("change", () => selectFile(fileInput.files[0]));
  form.addEventListener("submit", (event) => { event.preventDefault(); if (!state.busy) analyzeSelectedFile(); });
  const zone = byId("drop-zone");
  ["dragenter", "dragover"].forEach((type) => zone.addEventListener(type, (event) => {
    event.preventDefault(); if (!state.busy) zone.classList.add("dragover");
  }));
  ["dragleave", "drop"].forEach((type) => zone.addEventListener(type, (event) => {
    event.preventDefault(); zone.classList.remove("dragover");
  }));
  zone.addEventListener("drop", (event) => {
    if (state.busy) return;
    if (event.dataTransfer.files.length !== 1) { showError("Choose exactly one CSV file."); return; }
    fileInput.files = event.dataTransfer.files;
    selectFile(event.dataTransfer.files[0]);
  });
  byId("demo-button").addEventListener("click", async () => {
    setBusy(true);
    byId("error").hidden = true;
    status("Loading the reproducible seed-42 sample…");
    try {
      const response = await fetch("/sample_100d_data.csv");
      if (!response.ok) throw new Error("The sample could not load. Try uploading a CSV.");
      const file = new File([await response.blob()], "sample_100d_data.csv", { type: "text/csv" });
      const transfer = new DataTransfer();
      transfer.items.add(file);
      fileInput.files = transfer.files;
      selectFile(file);
      componentInput.value = "12";
      await analyzeSelectedFile();
    } catch (error) {
      showError(error.message);
    } finally {
      setBusy(false);
    }
  });
  byId("download-button").addEventListener("click", async () => {
    if (!state.payload) return;
    const button = byId("download-button");
    button.disabled = true;
    byId("error").hidden = true;
    try {
      const response = await fetch(state.payload.download_url);
      if (!response.ok) { await parseResponse(response); return; }
      const blobUrl = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = blobUrl;
      anchor.download = "pca_reduced_data.csv";
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
      status("Downloaded the complete reduced CSV.");
    } catch (error) {
      showError(error.message);
    } finally {
      button.disabled = false;
    }
  });
  byId("reset-button").addEventListener("click", () => {
    if (state.chart) { state.chart.destroy(); state.chart = null; }
    state.payload = null;
    state.view = "individual";
    form.reset();
    selectFile(null);
    byId("results").hidden = true;
    byId("empty-state").hidden = false;
    byId("variance-details").open = false;
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => { state.view = button.dataset.view; renderChart(); });
  });
  theme.addEventListener("change", () => { if (state.payload) renderChart(); });
})();