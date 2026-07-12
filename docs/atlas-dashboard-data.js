// Atlas CEO Dashboard — local static data file.
// No external calls, no analytics, no tracking, no secrets. Edit values by hand as real data comes in.

const atlasDashboardData = {
  // Mission
  founderMission: "Convert AOS into real revenue, starting with AI Services.",

  // Revenue
  revenueTargetNote: "Planning reference only (STRAT-005): first 30-day target revenue is $7,500-equivalent. Not a guarantee.",
  revenueCollected: 0, // USD
  paymentsReceived: 0,

  // Offer
  activeOffer: "AOS AI Workflow Starter Pack — $399 USD",
  paymentLink: "https://www.paypal.com/ncp/payment/2AN8FH99X682C",
  paymentLinkStatus: "Active — only approved link",
  currency: "USD",

  // Leads
  leadsFound: 0,
  leadsQualified: 0,

  // Outreach
  outreachDrafted: 0,
  outreachSent: 0,

  // Content
  contentDrafted: 0,
  contentPublished: 0,

  // Website
  websiteStatus: "Built, not yet published — see docs/README.md",

  // Partner tasks
  activePartners: [
    "Atlas — CEO command, planning, lead scoring, reporting, task routing",
    "The Librarian — indexing, knowledge retrieval, filing, document classification",
    "Guardian — security, compliance, credential protection, risk review"
  ],
  proposedPartners: "Marketing, Content, Reporting, Ecommerce, Finance, and Legal/Compliance Partners are proposed only — not active.",

  // CEO decisions pending
  ceoDecisions: [
    "Choose contact email",
    "Approve landing page copy",
    "Approve first outreach batch"
  ],

  // Risks
  risks: [
    "No revenue is guaranteed.",
    "No real leads are loaded yet.",
    "Website is built locally but not yet published."
  ],

  // Next actions
  nextActions: [
    "Approve landing page",
    "Choose contact email",
    "Publish website",
    "Fill first 25 leads",
    "Approve outreach template"
  ]
};

function renderAtlasDashboard(data) {
  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  };

  const setList = (id, items) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = "";
    items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      el.appendChild(li);
    });
  };

  setText("founder-mission", data.founderMission);
  setText("revenue-target-note", data.revenueTargetNote);
  setText("revenue-collected", "$" + data.revenueCollected);
  setText("payments-received", data.paymentsReceived);
  setText("active-offer", data.activeOffer);
  setText("payment-link", data.paymentLink);
  setText("payment-link-status", data.paymentLinkStatus);
  setText("leads-found", data.leadsFound);
  setText("leads-qualified", data.leadsQualified);
  setText("outreach-drafted", data.outreachDrafted);
  setText("outreach-sent", data.outreachSent);
  setText("content-drafted", data.contentDrafted);
  setText("content-published", data.contentPublished);
  setText("website-status", data.websiteStatus);

  setList("active-partners-list", data.activePartners);
  setText("proposed-partners-note", data.proposedPartners);
  setList("ceo-decisions-list", data.ceoDecisions);
  setList("risks-list", data.risks);
  setList("next-actions-list", data.nextActions);
}

document.addEventListener("DOMContentLoaded", function () {
  renderAtlasDashboard(atlasDashboardData);
});
