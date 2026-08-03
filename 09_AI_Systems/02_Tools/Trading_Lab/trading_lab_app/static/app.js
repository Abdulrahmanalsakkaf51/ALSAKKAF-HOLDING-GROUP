"use strict";

const state = { result: null, market: null, report: null, version: null, registry: null, liveMarket: null, news: null, paper: null, mode: null, signal: null, mt5: null, basket: null, marketIntelligence: null, marketDataFabric: null, scalping: null, charts: [] };
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

function renderModeStatus(mode) {
  if (!mode || mode.error) {
    setText("mode-current-badge", "UNAVAILABLE");
    setText("top-mode-badge", "MODE: UNAVAILABLE");
    return;
  }
  const badge = $("mode-current-badge");
  badge.textContent = mode.current_mode;
  badge.className = mode.current_mode === "OFF" ? "badge badge-neutral" : "badge badge-safe";
  setText("top-mode-badge", `MODE: ${mode.current_mode}`);
  setText("mode-broker-execution", mode.broker_execution_available ? "AVAILABLE" : "UNAVAILABLE");
  setText("mode-automated-trading", mode.automated_trading_available ? "AVAILABLE" : "UNAVAILABLE");
  setText("mode-live-arming", mode.live_arming_available ? "AVAILABLE" : "UNAVAILABLE");
  setText("mode-private-remote", mode.private_remote_access_available ? "AVAILABLE" : "UNAVAILABLE");

  const availableList = $("mode-available-list"); clearRows("mode-available-list");
  mode.available_modes.forEach((name) => {
    const li = document.createElement("li");
    li.textContent = name === mode.current_mode ? `${name} (current)` : name;
    availableList.appendChild(li);
  });

  const unavailableList = $("mode-unavailable-list"); clearRows("mode-unavailable-list");
  Object.keys(mode.unavailable_modes).sort().forEach((name) => {
    const li = document.createElement("li");
    li.textContent = `${name} — ${mode.unavailable_modes[name].join(", ")}`;
    unavailableList.appendChild(li);
  });

  const allCapabilities = new Set();
  Object.values(mode.capability_matrix).forEach((list) => list.forEach((cap) => allCapabilities.add(cap)));
  const granted = new Set(mode.current_capabilities);
  const table = $("mode-capability-table"); clearRows("mode-capability-table");
  Array.from(allCapabilities).sort().forEach((cap) => {
    const tr = document.createElement("tr");
    cell(tr, cap.replace(/_/g, " "));
    cell(tr, granted.has(cap) ? "YES" : "NO");
    table.appendChild(tr);
  });

  setText("mode-previous", mode.previous_mode || "None");
  setText("mode-last-event-type", mode.last_transition ? mode.last_transition.event_type : "None yet");
  const lastReason = mode.last_transition && mode.last_transition.payload
    ? mode.last_transition.payload.rejection_reason_code
    : null;
  setText("mode-last-reason", lastReason || "None");
  setText("mode-startup-diagnostic", mode.startup_diagnostic_code);
  setText("mode-persistence-status", mode.persistence_status);

  const warning = $("mode-startup-warning");
  if (mode.startup_diagnostic_code !== "OK") {
    warning.hidden = false;
    warning.textContent = `Startup recovered from an invalid or unsafe persisted mode (${mode.startup_diagnostic_code}). The application started in a safe mode.`;
  } else {
    warning.hidden = true;
  }
}

async function loadModeStatus() {
  try {
    return await getJson("/api/mode-status");
  } catch (error) { return { error: error.message }; }
}

function renderSignalIntelligence(bundle) {
  const badge = $("signal-availability-badge");
  if (!bundle || bundle.error || !bundle.status) {
    badge.textContent = "UNAVAILABLE"; badge.className = "badge badge-neutral";
    setText("signal-operating-mode", "—"); setText("signal-capability", "UNAVAILABLE");
    return;
  }
  const { status, registry, proposals } = bundle;
  badge.textContent = status.enabled ? "AVAILABLE" : "UNAVAILABLE";
  badge.className = status.enabled ? "badge badge-safe" : "badge badge-neutral";
  setText("signal-operating-mode", status.operating_mode);
  setText("signal-capability", status.signal_generation ? "AVAILABLE" : "UNAVAILABLE");
  setText("signal-startup-diagnostic", status.startup_diagnostic_code);
  setText("signal-persistence-status", status.persistence_status);

  const strategies = (registry && registry.strategies) || status.strategy_registry || [];
  const table = $("signal-strategy-table"); clearRows("signal-strategy-table");
  strategies.forEach((strategy) => {
    const tr = document.createElement("tr");
    cell(tr, strategy.strategy_id); cell(tr, strategy.strategy_version);
    cell(tr, strategy.enabled ? "YES" : "NO"); cell(tr, strategy.approval_status);
    table.appendChild(tr);
  });

  const empty = $("signal-proposal-empty");
  const detail = $("signal-proposal-detail");
  const roleTable = $("signal-role-table"); clearRows("signal-role-table");
  const list = (proposals && proposals.proposals) || [];
  if (!list.length) {
    empty.hidden = false; detail.hidden = true;
    return;
  }
  empty.hidden = true; detail.hidden = false;
  const proposal = list[list.length - 1];
  setText("signal-proposal-side", proposal.side);
  setText("signal-proposal-instrument", proposal.instrument);
  setText("signal-proposal-strategy", `${proposal.strategy_id} v${proposal.strategy_version}`);
  const executable = proposal.side === "BUY" || proposal.side === "SELL";
  setText("signal-proposal-entry", executable ? `${proposal.entry_zone_lower} – ${proposal.entry_zone_upper}` : "n/a");
  setText("signal-proposal-stop", executable ? proposal.stop_loss : "n/a");
  setText("signal-proposal-targets", executable && proposal.targets ? proposal.targets.join(" / ") : "n/a");
  setText("signal-proposal-candidate-quantity", proposal.candidate_quantity ?? "n/a");
  setText("signal-proposal-independent-quantity", proposal.independent_quantity ?? "n/a");
  setText("signal-proposal-confidence", `${proposal.confidence_score} — ${proposal.confidence_status} (heuristic research value, not a win probability or profit forecast, never used for position size)`);
  setText("signal-proposal-sample-label", proposal.sample_label);
  setText("signal-proposal-news-status", proposal.news_event_risk_result ? proposal.news_event_risk_result.status : "—");
  setText("signal-proposal-evidence-status", proposal.evidence_quality_status);
  setText("signal-proposal-blocked-reason", proposal.side === "BLOCKED" ? proposal.rejection_reasons.join(", ") : "None");

  const roleResults = proposal.role_results || {};
  Object.keys(roleResults).sort().forEach((role) => {
    const tr = document.createElement("tr");
    const result = roleResults[role];
    cell(tr, role.replace(/_/g, " "));
    cell(tr, result.status);
    cell(tr, (result.reasons || []).join(", ") || "—");
    roleTable.appendChild(tr);
  });
}

async function loadSignalIntelligence() {
  try {
    const [status, registry, proposals] = await Promise.all([
      getJson("/api/signal-status"), getJson("/api/signal-strategy-registry"), getJson("/api/signal-proposals"),
    ]);
    return { status, registry, proposals };
  } catch (error) { return { error: error.message }; }
}

function renderMt5Execution(bundle) {
  const badge = $("mt5-availability-badge");
  if (!bundle || bundle.error || !bundle.status) {
    badge.textContent = "UNAVAILABLE"; badge.className = "badge badge-neutral";
    setText("mt5-operating-mode", "—"); setText("mt5-adapter-tier", "—");
    setText("mt5-dependency", "—"); setText("mt5-fingerprint-configured", "—");
    return;
  }
  const { status, account, journal } = bundle;
  badge.textContent = status.enabled ? "AVAILABLE (DEMO ONLY)" : "UNAVAILABLE";
  badge.className = status.enabled ? "badge badge-warning" : "badge badge-neutral";
  setText("mt5-operating-mode", status.operating_mode);
  setText("mt5-adapter-tier", status.adapter_tier);
  setText("mt5-dependency", status.dependency && status.dependency.available ? "AVAILABLE" : "UNAVAILABLE");
  setText("mt5-fingerprint-configured", status.account_fingerprint_configured ? "CONFIGURED" : "NOT CONFIGURED (external blocker)");

  const terminal = (bundle.terminal) || {};
  setText("mt5-terminal-connected", terminal.connected ? "YES" : "NO");
  setText("mt5-terminal-trade-allowed", terminal.trade_allowed ? "YES" : "NO");
  setText("mt5-account-login", (account && account.login_redacted) || "—");
  setText("mt5-account-trade-mode", (account && account.trade_mode_name) || "—");

  const empty = $("mt5-journal-empty");
  const detail = $("mt5-journal-detail");
  const events = (journal && journal.events) || [];
  if (!events.length) {
    empty.hidden = false; detail.hidden = true;
    return;
  }
  empty.hidden = true; detail.hidden = false;
  const latest = events[events.length - 1];
  setText("mt5-journal-event-type", latest.event_type);
  setText("mt5-journal-event-time", latest.occurred_at_utc);
}

async function loadMt5Execution() {
  try {
    const [status, account, terminal, journal] = await Promise.all([
      getJson("/api/mt5-execution-status"), getJson("/api/mt5-account-status"),
      getJson("/api/mt5-terminal-status"), getJson("/api/execution-journal"),
    ]);
    return { status, account, terminal, journal };
  } catch (error) { return { error: error.message }; }
}

function renderBasketExecution(bundle) {
  const badge = $("basket-availability-badge");
  if (!bundle || bundle.error || !bundle.status) {
    badge.textContent = "UNAVAILABLE"; badge.className = "badge badge-neutral";
    setText("basket-operating-mode", "—"); setText("basket-capability-granted", "—"); setText("basket-count", "—");
    $("basket-list-table").replaceChildren();
    $("basket-detail-empty").hidden = false; $("basket-detail").hidden = true;
    return;
  }
  const { status, baskets } = bundle;
  badge.textContent = status.enabled ? "AVAILABLE (DEMO ONLY)" : "UNAVAILABLE";
  badge.className = status.enabled ? "badge badge-warning" : "badge badge-neutral";
  setText("basket-operating-mode", status.operating_mode);
  setText("basket-capability-granted", status.manual_basket_execution_granted ? "GRANTED" : "NOT GRANTED");

  const list = baskets || [];
  setText("basket-count", list.length);
  const listTable = $("basket-list-table");
  listTable.replaceChildren();
  list.forEach((basket) => {
    const tr = document.createElement("tr");
    cell(tr, basket.basket_id || "—");
    cell(tr, basket.basket_status || "—");
    cell(tr, basket.confirmation_status || "—");
    cell(tr, basket.found ? `${basket.filled_child_count} / ${basket.child_count}` : "—");
    cell(tr, basket.reconciliation_required ? "YES" : "NO");
    listTable.appendChild(tr);
  });

  const detailEmpty = $("basket-detail-empty");
  const detail = $("basket-detail");
  if (!list.length) {
    detailEmpty.hidden = false; detail.hidden = true;
    $("basket-children-table").replaceChildren();
    return;
  }
  detailEmpty.hidden = true; detail.hidden = false;
  const latest = list[list.length - 1];
  setText("basket-detail-id", latest.basket_id);
  setText("basket-detail-status", latest.basket_status);
  setText("basket-detail-confirmation-status", latest.confirmation_status);
  setText("basket-detail-cycle", latest.active_confirmation_cycle_number);
  setText("basket-detail-authorized-start", latest.authorized_start_child_id);
  setText("basket-detail-authorized-remaining", (latest.authorized_remaining_child_ids || []).join(", ") || "—");
  setText("basket-detail-live-next", latest.live_next_eligible_child_id);
  setText("basket-detail-completed-quantity", latest.completed_quantity);
  setText("basket-detail-remaining-quantity", latest.remaining_quantity);
  setText("basket-detail-filled-count", `${latest.filled_child_count} / ${latest.child_count}`);
  setText("basket-detail-reconciliation", latest.reconciliation_required ? "YES" : "NO");
  setText("basket-detail-terminal-reason", latest.terminal_reason);
  setText("basket-detail-rejection-reasons", (latest.rejection_reasons || []).join(", ") || "—");

  const childrenTable = $("basket-children-table");
  childrenTable.replaceChildren();
  (latest.children || []).forEach((child) => {
    const tr = document.createElement("tr");
    cell(tr, child.basket_child_id);
    cell(tr, child.target_price);
    cell(tr, child.target_allocation_percent);
    cell(tr, child.child_quantity);
    cell(tr, child.check_status || "—");
    cell(tr, child.check_fresh ? "YES" : "NO");
    cell(tr, child.send_status || "—");
    cell(tr, child.execution_state);
    childrenTable.appendChild(tr);
  });
}

async function loadBasketExecution() {
  try {
    const [status, basketsDoc] = await Promise.all([
      getJson("/api/basket-execution-status"), getJson("/api/execution-baskets"),
    ]);
    return { status, baskets: basketsDoc.baskets };
  } catch (error) { return { error: error.message }; }
}

function renderMarketIntelligence(bundle) {
  const badge = $("mi-availability-badge");
  if (!bundle || bundle.error || !bundle.status) {
    badge.textContent = "UNAVAILABLE"; badge.className = "badge badge-neutral";
    setText("mi-operating-mode", "—"); setText("mi-capability-granted", "—"); setText("mi-opportunity-count", "—");
    $("mi-opportunity-table").replaceChildren();
    $("mi-detail-empty").hidden = false; $("mi-detail").hidden = true;
    $("mi-preview-empty").hidden = false; $("mi-preview-detail").hidden = true;
    $("mi-evidence-table").replaceChildren(); $("mi-lattice-table").replaceChildren(); $("mi-telemetry-table").replaceChildren();
    return;
  }
  const { status, opportunities, telemetry, detail: latestDetail } = bundle;
  badge.textContent = status.enabled ? "AVAILABLE (RESEARCH ONLY)" : "UNAVAILABLE";
  badge.className = status.enabled ? "badge badge-warning" : "badge badge-neutral";
  setText("mi-operating-mode", status.operating_mode);
  setText("mi-capability-granted", status.market_intelligence_research_granted ? "GRANTED" : "NOT GRANTED");

  const list = opportunities || [];
  setText("mi-opportunity-count", list.length);
  const listTable = $("mi-opportunity-table");
  listTable.replaceChildren();
  list.forEach((opportunity) => {
    const tr = document.createElement("tr");
    cell(tr, opportunity.opportunity_id || "—");
    cell(tr, `${opportunity.instrument || "—"} / ${opportunity.timeframe || "—"}`);
    cell(tr, opportunity.proposed_side || "—");
    cell(tr, opportunity.decision_status || "—");
    cell(tr, opportunity.market_regime || "—");
    listTable.appendChild(tr);
  });

  const detailEmpty = $("mi-detail-empty");
  const detail = $("mi-detail");
  const previewEmpty = $("mi-preview-empty");
  const previewDetail = $("mi-preview-detail");
  const evidenceTable = $("mi-evidence-table");
  const latticeTable = $("mi-lattice-table");
  evidenceTable.replaceChildren();
  latticeTable.replaceChildren();
  if (!list.length) {
    detailEmpty.hidden = false; detail.hidden = true;
    previewEmpty.hidden = false; previewDetail.hidden = true;
  } else {
    detailEmpty.hidden = true; detail.hidden = false;
    const latest = list[list.length - 1];
    setText("mi-detail-id", latest.opportunity_id);
    setText("mi-detail-status", latest.decision_status);
    setText("mi-detail-reasons", (latest.decision_reason_codes || []).join(", ") || "—");
    setText("mi-detail-supporting", latest.supporting_score);
    setText("mi-detail-contradiction", latest.contradiction_score);
    setText("mi-detail-uncertainty", latest.uncertainty_score);
    setText("mi-detail-data-quality", latest.data_quality_score);
    setText("mi-detail-cost", latest.estimated_cost_score);
    setText("mi-detail-event-risk", latest.event_risk_score);
    setText("mi-detail-risk-exposure", latest.risk_exposure_score);

    ((latestDetail && latestDetail.virtual_opportunities) || []).slice().sort((a, b) => a.rank - b.rank).forEach((vop) => {
      const tr = document.createElement("tr");
      cell(tr, vop.rank); cell(tr, vop.state);
      cell(tr, vop.hypothetical_entry_trigger); cell(tr, vop.stop);
      cell(tr, vop.expected_reward_risk_ratio);
      cell(tr, "—");
      latticeTable.appendChild(tr);
    });

    const supporting = ((latestDetail && latestDetail.decision && latestDetail.decision.supporting_evidence_ids) || []);
    const opposing = ((latestDetail && latestDetail.decision && latestDetail.decision.opposing_evidence_ids) || []);
    supporting.forEach((id) => { const tr = document.createElement("tr"); cell(tr, id); cell(tr, "SUPPORTS"); cell(tr, "—"); evidenceTable.appendChild(tr); });
    opposing.forEach((id) => { const tr = document.createElement("tr"); cell(tr, id); cell(tr, "OPPOSES"); cell(tr, "—"); evidenceTable.appendChild(tr); });

    const preview = latestDetail && latestDetail.preview;
    if (preview) {
      previewEmpty.hidden = true; previewDetail.hidden = false;
      setText("mi-preview-id", preview.preview_id);
      setText("mi-preview-non-executable", preview.non_executable ? "TRUE (NON-EXECUTABLE)" : "—");
      setText("mi-preview-handoff", preview.execution_handoff_status);
      setText("mi-preview-allocations", (preview.ordered_target_allocations || []).join(", ") || "—");
    } else {
      previewEmpty.hidden = false; previewDetail.hidden = true;
    }
  }
  const telemetryTable = $("mi-telemetry-table");
  telemetryTable.replaceChildren();
  (telemetry || []).forEach((record) => {
    const tr = document.createElement("tr");
    cell(tr, record.telemetry_id || "—");
    cell(tr, record.original_decision_status || "—");
    cell(tr, record.outcome_classification || "—");
    cell(tr, record.calibration_bucket || "—");
    telemetryTable.appendChild(tr);
  });
}

async function loadMarketIntelligence() {
  try {
    const [status, opportunitiesDoc, telemetryDoc] = await Promise.all([
      getJson("/api/market-intelligence-status"), getJson("/api/market-opportunities"), getJson("/api/market-intelligence-telemetry"),
    ]);
    const opportunities = opportunitiesDoc.opportunities || [];
    let detail = null;
    if (opportunities.length) {
      const latestId = opportunities[opportunities.length - 1].opportunity_id;
      detail = await getJson(`/api/market-opportunity/${encodeURIComponent(latestId)}`).catch(() => null);
    }
    return { status, opportunities, telemetry: telemetryDoc.telemetry, detail };
  } catch (error) { return { error: error.message }; }
}

function renderMarketDataFabric(bundle) {
  const badge = $("mdr-availability-badge");
  if (!bundle || bundle.error || !bundle.status) {
    badge.textContent = "UNAVAILABLE"; badge.className = "badge badge-neutral";
    setText("mdr-operating-mode", "—"); setText("mdr-capability-granted", "—");
    setText("mdr-dataset-count", "—"); setText("mdr-session-count", "—");
    $("mdr-dataset-table").replaceChildren(); $("mdr-session-table").replaceChildren();
    return;
  }
  const { status, datasets, sessions } = bundle;
  badge.textContent = status.enabled ? "AVAILABLE (RESEARCH ONLY)" : "UNAVAILABLE";
  badge.className = status.enabled ? "badge badge-warning" : "badge badge-neutral";
  setText("mdr-operating-mode", status.operating_mode);
  setText("mdr-capability-granted", status.market_data_research_granted ? "GRANTED" : "NOT GRANTED");
  setText("mdr-dataset-count", status.dataset_count);
  setText("mdr-session-count", status.replay_session_count);

  const datasetTable = $("mdr-dataset-table");
  datasetTable.replaceChildren();
  (datasets || []).forEach((dataset) => {
    const tr = document.createElement("tr");
    cell(tr, dataset.dataset_id || "—");
    cell(tr, `${dataset.instrument || "—"} / ${dataset.timeframe || "—"}`);
    cell(tr, dataset.source_classification || "—");
    cell(tr, dataset.source_reference || "—");
    cell(tr, dataset.bar_count ?? "—");
    cell(tr, `${dataset.first_observed_at_utc || "—"} → ${dataset.last_observed_at_utc || "—"}`);
    cell(tr, dataset.gap_count ?? "—");
    cell(tr, dataset.largest_gap_intervals ?? "—");
    cell(tr, dataset.canonical_dataset_hash || "—");
    datasetTable.appendChild(tr);
  });

  const sessionTable = $("mdr-session-table");
  sessionTable.replaceChildren();
  (sessions || []).forEach((session) => {
    const tr = document.createElement("tr");
    const snapshot = session.latest_snapshot;
    cell(tr, session.replay_session_id || "—");
    cell(tr, session.status || "—");
    cell(tr, session.current_index ?? "—");
    cell(tr, snapshot ? `${snapshot.window_start_index}–${snapshot.window_end_index}` : "—");
    cell(tr, snapshot ? String(snapshot.non_live) : "—");
    cell(tr, snapshot ? String(snapshot.non_executable) : "—");
    sessionTable.appendChild(tr);
  });
}

async function loadMarketDataFabric() {
  try {
    const [status, datasetsDoc, sessionsDoc] = await Promise.all([
      getJson("/api/market-data-status"), getJson("/api/market-datasets"), getJson("/api/replay-sessions"),
    ]);
    return { status, datasets: datasetsDoc.datasets, sessions: sessionsDoc.replay_sessions };
  } catch (error) { return { error: error.message }; }
}

async function loadScalping() {
  try {
    const [status, cycles, orders, positions, journal] = await Promise.all([
      getJson("/api/scalping-status"), getJson("/api/scalping-cycles"),
      getJson("/api/scalping-owned-orders"), getJson("/api/scalping-owned-positions"),
      getJson("/api/scalping-journal"),
    ]);
    return { status, cycles: cycles.cycles, orders: orders.owned_orders, positions: positions.owned_positions, journal: journal.events };
  } catch (error) { return { error: error.message }; }
}

async function postScalping(path, body) {
  const token = state.scalping && state.scalping.status ? state.scalping.status.action_token : null;
  const response = await fetch(path, {
    method: "POST", cache: "no-store", credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-Scalping-Action-Token": token || "" },
    body: JSON.stringify(body || {}),
  });
  const document_ = await response.json();
  if (!response.ok) throw new Error(document_.error || `${path} returned HTTP ${response.status}`);
  return document_;
}

function renderScalping(bundle) {
  const stateBadge = $("scalping-state-badge");
  const automationBadge = $("scalping-automation-badge");
  const emergencyBadge = $("scalping-emergency-badge");
  if (!bundle || bundle.error) {
    stateBadge.textContent = "UNAVAILABLE";
    automationBadge.textContent = "AUTOMATION STATUS: UNAVAILABLE";
    emergencyBadge.textContent = "EMERGENCY STOP: UNKNOWN";
    return;
  }
  const { status, cycles, orders, positions, journal } = bundle;
  stateBadge.textContent = status.product_state;
  automationBadge.textContent = `AUTOMATION STATUS: ${status.product_state}`;
  emergencyBadge.textContent = status.emergency_stop_active ? "EMERGENCY STOP: ACTIVE" : "EMERGENCY STOP: INACTIVE";
  const profileEntries = Object.entries(status.profiles || {});
  setText("scalping-profile", profileEntries.length ? profileEntries.map(([symbol, profile]) => `${symbol}: ${profile}`).join(", ") : "—");
  setText("scalping-mt5-connection", status.journal_startup_diagnostic_code === "OK" ? "OK" : status.journal_startup_diagnostic_code);
  setText("scalping-demo-verified", "—");
  setText("scalping-equity", "—");
  setText("scalping-daily-pnl", "—");
  setText("scalping-decision", "—");

  const cycleTable = $("scalping-cycle-table");
  cycleTable.replaceChildren();
  (cycles || []).forEach((cycle) => {
    const tr = document.createElement("tr");
    [cycle.cycle_id, cycle.canonical_instrument, cycle.profile_id, cycle.state].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = escapeText(value);
      tr.appendChild(td);
    });
    cycleTable.appendChild(tr);
  });

  const ordersTable = $("scalping-orders-table");
  ordersTable.replaceChildren();
  (orders || []).forEach((order) => {
    const tr = document.createElement("tr");
    [order.ticket, order.symbol].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = escapeText(value);
      tr.appendChild(td);
    });
    ordersTable.appendChild(tr);
  });

  const positionsTable = $("scalping-positions-table");
  positionsTable.replaceChildren();
  (positions || []).forEach((position) => {
    const tr = document.createElement("tr");
    [position.ticket, position.symbol].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = escapeText(value);
      tr.appendChild(td);
    });
    positionsTable.appendChild(tr);
  });

  const journalList = $("scalping-journal-list");
  journalList.replaceChildren();
  (journal || []).slice(-20).reverse().forEach((event) => {
    const li = document.createElement("li");
    li.textContent = `${event.occurred_at_utc} · ${event.event_type}`;
    journalList.appendChild(li);
  });
}

function wireScalpingControls() {
  const resultLine = $("scalping-control-result");
  const bind = (id, path, body) => {
    $(id).addEventListener("click", async () => {
      resultLine.textContent = "Working...";
      try {
        const document_ = await postScalping(path, body);
        resultLine.textContent = `OK: ${JSON.stringify(document_)}`;
        state.scalping = await loadScalping();
        renderScalping(state.scalping);
      } catch (error) {
        resultLine.textContent = `REJECTED: ${error.message}`;
      }
    });
  };
  bind("scalping-btn-start", "/api/scalping-start-demo-auto");
  bind("scalping-btn-pause", "/api/scalping-pause");
  bind("scalping-btn-resume", "/api/scalping-resume");
  bind("scalping-btn-emergency-stop", "/api/scalping-emergency-stop");
  bind("scalping-btn-emergency-reset", "/api/scalping-emergency-reset");
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
  renderOverview(state.result, state.market); renderModeStatus(state.mode); renderSignalIntelligence(state.signal); renderMt5Execution(state.mt5); renderBasketExecution(state.basket); renderMarketIntelligence(state.marketIntelligence); renderMarketDataFabric(state.marketDataFabric); renderScalping(state.scalping); renderPaperDesk(state.paper); renderTables(state.market, state.result); renderSignals(state.result, state.market); renderStrategyAndReports(state.result, state.report, state.version); renderRegistry(state.registry); renderMarketConnection(state.liveMarket); renderOfficialNews(state.news);
  chart("market-canvas", "market-tooltip", state.market.points, [{ key: "close", label: "Close", color: "#eef3f6", width: 2 }, { key: "fast_sma", label: "Fast SMA", color: "#36d1c4" }, { key: "slow_sma", label: "Slow SMA", color: "#67a6ff" }], { signals: true });
  chart("equity-canvas", "equity-tooltip", state.result.equity_curve, [{ key: "total_marked_equity", label: "Marked equity", color: "#36d1c4", width: 2 }]);
  chart("drawdown-canvas", "drawdown-tooltip", state.result.equity_curve, [{ key: "drawdown_pct", label: "Drawdown", color: "#ef6e72", format: (v) => `${number(v, 4)}%` }], { min: -15, max: 0, reference: -15, percent: true });
}

async function loadDashboard() {
  $("loading-state").hidden = false; $("error-state").hidden = true; $("dashboard-content").hidden = true;
  try {
    [state.result, state.market, state.report, state.version, state.registry, state.liveMarket, state.news, state.paper, state.mode, state.signal, state.mt5, state.basket, state.marketIntelligence, state.marketDataFabric, state.scalping] = await Promise.all([getJson("/api/demo/result"), getJson("/api/demo/market-data"), getJson("/api/demo/report"), getJson("/api/version"), getJson("/api/strategy-registry"), getJson("/api/market-snapshot").catch(() => null), loadOfficialNews(), loadPaperDesk(), loadModeStatus(), loadSignalIntelligence(), loadMt5Execution(), loadBasketExecution(), loadMarketIntelligence(), loadMarketDataFabric(), loadScalping()]);
    renderAll(); $("loading-state").hidden = true; $("dashboard-content").hidden = false;
  } catch (error) { $("loading-state").hidden = true; $("error-state").hidden = false; setText("error-message", error.message); }
}

window.addEventListener("resize", () => state.charts.forEach(drawChart));
$("retry-button").addEventListener("click", loadDashboard); wireTabs(); wireDownloads(); wireScalpingControls(); loadDashboard();
