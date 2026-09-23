"use strict";

document.documentElement.dataset.application = "airbnb-market-intelligence";

const statusMessage = document.querySelector("#status-message");
const statusIndicator = document.querySelector("#status-indicator");
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
const historySection = document.querySelector("#history-section");
const historyMessage = document.querySelector("#history-message");
const historyList = document.querySelector("#history-list");
const refreshHistoryButton = document.querySelector("#refresh-history");
const analyticsMessage = document.querySelector("#analytics-message");
const analyticsGrid = document.querySelector("#analytics-grid");

async function checkPlatformHealth() {
  if (!apiBaseUrl) {
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

    statusMessage.textContent = "Frontend, API Gateway, and Lambda are responding normally.";
    statusIndicator.classList.remove("status-indicator-pending");
  } catch (error) {
    console.error("Platform health check failed", error);
    statusMessage.textContent = "The API health check is currently unavailable.";
    statusIndicator.classList.remove("status-indicator-pending");
    statusIndicator.classList.add("status-indicator-error");
  }
}

checkPlatformHealth();

function analyticsItem(item) {
  const card = document.createElement("article");
  const city = document.createElement("h3");
  city.textContent = item.city;
  const median = document.createElement("strong");
  median.textContent = `${item.currency} ${item.median_nightly_price.toLocaleString()}`;
  const medianLabel = document.createElement("span");
  medianLabel.textContent = "median nightly price";
  const details = document.createElement("p");
  const rating = item.average_rating === null ? "not available" : item.average_rating.toFixed(1);
  details.textContent = `${item.listing_count.toLocaleString()} listings, average rating ${rating}/100`;
  card.append(city, median, medianLabel, details);
  return card;
}

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
    analyticsGrid.replaceChildren(...result.items.map(analyticsItem));
    analyticsMessage.textContent = `${result.scope}. Prices use each city's local currency.`;
  } catch (error) {
    analyticsMessage.textContent = error.message;
  }
}

loadAnalytics();

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
}

async function loadModelOptions() {
  const response = await fetch("model-options.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Model options could not be loaded");
  }
  modelOptions = await response.json();
  populateSelect(citySelect, modelOptions.cities.map((city) => city.name));
  populateSelect(propertyTypeSelect, modelOptions.property_types);
  populateSelect(roomTypeSelect, modelOptions.room_types);
  updateCityFields();
}

function numericFormValue(formData, field, optional = false) {
  const value = formData.get(field);
  if (optional && value === "") {
    return null;
  }
  return Number(value);
}

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

function showPredictionResult(content, isError = false) {
  predictionResult.replaceChildren(content);
  predictionResult.hidden = false;
  predictionResult.classList.toggle("prediction-result-error", isError);
}

citySelect.addEventListener("change", updateCityFields);

predictionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  predictionSubmit.disabled = true;
  predictionSubmit.textContent = "Estimating...";

  try {
    const idToken = window.Auth.getIdToken();
    const route = idToken ? "predictions" : "predict";
    const headers = { "content-type": "application/json" };
    if (idToken) {
      headers.authorization = `Bearer ${idToken}`;
    }
    const response = await fetch(`${apiBaseUrl}/${route}`, {
      method: "POST",
      headers,
      body: JSON.stringify(predictionPayload(predictionForm)),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error?.message || "Prediction failed");
    }

    const content = document.createElement("div");
    const price = document.createElement("strong");
    price.className = "prediction-price";
    price.textContent = `${result.currency} ${result.estimated_nightly_price.toLocaleString()}`;
    const disclaimer = document.createElement("span");
    disclaimer.textContent = result.saved
      ? `${result.disclaimer} This estimate was saved to your history.`
      : result.disclaimer;
    content.append(price, disclaimer);
    showPredictionResult(content);
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

window.Auth.ready.then(updateAccountUi).catch((error) => {
  accountLabel.textContent = error.message;
});

loadModelOptions().catch((error) => {
  console.error("Model options failed to load", error);
  predictionSubmit.disabled = true;
  const message = document.createElement("span");
  message.textContent = "The estimator configuration is unavailable.";
  showPredictionResult(message, true);
});
