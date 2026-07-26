"use strict";

const state = { result: null, market: null, report: null, version: null, charts: [] };
const $ = (id) => document.getElementById(id);
const number = (value, digits = 4) => Number(value).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
const signed = (value, suffix = "") => `${Number(value) >= 0 ? "+" : ""}${number(value)}${suffix}`;
const escapeText = (value) => String(value ?? "—");

async function getJson(path) {
  const response = await fetch(path, { method: "GET", cache: "no-store", credentials: "same-origin" });
  if (!response.ok) throw new Error(`${path} returned HTTP ${response.status}`);
  return response.json();
}

function setText(id, value) { $(id).textContent = escapeText(value); }
function pnlClass(id, value) { $(id).classList.add(Number(value) >= 0 ? "positive" : "negative"); }

function renderOverview(result, market) {
  setText("final-equity", number(result.final_equity));
  setText("final-cash", number(result.final_cash));
  setText("realized-pnl", signed(result.realized_pnl));
  setText("unrealized-pnl", signed(result.unrealized_pnl));
  setText("total-costs", number(result.cumulative_costs, 6));
  setText("max-drawdown", `${number(result.max_drawdown_pct, 4)}%`);
  pnlClass("realized-pnl", result.realized_pnl); pnlClass("unrealized-pnl", result.unrealized_pnl);
  setText("outcome", result.outcome); setText("reason-code", result.reason_code);
  setText("position-status", result.open_position ? "OPEN · MARKED" : "FLAT");
  setText("data-freshness", `${market.data_as_of} · ${market.freshness}`);
}

function chart(canvasId, tooltipId, rows, series, options = {}) {
  const canvas = $(canvasId), tooltip = $(tooltipId);
  const chartState = { canvas, tooltip, rows, series, options, selected: rows.length - 1 };
  state.charts.push(chartState);
  const draw = () => drawChart(chartState);
  canvas.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight" && event.key !== "Home" && event.key !== "End") return;
    event.preventDefault();
    if (event.key === "ArrowLeft") chartState.selected = Math.max(0, chartState.selected - 1);
    if (event.key === "ArrowRight") chartState.selected = Math.min(rows.length - 1, chartState.selected + 1);
    if (event.key === "Home") chartState.selected = 0;
    if (event.key === "End") chartState.selected = rows.length - 1;
    draw(); announcePoint(chartState);
  });
  canvas.addEventListener("pointermove", (event) => {
    const rect = canvas.getBoundingClientRect();
    const fraction = Math.max(0, Math.min(1, (event.clientX - rect.left - 42) / Math.max(1, rect.width - 62)));
    chartState.selected = Math.round(fraction * (rows.length - 1)); draw(); announcePoint(chartState);
  });
  draw(); announcePoint(chartState);
}

function announcePoint(item) {
  const row = item.rows[item.selected];
  const values = item.series.map((line) => `${line.label} ${line.format ? line.format(row[line.key]) : number(row[line.key], 3)}`).join(", ");
  item.tooltip.textContent = `${row.timestamp}: ${values}`;
}

function drawChart(item) {
  const { canvas, rows, series, options, selected } = item;
  const ratio = window.devicePixelRatio || 1, width = Math.max(300, canvas.clientWidth), height = Number(canvas.getAttribute("height"));
  canvas.width = Math.floor(width * ratio); canvas.height = Math.floor(height * ratio);
  const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio);
  const pad = { left: 48, right: 16, top: 18, bottom: 30 }, plotW = width - pad.left - pad.right, plotH = height - pad.top - pad.bottom;
  const values = series.flatMap((line) => rows.map((row) => row[line.key]).filter((v) => Number.isFinite(v)));
  if (Number.isFinite(options.reference)) values.push(options.reference);
  let min = options.min !== undefined ? options.min : Math.min(...values), max = options.max !== undefined ? options.max : Math.max(...values);
  const margin = Math.max((max - min) * .12, Math.abs(max || 1) * .005); min -= options.min === undefined ? margin : 0; max += options.max === undefined ? margin : 0;
  const x = (i) => pad.left + (i / Math.max(1, rows.length - 1)) * plotW;
  const y = (v) => pad.top + (max - v) / Math.max(.000001, max - min) * plotH;
  ctx.clearRect(0, 0, width, height); ctx.font = "11px ui-monospace, Consolas"; ctx.fillStyle = "#71838d";
  for (let i = 0; i <= 4; i += 1) { const yy = pad.top + plotH * i / 4, value = max - (max - min) * i / 4; ctx.strokeStyle = "#1a2b31"; ctx.beginPath(); ctx.moveTo(pad.left, yy); ctx.lineTo(width - pad.right, yy); ctx.stroke(); ctx.fillText(options.percent ? `${value.toFixed(1)}%` : value.toFixed(2), 3, yy + 4); }
  if (Number.isFinite(options.reference)) { ctx.setLineDash([6, 5]); ctx.strokeStyle = "#ef6e72"; ctx.beginPath(); ctx.moveTo(pad.left, y(options.reference)); ctx.lineTo(width - pad.right, y(options.reference)); ctx.stroke(); ctx.setLineDash([]); }
  series.forEach((line) => { ctx.strokeStyle = line.color; ctx.lineWidth = line.width || 2; ctx.beginPath(); let active = false; rows.forEach((row, i) => { const value = row[line.key]; if (!Number.isFinite(value)) { active = false; return; } if (!active) { ctx.moveTo(x(i), y(value)); active = true; } else ctx.lineTo(x(i), y(value)); }); ctx.stroke(); });
  if (options.signals) rows.forEach((row, i) => { if (!row.signals || !row.signals.length) return; ctx.fillStyle = "#e9b75d"; ctx.beginPath(); ctx.moveTo(x(i), y(row.close) - 11); ctx.lineTo(x(i) - 5, y(row.close) - 2); ctx.lineTo(x(i) + 5, y(row.close) - 2); ctx.closePath(); ctx.fill(); });
  const selectedX = x(selected); ctx.strokeStyle = "rgba(238,243,246,.32)"; ctx.beginPath(); ctx.moveTo(selectedX, pad.top); ctx.lineTo(selectedX, pad.top + plotH); ctx.stroke();
  ctx.fillStyle = "#71838d"; ctx.fillText(rows[0].timestamp, pad.left, height - 8); const last = rows[rows.length - 1].timestamp; ctx.fillText(last, width - pad.right - ctx.measureText(last).width, height - 8);
}

function cell(row, value) { const td = document.createElement("td"); td.textContent = value; row.appendChild(td); }
function renderTables(market, result) {
  market.points.forEach((point) => { const tr = document.createElement("tr"); cell(tr, point.timestamp); cell(tr, number(point.close, 3)); cell(tr, point.fast_sma == null ? "—" : number(point.fast_sma, 3)); cell(tr, point.slow_sma == null ? "—" : number(point.slow_sma, 3)); cell(tr, point.signals.map((s) => s.action.toUpperCase()).join(", ") || "—"); $("market-table").appendChild(tr); });
  result.equity_curve.forEach((point) => { const tr = document.createElement("tr"); cell(tr, point.timestamp); cell(tr, number(point.cash)); cell(tr, number(point.position_value)); cell(tr, number(point.total_marked_equity)); cell(tr, `${number(point.drawdown_pct, 4)}%`); $("equity-table").appendChild(tr); });
}

function renderSignals(result, market) {
  const list = $("signal-list");
  result.decisions.forEach((decision) => {
    const article = document.createElement("article"); article.className = "signal-card";
    const explanation = decision.action === "enter" ? "Fast SMA crossed above slow SMA at the completed bar close; any hypothetical eligibility begins at the next validated bar open." : "Fast SMA crossed below slow SMA while the paper portfolio was flat; no action was taken.";
    const blocks = [`<div><span>Signal timestamp</span><strong>${escapeText(decision.signal_timestamp)}</strong></div>`, `<div><span>Rule event</span><strong>${escapeText(decision.action).toUpperCase()}</strong></div>`, `<div><span>SMA-001 · v${escapeText(result.metadata.strategy_version)}</span><p>${explanation}</p></div>`, `<div><span>Reason code</span><code>${escapeText(decision.reason_code)}</code><p>${escapeText(market.data_source)} · ${escapeText(market.freshness)}</p></div>`];
    article.innerHTML = blocks.join(""); list.appendChild(article);
  });
  if (!result.decisions.length) { const empty = document.createElement("p"); empty.textContent = "No crossing events exist in this committed synthetic run."; list.appendChild(empty); }
}

function renderStrategyAndReports(result, report, version) {
  const meta = result.metadata, p = meta.strategy_parameters;
  setText("strategy-version", `v${meta.strategy_version}`); setText("fast-period", p.fast); setText("slow-period", p.slow); setText("paper-size", `${number(p.paper_size_pct, 1)}%`); setText("strategy-symbol", p.symbol); setText("strategy-hash", meta.strategy_definition_hash);
  setText("run-id", meta.run_id); setText("input-hash", meta.input_data_hash); setText("configuration-hash", meta.configuration_hash); setText("report-strategy-hash", meta.strategy_definition_hash); setText("engine-digest", meta.engine_source_digest);
  setText("report-content", report.content); setText("json-content", JSON.stringify(result, null, 2)); setText("app-version", version.application_version); setText("kernel-version", `${version.kernel_name} ${version.kernel_version}`);
}

function wireTabs() {
  [["report-tab", "report-panel", "json-tab", "json-panel"], ["json-tab", "json-panel", "report-tab", "report-panel"]].forEach(([tab, panel, otherTab, otherPanel]) => $(tab).addEventListener("click", () => { $(tab).setAttribute("aria-selected", "true"); $(otherTab).setAttribute("aria-selected", "false"); $(panel).hidden = false; $(otherPanel).hidden = true; }));
}
function download(filename, content, type) { const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url); }
function wireDownloads() { $("download-json").addEventListener("click", () => download("TRL-R2-001-synthetic-result.json", `${JSON.stringify(state.result, null, 2)}\n`, "application/json;charset=utf-8")); $("download-markdown").addEventListener("click", () => download(state.report.filename, state.report.content, "text/markdown;charset=utf-8")); }

function renderAll() {
  renderOverview(state.result, state.market); renderTables(state.market, state.result); renderSignals(state.result, state.market); renderStrategyAndReports(state.result, state.report, state.version);
  chart("market-canvas", "market-tooltip", state.market.points, [{ key: "close", label: "Close", color: "#eef3f6", width: 2 }, { key: "fast_sma", label: "Fast SMA", color: "#36d1c4" }, { key: "slow_sma", label: "Slow SMA", color: "#67a6ff" }], { signals: true });
  chart("equity-canvas", "equity-tooltip", state.result.equity_curve, [{ key: "total_marked_equity", label: "Marked equity", color: "#36d1c4", width: 2 }]);
  chart("drawdown-canvas", "drawdown-tooltip", state.result.equity_curve, [{ key: "drawdown_pct", label: "Drawdown", color: "#ef6e72", format: (v) => `${number(v, 4)}%` }], { min: -15, max: 0, reference: -15, percent: true });
}

async function loadDashboard() {
  $("loading-state").hidden = false; $("error-state").hidden = true; $("dashboard-content").hidden = true;
  try {
    [state.result, state.market, state.report, state.version] = await Promise.all([getJson("/api/demo/result"), getJson("/api/demo/market-data"), getJson("/api/demo/report"), getJson("/api/version")]);
    renderAll(); $("loading-state").hidden = true; $("dashboard-content").hidden = false;
  } catch (error) { $("loading-state").hidden = true; $("error-state").hidden = false; setText("error-message", error.message); }
}

window.addEventListener("resize", () => state.charts.forEach(drawChart));
$("retry-button").addEventListener("click", loadDashboard); wireTabs(); wireDownloads(); loadDashboard();
