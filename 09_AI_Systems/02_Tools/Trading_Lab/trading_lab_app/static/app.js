"use strict";

const state = { result: null, market: null, report: null, version: null, registry: null, liveMarket: null, news: null, paper: null, charts: [] };
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

function renderPaperDesk(bundle) {
  const empty = $("paper-empty-state");
  const warning = $("paper-persistence-warning");
  warning.hidden = true;
  if (!bundle || bundle.error) {
    empty.textContent = "The local paper desk is unavailable. No paper or broker action was taken.";
    setText("paper-persistence-status", "UNAVAILABLE");
    return;
  }
  const { account, positions, timeline, health } = bundle;
  empty.textContent = account.message;
  empty.hidden = positions.position_count > 0;
  if (account.enabled && account.marked_equity != null) {
    setText("paper-balance", number(account.cash, 2));
    setText("paper-equity", number(account.marked_equity, 2));
    setText("paper-daily-pnl", signed(account.daily_paper_pnl));
    setText("paper-drawdown", `${number(account.current_drawdown_percent, 2)}%`);
    setText("paper-open-risk", number(account.open_paper_risk_amount, 2));
    pnlClass("paper-daily-pnl", account.daily_paper_pnl);
  }
  setText("paper-open-positions", account.open_position_count);
  setText("paper-completed-trades", account.completed_paper_trade_count);
  setText("paper-timeline-count", timeline.event_count);
  setText("paper-risk-halt", health.risk_halt ? "HALTED" : "INACTIVE");
  setText("paper-risk-halt-reason", health.risk_halt_reason || "No session halt");
  setText("paper-account-schema", account.schema_version);
  setText("paper-projection-id", account.projection_id);
  setText("paper-timeline-schema", timeline.timeline_schema_version);
  setText("paper-tail-hash", timeline.tail_event_hash);
  setText("paper-persistence-status", health.persistence_status);
  setText("paper-last-observation", account.last_observation_at_utc);
  if (health.persistence_status === "WRITE_FAILED_IN_MEMORY_VALID") warning.hidden = false;
}

async function loadPaperDesk() {
  try {
    const [account, positions, timeline, health] = await Promise.all([
      getJson("/api/paper-account"),
      getJson("/api/paper-positions"),
      getJson("/api/market-timeline"),
      getJson("/api/paper-health"),
    ]);
    return { account, positions, timeline, health };
  } catch (error) { return { error: error.message }; }
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

function renderRegistry(registry) {
  const health = registry.registry_health;
  setText("registry-health", `${health.status} · ${health.reason_code}`);
  if (health.status !== "VALID") {
    $("registry-health").classList.add("registry-failed");
    setText("installed-strategy-count", "0"); setText("eligible-strategy-count", "0");
    setText("vault-bundle-digest", "Unavailable — registry failed closed");
    return;
  }
  setText("installed-strategy-count", registry.installed_strategy_count);
  setText("eligible-strategy-count", registry.executable_research_strategy_count);
  setText("vault-bundle-digest", registry.vault.bundle_digest);
  const installed = registry.installed_executable_strategies[0];
  if (installed) {
    const record = installed.record;
    setText("vault-approval-status", record.approval_status.replaceAll("_", " "));
    setText("vault-strategy-id", record.strategy_id); setText("vault-strategy-version", `v${record.strategy_version}`);
    setText("vault-strategy-name", record.display_name); setText("vault-family", record.family);
    setText("vault-markets", record.supported_markets.join(", "));
    setText("vault-timeframes", record.supported_timeframes.join(", "));
    setText("vault-indicators", record.required_indicators.join(", "));
    setText("vault-parameters", Object.keys(record.parameter_schema).join(", "));
    setText("vault-kernel-hash", record.kernel_strategy_definition_hash);
    setText("vault-record-digest", installed.registry_record_digest);
    record.known_limitations.forEach((limitation) => { const li = document.createElement("li"); li.textContent = limitation; $("vault-limitations").appendChild(li); });
  }
  registry.research_backlog.entries.forEach((entry) => {
    const article = document.createElement("article"); article.className = "backlog-card";
    const label = document.createElement("span"); label.className = "mode-state blocked"; label.textContent = "PLANNED — NOT IMPLEMENTED";
    const heading = document.createElement("h4"); heading.textContent = entry.display_name;
    const identity = document.createElement("p"); identity.textContent = `${entry.backlog_id} · ${entry.intended_timeframes.join(", ")}`;
    const question = document.createElement("p"); question.textContent = entry.research_questions.join(" ");
    article.append(label, heading, identity, question); $("backlog-cards").appendChild(article);
    const tr = document.createElement("tr"); cell(tr, entry.backlog_id); cell(tr, entry.display_name); cell(tr, entry.intended_timeframes.join(", ")); cell(tr, "PLANNED_NOT_IMPLEMENTED"); cell(tr, "False"); $("backlog-table").appendChild(tr);
  });
}

function renderMarketConnection(snapshot) {
  const table = $("market-timeframe-table");
  table.textContent = "";
  if (!snapshot) {
    setText("market-connection-status", "LOCAL MARKET API UNAVAILABLE");
    setText("market-connection-summary", "The synthetic dashboard remains available. No live value is displayed.");
    return;
  }
  setText("market-connection-status", `${snapshot.connection_status} · ${snapshot.reason_code}`);
  setText("market-mode", snapshot.connector_mode);
  setText("market-requested-symbol", snapshot.requested_symbol);
  setText("market-resolved-symbol", snapshot.resolved_symbol);
  setText("market-candidates", snapshot.candidate_symbols.length ? snapshot.candidate_symbols.join(", ") : "None");
  setText("market-retrieval-time", snapshot.retrieval_timestamp_utc);
  setText("market-freshness", `${snapshot.data_quality.freshness_status} · ${snapshot.data_quality.market_session_status}`);
  setText("market-connection-summary", snapshot.data_quality.diagnostic);
  const tick = snapshot.tick;
  const specification = snapshot.symbol_specification;
  setText("market-source-time", tick ? tick.source_timestamp_utc : null);
  setText("market-bid", tick ? tick.bid : null);
  setText("market-ask", tick ? tick.ask : null);
  setText("market-spread", tick ? `${tick.spread_price} price · ${tick.spread_points ?? "unknown"} points` : null);
  setText("market-digits-point", specification ? `${specification.digits} / ${specification.point}` : null);
  setText("market-contract-size", specification ? specification.trade_contract_size : null);
  setText("market-volume-limits", specification ? `${specification.volume_minimum} / ${specification.volume_maximum} / ${specification.volume_step}` : null);
  setText("market-stop-levels", specification ? `${specification.stops_level} / ${specification.freeze_level}` : null);
  setText("market-reported-spread", specification ? specification.broker_reported_spread_points : null);
  ["M1", "M5", "H4", "D1"].forEach((timeframe) => {
    const item = snapshot.timeframe_series[timeframe];
    const tr = document.createElement("tr");
    cell(tr, timeframe);
    cell(tr, item ? item.status : "NOT REQUESTED");
    cell(tr, item ? item.bar_count : "—");
    cell(tr, item ? item.closed_bar_count : "—");
    cell(tr, item ? item.forming_bar_count : "—");
    cell(tr, item ? item.latest_source_timestamp_utc || "—" : "—");
    table.appendChild(tr);
  });
}

function externalSourceLink(url, title) {
  const link = document.createElement("a");
  link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer";
  link.textContent = title;
  return link;
}

function officialItemReference(record, label) {
  const container = document.createElement("span");
  if (record.source_url_availability_status === "GOVERNED_ITEM_LINK_AVAILABLE") {
    container.appendChild(externalSourceLink(record.source_url, label));
    return container;
  }
  const reason = record.source_url_reason_code || "SOURCE_ITEM_LINK_NOT_PROVIDED";
  container.className = "official-link-unavailable";
  container.textContent = `${label} — Official item link unavailable (${record.source_url_availability_status || "SOURCE_ENDPOINT_FALLBACK"}; ${reason})`;
  return container;
}

function operationalFreshnessLabel(record) {
  const confirmed = record.last_successfully_observed_timestamp_utc || "SOURCE_NOT_PROVIDED";
  if (record.operational_freshness_status === "NEWS_RECORD_STALE") {
    return `STALE — SOURCE UNAVAILABLE · ${record.latest_source_failure_reason || "NEWS_SOURCE_SCHEMA_INVALID"} · Last confirmed ${confirmed}`;
  }
  return `CURRENT · Last confirmed ${confirmed}`;
}

function clearRows(id) { $(id).textContent = ""; }
function unavailable(value) { return value == null ? "Unavailable — SOURCE_NOT_PROVIDED" : String(value); }

function renderOfficialNews(bundle) {
  ["news-loading-state", "news-disabled-state", "news-empty-state", "news-partial-state", "news-error-state", "news-persistence-state"].forEach((id) => { $(id).hidden = true; });
  clearRows("news-source-table"); clearRows("news-item-table"); clearRows("economic-event-table"); $("news-item-cards").textContent = "";
  if (!bundle || bundle.error) {
    setText("news-overall-status", "ERROR"); setText("news-reason-code", bundle ? bundle.error : "LOCAL_NEWS_API_UNAVAILABLE"); $("news-error-state").hidden = false; return;
  }
  const { health, sources, items, events } = bundle;
  setText("news-overall-status", health.status); setText("news-reason-code", health.reason_code);
  setText("news-cache-persistence", health.cache_persistence_status);
  setText("news-last-success", health.last_successful_retrieval_utc); setText("news-next-refresh", health.next_permitted_refresh_utc);
  if (!health.enabled) $("news-disabled-state").hidden = false;
  else if (health.status === "NEWS_PARTIAL") $("news-partial-state").hidden = false;
  else if (["NEWS_ALL_SOURCES_FAILED", "NEWS_CACHE_INVALID", "NEWS_CACHE_WRITE_FAILED", "NEWS_PROVIDER_CHANGED"].includes(health.status)) $("news-error-state").hidden = false;
  else if (!items.items.length && !events.events.length) $("news-empty-state").hidden = false;
  if (health.cache_persistence_status === "NEWS_CACHE_WRITE_FAILED") {
    const warning = $("news-persistence-state");
    warning.textContent = health.cache_persistence_diagnostic || "Local cache persistence failed. Current in-memory news updates were not persisted and may be lost after restart.";
    warning.hidden = false;
  }
  sources.sources.forEach((source) => {
    const tr = document.createElement("tr");
    cell(tr, source.source_id); cell(tr, source.publisher); cell(tr, source.country_or_region); cell(tr, source.currency_tags.join(", ")); cell(tr, source.health.status); cell(tr, source.health.last_success_timestamp_utc || "—");
    $("news-source-table").appendChild(tr);
  });
  items.items.forEach((item) => {
    const freshness = operationalFreshnessLabel(item);
    const card = document.createElement("article"); card.className = "news-card";
    if (item.operational_freshness_status === "NEWS_RECORD_STALE") card.classList.add("record-stale");
    const freshnessBadge = document.createElement("p"); freshnessBadge.className = item.operational_freshness_status === "NEWS_RECORD_STALE" ? "freshness-label freshness-stale" : "freshness-label freshness-fresh"; freshnessBadge.textContent = freshness; card.appendChild(freshnessBadge);
    card.appendChild(officialItemReference(item, item.title));
    const metadata = document.createElement("p"); metadata.textContent = `${item.publisher} · ${item.published_timestamp_utc || "Time not supplied"} · ${item.country_or_region} · ${item.currency_tags.join(", ")} · ${freshness}`; card.appendChild(metadata); $("news-item-cards").appendChild(card);
    const tr = document.createElement("tr"); cell(tr, item.published_timestamp_utc || "SOURCE_NOT_PROVIDED"); cell(tr, item.publisher);
    const titleCell = document.createElement("td"); titleCell.appendChild(officialItemReference(item, item.title)); tr.appendChild(titleCell);
    cell(tr, item.country_or_region); cell(tr, item.currency_tags.join(", ")); cell(tr, freshness); $("news-item-table").appendChild(tr);
  });
  events.events.forEach((event) => {
    const tr = document.createElement("tr");
    const utcLabel = event.scheduled_time_precision === "DATE_ONLY" ? `${event.scheduled_timestamp_utc} (DATE ONLY)` : event.scheduled_timestamp_utc;
    const localLabel = event.scheduled_time_precision === "DATE_ONLY" ? "Date only — local release time not provided" : new Date(event.scheduled_timestamp_utc).toLocaleString();
    cell(tr, utcLabel); cell(tr, localLabel);
    const eventCell = document.createElement("td"); eventCell.appendChild(officialItemReference(event, event.event_name)); tr.appendChild(eventCell);
    cell(tr, event.event_series_id);
    cell(tr, unavailable(event.actual)); cell(tr, unavailable(event.forecast)); cell(tr, unavailable(event.previous)); cell(tr, unavailable(event.importance)); cell(tr, operationalFreshnessLabel(event)); $("economic-event-table").appendChild(tr);
  });
}

async function loadOfficialNews() {
  try {
    const [health, sources, items, events] = await Promise.all([getJson("/api/news-health"), getJson("/api/news-sources"), getJson("/api/news-items"), getJson("/api/economic-events")]);
    return { health, sources, items, events };
  } catch (error) { return { error: error.message }; }
}

function wireTabs() {
  [["report-tab", "report-panel", "json-tab", "json-panel"], ["json-tab", "json-panel", "report-tab", "report-panel"]].forEach(([tab, panel, otherTab, otherPanel]) => $(tab).addEventListener("click", () => { $(tab).setAttribute("aria-selected", "true"); $(otherTab).setAttribute("aria-selected", "false"); $(panel).hidden = false; $(otherPanel).hidden = true; }));
}
function download(filename, content, type) { const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url); }
function wireDownloads() { $("download-json").addEventListener("click", () => download("TRL-R2-001-synthetic-result.json", `${JSON.stringify(state.result, null, 2)}\n`, "application/json;charset=utf-8")); $("download-markdown").addEventListener("click", () => download(state.report.filename, state.report.content, "text/markdown;charset=utf-8")); }

function renderAll() {
  renderOverview(state.result, state.market); renderPaperDesk(state.paper); renderTables(state.market, state.result); renderSignals(state.result, state.market); renderStrategyAndReports(state.result, state.report, state.version); renderRegistry(state.registry); renderMarketConnection(state.liveMarket); renderOfficialNews(state.news);
  chart("market-canvas", "market-tooltip", state.market.points, [{ key: "close", label: "Close", color: "#eef3f6", width: 2 }, { key: "fast_sma", label: "Fast SMA", color: "#36d1c4" }, { key: "slow_sma", label: "Slow SMA", color: "#67a6ff" }], { signals: true });
  chart("equity-canvas", "equity-tooltip", state.result.equity_curve, [{ key: "total_marked_equity", label: "Marked equity", color: "#36d1c4", width: 2 }]);
  chart("drawdown-canvas", "drawdown-tooltip", state.result.equity_curve, [{ key: "drawdown_pct", label: "Drawdown", color: "#ef6e72", format: (v) => `${number(v, 4)}%` }], { min: -15, max: 0, reference: -15, percent: true });
}

async function loadDashboard() {
  $("loading-state").hidden = false; $("error-state").hidden = true; $("dashboard-content").hidden = true;
  try {
    [state.result, state.market, state.report, state.version, state.registry, state.liveMarket, state.news, state.paper] = await Promise.all([getJson("/api/demo/result"), getJson("/api/demo/market-data"), getJson("/api/demo/report"), getJson("/api/version"), getJson("/api/strategy-registry"), getJson("/api/market-snapshot").catch(() => null), loadOfficialNews(), loadPaperDesk()]);
    renderAll(); $("loading-state").hidden = true; $("dashboard-content").hidden = false;
  } catch (error) { $("loading-state").hidden = true; $("error-state").hidden = false; setText("error-message", error.message); }
}

window.addEventListener("resize", () => state.charts.forEach(drawChart));
$("retry-button").addEventListener("click", loadDashboard); wireTabs(); wireDownloads(); loadDashboard();
