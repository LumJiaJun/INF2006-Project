"use strict";

document.documentElement.dataset.application = "airbnb-market-intelligence";

const statusMessage = document.querySelector("#status-message");
const statusIndicator = document.querySelector("#status-indicator");
const platformStatusHeading = document.querySelector("#platform-status-heading");
const apiBaseUrl = window.APP_CONFIG?.apiBaseUrl;
const predictionForm = document.querySelector("#prediction-form");
const predictionResult = document.querySelector("#prediction-result");
const predictionSubmit = document.querySelector("#prediction-submit");
const citySelect = document.querySelector("#city");
const neighbourhoodSelect = document.querySelector("#neighbourhood");
const propertyTypeSelect = document.querySelector("#property-type");
const roomTypeSelect = document.querySelector("#room-type");
const latitudeInput = document.querySelector("#latitude");
const longitudeInput = document.querySelector("#longitude");
let modelOptions;
const accountLabel = document.querySelector("#account-label");
const signInButton = document.querySelector("#sign-in");
const signOutButton = document.querySelector("#sign-out");
const menuToggle = document.querySelector("#menu-toggle");
const primaryNav = document.querySelector("#primary-nav");
const historySection = document.querySelector("#history-section");
const historyMessage = document.querySelector("#history-message");
const historyList = document.querySelector("#history-list");
const refreshHistoryButton = document.querySelector("#refresh-history");
const analyticsMessage = document.querySelector("#analytics-message");
const analyticsGrid = document.querySelector("#analytics-grid");
const analyticsSort = document.querySelector("#analytics-sort");
const analyticsSearch = document.querySelector("#analytics-search");
const marketResultCount = document.querySelector("#market-result-count");
const spotlightCity = document.querySelector("#spotlight-city");
const spotlightDescription = document.querySelector("#spotlight-description");
const spotlightMedian = document.querySelector("#spotlight-median");
const spotlightListings = document.querySelector("#spotlight-listings");
const spotlightRating = document.querySelector("#spotlight-rating");
const useMarketButton = document.querySelector("#use-market");
const heroCityCount = document.querySelector("#hero-city-count");
const presetButtons = [...document.querySelectorAll(".preset-button")];
const snapshotLocation = document.querySelector("#snapshot-location");
const snapshotStay = document.querySelector("#snapshot-stay");
const snapshotSpace = document.querySelector("#snapshot-space");
const snapshotSignals = document.querySelector("#snapshot-signals");
const readinessLabel = document.querySelector("#readiness-label");
const readinessBar = document.querySelector("#readiness-bar");
const readinessDetail = document.querySelector("#readiness-detail");
const saveDraftButton = document.querySelector("#save-draft");
const restoreDraftButton = document.querySelector("#restore-draft");
const clearDraftButton = document.querySelector("#clear-draft");
const draftStatus = document.querySelector("#draft-status");
const draftStorageKey = "airbnb-market-intelligence-listing-draft";
const stayPlanner = document.querySelector("#stay-planner");
const plannerCheckin = document.querySelector("#planner-checkin");
const plannerCheckout = document.querySelector("#planner-checkout");
const plannerSummary = document.querySelector("#planner-summary");
const scenarioComparison = document.querySelector("#scenario-comparison");
const scenarioComparisonList = document.querySelector("#scenario-comparison-list");
const scenarioComparisonNote = document.querySelector("#scenario-comparison-note");
const clearScenariosButton = document.querySelector("#clear-scenarios");
const scenarioStorageKey = "airbnb-market-intelligence-scenarios";
let plannerRate = null;
let plannerCurrency = "";
let analyticsItems = [];
let selectedMarket = null;
let lastPredictionScenario = null;
let comparisonScenarios = [];

function closeNavigation() {
  if (!menuToggle || !primaryNav) return;
  menuToggle.setAttribute("aria-expanded", "false");
  primaryNav.classList.remove("is-open");
}

menuToggle?.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!isOpen));
  primaryNav?.classList.toggle("is-open", !isOpen);
});

primaryNav?.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeNavigation));

const presets = {
  starter: {
    accommodates: 2,
    bedrooms: 1,
    minimum_nights: 2,
    review_scores_rating: "",
    host_total_listings_count: 0,
    amenities_count: 8,
    instant_bookable: false,
    host_is_superhost: false,
    host_identity_verified: false,
  },
  couple: {
    accommodates: 2,
    bedrooms: 1,
    minimum_nights: 2,
    review_scores_rating: 95,
    host_total_listings_count: 1,
    amenities_count: 8,
    instant_bookable: false,
    host_is_superhost: false,
    host_identity_verified: true,
  },
  family: {
    accommodates: 4,
    bedrooms: 2,
    minimum_nights: 3,
    review_scores_rating: 93,
    host_total_listings_count: 1,
    amenities_count: 12,
    instant_bookable: false,
    host_is_superhost: false,
    host_identity_verified: true,
  },
  premium: {
    accommodates: 2,
    bedrooms: 1,
    minimum_nights: 2,
    review_scores_rating: 98,
    host_total_listings_count: 2,
    amenities_count: 18,
    instant_bookable: true,
    host_is_superhost: true,
    host_identity_verified: true,
  },
};

// Check the public health route so visitors can see whether the platform is ready.
async function checkPlatformHealth() {
  if (!apiBaseUrl) {
    platformStatusHeading.textContent = "Configuration unavailable";
    statusMessage.textContent = "The API configuration is not available.";
    statusIndicator.classList.add("status-indicator-error");
    return;
  }

  try {
    const response = await fetch(`${apiBaseUrl}/health`, {
      headers: { accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Health request returned HTTP ${response.status}`);
    }

    const result = await response.json();
    if (result.status !== "healthy") {
      throw new Error("Health response was not healthy");
    }

    platformStatusHeading.textContent = "Services online";
    statusMessage.textContent = "Frontend, API Gateway, and Lambda are responding normally.";
    statusIndicator.classList.remove("status-indicator-pending");
  } catch (error) {
    console.error("Platform health check failed", error);
    platformStatusHeading.textContent = "Service check unavailable";
    statusMessage.textContent = "The API health check is currently unavailable.";
    statusIndicator.classList.remove("status-indicator-pending");
    statusIndicator.classList.add("status-indicator-error");
  }
}

checkPlatformHealth();

function selectMarket(item) {
  selectedMarket = item;
  spotlightCity.textContent = item.city;
  spotlightDescription.textContent = `Explore ${item.city}'s historical listing profile before preparing an estimate.`;
  spotlightMedian.textContent = `${item.currency} ${item.median_nightly_price.toLocaleString()}`;
  spotlightListings.textContent = item.listing_count.toLocaleString();
  spotlightRating.textContent =
    item.average_rating === null ? "Not available" : `${item.average_rating.toFixed(1)}/100`;
  useMarketButton.disabled = false;
  document.querySelectorAll(".market-card").forEach((card) => {
    card.classList.toggle("is-selected", card.dataset.city === item.city);
  });
}

function analyticsItem(item) {
  const card = document.createElement("button");
  card.className = "market-card";
  card.type = "button";
  card.dataset.city = item.city;
  card.setAttribute("aria-label", `View ${item.city} market details`);
  const city = document.createElement("h3");
  city.textContent = item.city;
  const image = document.createElement("img");
  image.className = "market-card-image";
  image.src = marketImageFor(item.city);
  image.alt = `${item.city} market context`;
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.src = "assets/global-markets.webp";
  }, { once: true });
  const median = document.createElement("strong");
  median.textContent = `${item.currency} ${item.median_nightly_price.toLocaleString()}`;
  const medianLabel = document.createElement("span");
  medianLabel.textContent = "median nightly price";
  const details = document.createElement("p");
  const rating = item.average_rating === null ? "not available" : item.average_rating.toFixed(1);
  const shape = item.average_to_median_ratio === null
    ? "not available"
    : `${item.average_to_median_ratio.toFixed(2)}x`;
  const capacityAssociation = item.capacity_price_correlation === null
    ? "not available"
    : `r=${item.capacity_price_correlation.toFixed(2)}`;
  details.textContent = `${item.listing_count.toLocaleString()} listings, average rating ${rating}/100, average-to-median ${shape}, capacity-price association ${capacityAssociation}`;
  card.append(image, city, median, medianLabel, details);
  card.addEventListener("click", () => selectMarket(item));
  return card;
}

// Use repository-owned images and fall back to a known local asset.
function marketImageFor(city) {
  return city.length % 2 === 0 ? "assets/terrace-analytics.webp" : "assets/global-markets.webp";
}

function sortedAnalyticsItems() {
  const query = analyticsSearch.value.trim().toLocaleLowerCase();
  const items = analyticsItems.filter((item) => item.city.toLocaleLowerCase().includes(query));
  if (analyticsSort.value === "listings") {
    return items.sort((first, second) => second.listing_count - first.listing_count);
  }
  if (analyticsSort.value === "median") {
    return items.sort((first, second) => second.median_nightly_price - first.median_nightly_price);
  }
  if (analyticsSort.value === "rating") {
    return items.sort((first, second) => (second.average_rating ?? 0) - (first.average_rating ?? 0));
  }
  return items.sort((first, second) => first.city.localeCompare(second.city));
}

function renderAnalytics() {
  const items = sortedAnalyticsItems();
  marketResultCount.textContent = `${items.length} of ${analyticsItems.length} markets shown`;
  if (!items.length) {
    const emptyState = document.createElement("p");
    emptyState.className = "market-empty-state";
    emptyState.textContent = "No supported market matches that search.";
    analyticsGrid.replaceChildren(emptyState);
    return;
  }
  analyticsGrid.replaceChildren(...items.map(analyticsItem));
  if (selectedMarket) {
    selectMarket(selectedMarket);
  }
}

// Load approved city summaries and choose a useful default market.
async function loadAnalytics() {
  try {
    const response = await fetch(`${apiBaseUrl}/analytics`, {
      headers: { accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error("Market analytics could not be loaded.");
    }
    const result = await response.json();
    // Currency labels remain visible because city prices cannot be compared as one currency.
    analyticsItems = result.items;
    heroCityCount.textContent = analyticsItems.length.toLocaleString();
    selectedMarket = analyticsItems.find((item) => item.city === "Paris") || analyticsItems[0] || null;
    renderAnalytics();
    if (selectedMarket) {
      selectMarket(selectedMarket);
    }
    analyticsMessage.textContent = `${result.scope}. Prices use each city's local currency.`;
  } catch (error) {
    analyticsMessage.textContent = error.message;
  }
}

loadAnalytics();

analyticsSort.addEventListener("change", renderAnalytics);
analyticsSearch.addEventListener("input", renderAnalytics);

useMarketButton.addEventListener("click", () => {
  if (!selectedMarket || !modelOptions) {
    return;
  }
  citySelect.value = selectedMarket.city;
  updateCityFields();
  document.querySelector("#estimator").scrollIntoView({ behavior: "smooth", block: "start" });
  citySelect.focus({ preventScroll: true });
});

function applyPreset(name) {
  const preset = presets[name];
  if (!preset) {
    return;
  }
  Object.entries(preset).forEach(([fieldName, value]) => {
    const field = predictionForm.elements.namedItem(fieldName);
    if (field.type === "checkbox") {
      field.checked = value;
    } else {
      field.value = value;
    }
  });
  presetButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.preset === name);
  });
  updateListingSnapshot();
}

presetButtons.forEach((button) => {
  button.addEventListener("click", () => applyPreset(button.dataset.preset));
});

function populateSelect(select, values) {
  select.replaceChildren(
    ...values.map((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      return option;
    }),
  );
}

function selectedCity() {
  return modelOptions.cities.find((city) => city.name === citySelect.value);
}

function updateCityFields() {
  const city = selectedCity();
  if (!city) {
    return;
  }
  populateSelect(neighbourhoodSelect, city.neighbourhoods);
  latitudeInput.min = city.coordinate_range.latitude.minimum;
  latitudeInput.max = city.coordinate_range.latitude.maximum;
  longitudeInput.min = city.coordinate_range.longitude.minimum;
  longitudeInput.max = city.coordinate_range.longitude.maximum;
  latitudeInput.value = (
    (city.coordinate_range.latitude.minimum + city.coordinate_range.latitude.maximum) /
    2
  ).toFixed(5);
  longitudeInput.value = (
    (city.coordinate_range.longitude.minimum + city.coordinate_range.longitude.maximum) /
    2
  ).toFixed(5);
  updateListingSnapshot();
  updateEstimatorReadiness();
}

// Keep a concise listing summary visible while the user adjusts model inputs.
function updateListingSnapshot() {
  const formData = new FormData(predictionForm);
  const city = formData.get("city") || "Selected market";
  const neighbourhood = formData.get("neighbourhood");
  const guests = Number(formData.get("accommodates")) || 0;
  const bedrooms = Number(formData.get("bedrooms")) || 0;
  const signals = [];

  if (formData.has("host_is_superhost")) {
    signals.push("Superhost");
  }
  if (formData.has("instant_bookable")) {
    signals.push("Instant book");
  }
  if (formData.has("host_identity_verified")) {
    signals.push("Identity verified");
  }

  snapshotLocation.textContent = neighbourhood ? `${neighbourhood}, ${city}` : city;
  snapshotStay.textContent = `${guests} guest${guests === 1 ? "" : "s"}, ${bedrooms} bedroom${bedrooms === 1 ? "" : "s"}`;
  snapshotSpace.textContent = formData.get("room_type") || "Select a room type";
  snapshotSignals.textContent = signals.length ? signals.join(" + ") : "No host signals selected";
}

// Show which estimator sections are complete before the user requests a model estimate.
function updateEstimatorReadiness() {
  const sections = {
    market: ["city", "neighbourhood", "property_type", "room_type", "latitude", "longitude"],
    listing: [
      "accommodates",
      "minimum_nights",
      "host_total_listings_count",
      "amenities_count",
    ],
    host: ["host_identity_verified", "host_is_superhost", "instant_bookable"],
  };
  const completedSections = Object.entries(sections).filter(([section, fields]) => {
    if (section === "host") {
      return fields.some((fieldName) => predictionForm.elements.namedItem(fieldName).checked);
    }
    return fields.every((fieldName) => predictionForm.elements.namedItem(fieldName).checkValidity());
  });
  const completedCount = completedSections.length;

  document.querySelectorAll(".form-progress [data-step]").forEach((step) => {
    if (step.dataset.step === "compare") return;
    step.classList.toggle("is-complete", completedSections.some(([name]) => name === step.dataset.step));
  });
  readinessBar.style.width = `${(completedCount / 3) * 100}%`;
  readinessLabel.textContent = completedCount === 3 ? "Ready to estimate" : `${completedCount} of 3 sections ready`;
  readinessDetail.textContent =
    completedCount === 3
      ? "All required inputs are complete. You can request a model estimate."
      : "Complete the highlighted sections to prepare a complete estimate.";
}

// Keep only the current listing form values in local browser storage for a later visit.
function listingDraft() {
  return Array.from(predictionForm.elements)
    .filter((field) => field.name)
    .reduce((draft, field) => {
      draft[field.name] = field.type === "checkbox" ? field.checked : field.value;
      return draft;
    }, {});
}

function storedDraft() {
  try {
    const draft = window.localStorage.getItem(draftStorageKey);
    return draft ? JSON.parse(draft) : null;
  } catch (error) {
    console.warn("Listing draft could not be read", error);
    return null;
  }
}

function updateDraftControls(message) {
  const hasDraft = Boolean(storedDraft());
  restoreDraftButton.disabled = !hasDraft;
  clearDraftButton.disabled = !hasDraft;
  draftStatus.textContent = message || (hasDraft ? "A listing draft is saved on this device." : "No draft saved on this device.");
}

function restoreListingDraft() {
  const draft = storedDraft();
  if (!draft) {
    updateDraftControls();
    return;
  }
  if (typeof draft.city === "string" && Array.from(citySelect.options).some((option) => option.value === draft.city)) {
    citySelect.value = draft.city;
    updateCityFields();
  }
  Object.entries(draft).forEach(([name, value]) => {
    if (name === "city") {
      return;
    }
    const field = predictionForm.elements.namedItem(name);
    if (!field || (field.tagName === "SELECT" && !Array.from(field.options).some((option) => option.value === value))) {
      return;
    }
    if (field.type === "checkbox") {
      field.checked = value === true;
    } else {
      field.value = value;
    }
  });
  updateCityFields();
  updateListingSnapshot();
  updateEstimatorReadiness();
  updateDraftControls("Draft restored. Review it before estimating.");
}

saveDraftButton.addEventListener("click", () => {
  try {
    window.localStorage.setItem(draftStorageKey, JSON.stringify(listingDraft()));
    updateDraftControls("Draft saved in this browser. It is not sent to the platform.");
  } catch (error) {
    console.warn("Listing draft could not be saved", error);
    draftStatus.textContent = "This browser could not save a draft.";
  }
});

restoreDraftButton.addEventListener("click", restoreListingDraft);

clearDraftButton.addEventListener("click", () => {
  try {
    window.localStorage.removeItem(draftStorageKey);
    updateDraftControls("Browser draft cleared.");
  } catch (error) {
    console.warn("Listing draft could not be cleared", error);
    draftStatus.textContent = "This browser could not clear the draft.";
  }
});

async function loadModelOptions() {
  const response = await fetch("model-options.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Model options could not be loaded");
  }
  modelOptions = await response.json();
  populateSelect(citySelect, modelOptions.cities.map((city) => city.name));
  populateSelect(propertyTypeSelect, modelOptions.property_types);
  populateSelect(roomTypeSelect, modelOptions.room_types);
  const requestedCity = new URLSearchParams(window.location.search).get("city");
  if (requestedCity && modelOptions.cities.some((city) => city.name === requestedCity)) {
    citySelect.value = requestedCity;
  }
  updateCityFields();
  updateDraftControls();
}

function numericFormValue(formData, field, optional = false) {
  const value = formData.get(field);
  if (optional && value === "") {
    return null;
  }
  return Number(value);
}

// Convert form controls into the exact schema expected by the prediction API.
function predictionPayload(form) {
  const formData = new FormData(form);
  return {
    city: formData.get("city"),
    neighbourhood: formData.get("neighbourhood"),
    property_type: formData.get("property_type"),
    room_type: formData.get("room_type"),
    latitude: numericFormValue(formData, "latitude"),
    longitude: numericFormValue(formData, "longitude"),
    accommodates: numericFormValue(formData, "accommodates"),
    bedrooms: numericFormValue(formData, "bedrooms", true),
    minimum_nights: numericFormValue(formData, "minimum_nights"),
    review_scores_rating: numericFormValue(formData, "review_scores_rating", true),
    host_total_listings_count: numericFormValue(formData, "host_total_listings_count"),
    amenities_count: numericFormValue(formData, "amenities_count"),
    instant_bookable: formData.has("instant_bookable"),
    host_is_superhost: formData.has("host_is_superhost"),
    host_identity_verified: formData.has("host_identity_verified"),
  };
}

function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function requestPrediction(route, headers, payload, onWarmup) {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    const response = await fetch(`${apiBaseUrl}/${route}`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (attempt === 0 && [502, 503, 504].includes(response.status)) {
      onWarmup?.();
      await wait(1500);
      continue;
    }
    if (!response.ok) {
      throw new Error(result.error?.message || "Prediction failed");
    }
    return result;
  }
  throw new Error("The prediction model is still warming up. Please try again shortly.");
}

function buildWhatIfPanel(baselinePayload, baselineResult) {
  const panel = document.createElement("section");
  panel.className = "what-if-panel";
  const heading = document.createElement("strong");
  heading.textContent = "Predictive what-if analysis";
  const note = document.createElement("p");
  note.textContent = "Change one supported input and rerun the same model. This is scenario analysis, not a future-price forecast.";
  const actions = document.createElement("div");
  actions.className = "what-if-actions";
  const output = document.createElement("p");
  output.className = "what-if-output";
  output.textContent = "Choose one change to compare with this estimate.";
  const scenarios = [
    {
      label: "+5 amenities",
      change: (payload) => {
        payload.amenities_count = Math.min(200, payload.amenities_count + 5);
      },
    },
    {
      label: "+1 guest",
      change: (payload) => {
        payload.accommodates = Math.min(16, payload.accommodates + 1);
      },
    },
    {
      label: "Toggle superhost",
      change: (payload) => {
        payload.host_is_superhost = !payload.host_is_superhost;
      },
    },
  ];
  scenarios.forEach((scenario) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = scenario.label;
    button.addEventListener("click", async () => {
      const scenarioPayload = { ...baselinePayload };
      scenario.change(scenarioPayload);
      Array.from(actions.children).forEach((action) => {
        action.disabled = true;
      });
      output.textContent = `Testing ${scenario.label.toLowerCase()}...`;
      try {
        const result = await requestPrediction(
          "predict",
          { "content-type": "application/json" },
          scenarioPayload,
          () => {
            output.textContent = "The model is warming up. Retrying this scenario once...";
          },
        );
        const difference = result.estimated_nightly_price - baselineResult.estimated_nightly_price;
        const direction = difference >= 0 ? "above" : "below";
        output.textContent = `${scenario.label}: ${result.currency} ${result.estimated_nightly_price.toLocaleString()} (${result.currency} ${Math.abs(difference).toLocaleString(undefined, { maximumFractionDigits: 2 })} ${direction} this estimate).`;
      } catch (error) {
        output.textContent = error.message || "This scenario could not be estimated.";
      } finally {
        Array.from(actions.children).forEach((action) => {
          action.disabled = false;
        });
      }
    });
    actions.append(button);
  });
  panel.append(heading, note, actions, output);
  return panel;
}

function showPredictionResult(content, isError = false) {
  predictionResult.replaceChildren(content);
  predictionResult.hidden = false;
  predictionResult.classList.toggle("prediction-result-error", isError);
}

function loadComparisonScenarios() {
  try {
    const stored = JSON.parse(window.localStorage.getItem(scenarioStorageKey) || "[]");
    comparisonScenarios = Array.isArray(stored) ? stored.slice(0, 3) : [];
  } catch (error) {
    console.warn("Comparison scenarios could not be loaded", error);
    comparisonScenarios = [];
  }
}

function saveComparisonScenarios() {
  try {
    window.localStorage.setItem(scenarioStorageKey, JSON.stringify(comparisonScenarios));
    return true;
  } catch (error) {
    console.warn("Comparison scenarios could not be saved", error);
    scenarioComparisonNote.textContent = "This browser could not save the comparison.";
    return false;
  }
}

function scenarioDifference(scenario) {
  const baseline = comparisonScenarios[0];
  if (!baseline || baseline.id === scenario.id) return "Comparison baseline";
  if (baseline.currency !== scenario.currency) return "Different local currency; no direct price difference shown";
  const difference = scenario.price - baseline.price;
  const direction = difference >= 0 ? "above" : "below";
  return `${scenario.currency} ${Math.abs(difference).toLocaleString(undefined, { maximumFractionDigits: 2 })} ${direction} baseline`;
}

function renderScenarioComparison() {
  scenarioComparison.hidden = comparisonScenarios.length === 0;
  document.querySelector('[data-step="compare"]')?.classList.toggle(
    "is-complete",
    comparisonScenarios.length > 0,
  );
  if (!comparisonScenarios.length) {
    scenarioComparisonList.replaceChildren();
    return;
  }

  scenarioComparisonNote.textContent = `${comparisonScenarios.length} of 3 browser-local scenarios saved. Direct differences are shown only when currencies match.`;
  const cards = comparisonScenarios.map((scenario) => {
    const card = document.createElement("article");
    card.className = "scenario-card";
    const location = document.createElement("span");
    location.className = "scenario-location";
    location.textContent = `${scenario.neighbourhood}, ${scenario.city}`;
    const price = document.createElement("strong");
    price.textContent = `${scenario.currency} ${Number(scenario.price).toLocaleString()}`;
    const details = document.createElement("p");
    details.textContent = `${scenario.propertyType} | ${scenario.roomType} | ${scenario.guests} guests | ${scenario.bedrooms ?? "Unknown"} bedrooms | ${scenario.amenities} amenities`;
    const difference = document.createElement("span");
    difference.className = "scenario-difference";
    difference.textContent = scenarioDifference(scenario);
    const remove = document.createElement("button");
    remove.className = "scenario-remove";
    remove.type = "button";
    remove.dataset.scenarioId = scenario.id;
    remove.textContent = "Remove";
    card.append(location, price, details, difference, remove);
    return card;
  });
  scenarioComparisonList.replaceChildren(...cards);
}

function addCurrentScenario() {
  if (!lastPredictionScenario) return;
  const previousScenarios = [...comparisonScenarios];
  if (comparisonScenarios.length >= 3) comparisonScenarios.shift();
  comparisonScenarios.push(lastPredictionScenario);
  if (!saveComparisonScenarios()) comparisonScenarios = previousScenarios;
  renderScenarioComparison();
}

scenarioComparisonList.addEventListener("click", (event) => {
  const scenarioId = event.target.closest("[data-scenario-id]")?.dataset.scenarioId;
  if (!scenarioId) return;
  comparisonScenarios = comparisonScenarios.filter((scenario) => scenario.id !== scenarioId);
  saveComparisonScenarios();
  renderScenarioComparison();
});

clearScenariosButton.addEventListener("click", () => {
  comparisonScenarios = [];
  window.localStorage.removeItem(scenarioStorageKey);
  renderScenarioComparison();
});

function updateStayPlanner() {
  if (!plannerCheckin.value || !plannerCheckout.value || plannerRate === null) {
    plannerSummary.textContent = "Choose dates to calculate an indicative stay total.";
    return;
  }
  const checkin = new Date(`${plannerCheckin.value}T00:00:00Z`);
  const checkout = new Date(`${plannerCheckout.value}T00:00:00Z`);
  const nights = Math.round((checkout - checkin) / 86400000);
  if (nights <= 0) {
    plannerSummary.textContent = "Check-out must be after check-in.";
    return;
  }
  const total = plannerRate * nights;
  plannerSummary.textContent = `${nights} night${nights === 1 ? "" : "s"} x ${plannerCurrency} ${plannerRate.toLocaleString()} estimated nightly rate = ${plannerCurrency} ${total.toLocaleString(undefined, { maximumFractionDigits: 2 })}. Taxes, fees, availability, and currency conversion are not included.`;
}

plannerCheckin.addEventListener("change", updateStayPlanner);
plannerCheckout.addEventListener("change", updateStayPlanner);

citySelect.addEventListener("change", updateCityFields);
predictionForm.addEventListener("input", updateListingSnapshot);
predictionForm.addEventListener("change", updateListingSnapshot);
predictionForm.addEventListener("input", updateEstimatorReadiness);
predictionForm.addEventListener("change", updateEstimatorReadiness);

// A failed save keeps its key so resubmitting the same form cannot create a duplicate history record.
let pendingSave = null;

function idempotencyKeyFor(payload) {
  const fingerprint = JSON.stringify(payload);
  if (!pendingSave || pendingSave.fingerprint !== fingerprint) {
    pendingSave = { fingerprint, key: crypto.randomUUID() };
  }
  return pendingSave.key;
}

predictionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  predictionSubmit.disabled = true;
  predictionSubmit.textContent = "Estimating...";

  try {
    const idToken = window.Auth.getIdToken();
    const payload = predictionPayload(predictionForm);
    const route = idToken ? "predictions" : "predict";
    const headers = { "content-type": "application/json" };
    if (idToken) {
      headers.authorization = `Bearer ${idToken}`;
      headers["Idempotency-Key"] = idempotencyKeyFor(payload);
    }
    const result = await requestPrediction(route, headers, payload, () => {
      predictionSubmit.textContent = "Warming model and retrying...";
    });
    pendingSave = null;

    const content = document.createElement("div");
    const price = document.createElement("strong");
    price.className = "prediction-price";
    price.textContent = `${result.currency} ${result.estimated_nightly_price.toLocaleString()}`;
    const disclaimer = document.createElement("span");
    disclaimer.textContent = result.saved
      ? `${result.disclaimer} This estimate was saved to your history.`
      : result.disclaimer;
    const market = analyticsItems.find((item) => item.city === citySelect.value);
    if (market && market.median_nightly_price > 0) {
      const difference =
        ((result.estimated_nightly_price - market.median_nightly_price) /
          market.median_nightly_price) *
        100;
      const comparison = document.createElement("span");
      comparison.className = "prediction-comparison";
      comparison.textContent =
        Math.abs(difference) < 2
          ? `Close to the historical ${market.city} median.`
          : `${Math.abs(difference).toFixed(0)}% ${difference > 0 ? "above" : "below"} the historical ${market.city} median.`;
      const guidance = document.createElement("span");
      guidance.className = "prediction-guidance";
      if (difference > 15) {
        guidance.textContent = "Next step: verify that the listing's location, amenities, and host signals justify this above-median scenario, then compare a simpler configuration.";
      } else if (difference < -15) {
        guidance.textContent = "Next step: check that every listing feature is complete and compare a stronger-amenity scenario before setting a price.";
      } else {
        guidance.textContent = "Next step: use this near-median scenario as a baseline and compare one feature change at a time.";
      }
      content.append(price, comparison, guidance, disclaimer);
    } else {
      content.append(price, disclaimer);
    }
    lastPredictionScenario = {
      id: crypto.randomUUID(),
      city: payload.city,
      neighbourhood: payload.neighbourhood,
      propertyType: payload.property_type,
      roomType: payload.room_type,
      guests: payload.accommodates,
      bedrooms: payload.bedrooms,
      amenities: payload.amenities_count,
      price: result.estimated_nightly_price,
      currency: result.currency,
    };
    const compareButton = document.createElement("button");
    compareButton.className = "scenario-add";
    compareButton.type = "button";
    compareButton.textContent = "Add estimate to comparison";
    compareButton.addEventListener(
      "click",
      () => {
        addCurrentScenario();
        compareButton.disabled = true;
        compareButton.textContent = "Added to comparison";
      },
      { once: true },
    );
    content.append(buildWhatIfPanel(payload, result), compareButton);
    showPredictionResult(content);
    plannerRate = result.estimated_nightly_price;
    plannerCurrency = result.currency;
    stayPlanner.hidden = false;
    updateStayPlanner();
    if (result.saved) {
      await loadHistory();
    }
  } catch (error) {
    const message = document.createElement("span");
    message.textContent = error.message || "The prediction service is unavailable.";
    showPredictionResult(message, true);
  } finally {
    predictionSubmit.disabled = false;
    predictionSubmit.textContent = "Estimate nightly price";
  }
});

function updateAccountUi() {
  if (window.APP_CONFIG?.localMode) {
    accountLabel.textContent = "Local mode";
    signInButton.hidden = true;
    signOutButton.hidden = true;
    historySection.hidden = true;
    return;
  }
  const user = window.Auth.getUser();
  accountLabel.textContent = user?.email || "Not signed in";
  signInButton.hidden = Boolean(user);
  signOutButton.hidden = !user;
  historySection.hidden = !user;
  if (user) {
    loadHistory();
  } else {
    historyList.replaceChildren();
  }
}

function historyItem(record) {
  const item = document.createElement("article");
  item.className = "history-item";
  const title = document.createElement("span");
  title.textContent = `${record.city}, ${record.neighbourhood}`;
  const details = document.createElement("p");
  const createdAt = new Date(record.created_at).toLocaleString();
  details.textContent = `${record.room_type} for ${record.accommodates} guests, ${createdAt}`;
  const price = document.createElement("strong");
  price.textContent = `${record.currency} ${Number(record.predicted_price).toLocaleString()}`;
  item.append(title, details, price);
  return item;
}

async function loadHistory() {
  const idToken = window.Auth.getIdToken();
  if (!idToken) {
    return;
  }
  historyMessage.textContent = "Loading prediction history...";
  try {
    const response = await fetch(`${apiBaseUrl}/history`, {
      headers: { authorization: `Bearer ${idToken}` },
    });
    if (!response.ok) {
      throw new Error("Prediction history could not be loaded.");
    }
    const result = await response.json();
    historyList.replaceChildren(...result.items.map(historyItem));
    historyMessage.textContent = result.count
      ? `Showing ${result.count} most recent prediction${result.count === 1 ? "" : "s"}.`
      : "No saved predictions yet.";
  } catch (error) {
    historyMessage.textContent = error.message;
  }
}

signInButton.addEventListener("click", () => window.Auth.signIn());
signOutButton.addEventListener("click", () => window.Auth.signOut());
refreshHistoryButton.addEventListener("click", loadHistory);

window.Auth.ready
  .then(() => {
    updateAccountUi();
    const signInRequested = new URLSearchParams(window.location.search).get("signin") === "1";
    if (!window.APP_CONFIG?.localMode && signInRequested && !window.Auth.getUser()) {
      window.Auth.signIn();
    }
  })
  .catch((error) => {
    accountLabel.textContent = error.message;
  });

loadModelOptions().catch((error) => {
  console.error("Model options failed to load", error);
  predictionSubmit.disabled = true;
  const message = document.createElement("span");
  message.textContent = "The estimator configuration is unavailable.";
  showPredictionResult(message, true);
});

// Scenario comparisons stay on this device and never enter prediction history.
loadComparisonScenarios();
renderScenarioComparison();
