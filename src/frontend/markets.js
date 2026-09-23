"use strict";

const marketGrid = document.querySelector("#market-page-grid");
const marketStatus = document.querySelector("#market-page-status");
const marketSort = document.querySelector("#market-page-sort");
const regionButtons = [...document.querySelectorAll("#region-filters button")];
const apiBaseUrl = window.APP_CONFIG?.apiBaseUrl;
let markets = [];
let activeRegion = "All";

const cityDetails = {
  Bangkok: { region: "Asia-Pacific", note: "A high-volume tropical capital with broad neighbourhood variety." },
  "Cape Town": { region: "Africa", note: "Coastal stays, mountain districts, and strong historical guest ratings." },
  "Hong Kong": { region: "Asia-Pacific", note: "A compact, vertical market shaped by dense urban neighbourhoods." },
  Istanbul: { region: "Europe", note: "A large cross-continental market with deep listing coverage." },
  "Mexico City": { region: "Americas", note: "A diverse metropolitan market with consistently strong ratings." },
  "New York": { region: "Americas", note: "A mature, high-volume urban market spanning distinct borough contexts." },
  Paris: { region: "Europe", note: "The dataset's largest city market, with extensive neighbourhood coverage." },
  "Rio de Janeiro": { region: "Americas", note: "A coastal city market with highly rated historical listings." },
  Rome: { region: "Europe", note: "A heritage-led European market with broad central-city supply." },
  Sydney: { region: "Asia-Pacific", note: "A large harbour city market with balanced coverage and ratings." },
};

function sortedMarkets(items) {
  const sorted = [...items];
  if (marketSort.value === "listings") {
    return sorted.sort((first, second) => second.listing_count - first.listing_count);
  }
  if (marketSort.value === "median") {
    return sorted.sort((first, second) => second.median_nightly_price - first.median_nightly_price);
  }
  if (marketSort.value === "rating") {
    return sorted.sort((first, second) => (second.average_rating ?? 0) - (first.average_rating ?? 0));
  }
  return sorted.sort((first, second) => first.city.localeCompare(second.city));
}

function marketCard(item) {
  const details = cityDetails[item.city] || { region: "Global", note: "A supported city market in the project dataset." };
  const article = document.createElement("article");
  article.className = "directory-card";

  const heading = document.createElement("div");
  heading.className = "directory-card-heading";
  const region = document.createElement("span");
  region.textContent = details.region;
  const city = document.createElement("h3");
  city.textContent = item.city;
  heading.append(region, city);

  const note = document.createElement("p");
  note.textContent = details.note;

  const metrics = document.createElement("div");
  metrics.className = "directory-card-metrics";
  const metricValues = [
    [`${item.currency} ${item.median_nightly_price.toLocaleString()}`, "median night"],
    [item.listing_count.toLocaleString(), "listings"],
    [item.average_rating === null ? "N/A" : item.average_rating.toFixed(1), "rating / 100"],
  ];
  metricValues.forEach(([value, label]) => {
    const metric = document.createElement("span");
    const metricValue = document.createElement("strong");
    metricValue.textContent = value;
    metric.append(metricValue, label);
    metrics.append(metric);
  });

  const link = document.createElement("a");
  link.href = `index.html?city=${encodeURIComponent(item.city)}#estimator`;
  link.textContent = "Estimate this market";
  link.className = "directory-card-link";
  article.append(heading, note, metrics, link);
  return article;
}

function renderMarkets() {
  const filtered = markets.filter((item) => {
    return activeRegion === "All" || cityDetails[item.city]?.region === activeRegion;
  });
  marketGrid.replaceChildren(...sortedMarkets(filtered).map(marketCard));
  marketStatus.textContent = `${filtered.length} ${filtered.length === 1 ? "market" : "markets"} shown. Prices remain in local currency.`;
}

// Load the same governed summaries used by the estimator dashboard.
async function loadMarkets() {
  if (!apiBaseUrl) {
    marketStatus.textContent = "The analytics configuration is unavailable.";
    return;
  }
  try {
    const response = await fetch(`${apiBaseUrl}/analytics`, { headers: { accept: "application/json" } });
    if (!response.ok) {
      throw new Error("Market summaries could not be loaded.");
    }
    const result = await response.json();
    markets = result.items;
    renderMarkets();
  } catch (error) {
    marketStatus.textContent = error.message;
  }
}

marketSort.addEventListener("change", renderMarkets);
regionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activeRegion = button.dataset.region;
    regionButtons.forEach((item) => item.classList.toggle("is-active", item === button));
    renderMarkets();
  });
});

loadMarkets();
