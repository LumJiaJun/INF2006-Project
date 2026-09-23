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
    const response = await fetch(`${apiBaseUrl}/predict`, {
      method: "POST",
      headers: { "content-type": "application/json" },
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
    disclaimer.textContent = result.disclaimer;
    content.append(price, disclaimer);
    showPredictionResult(content);
  } catch (error) {
    const message = document.createElement("span");
    message.textContent = error.message || "The prediction service is unavailable.";
    showPredictionResult(message, true);
  } finally {
    predictionSubmit.disabled = false;
    predictionSubmit.textContent = "Estimate nightly price";
  }
});

loadModelOptions().catch((error) => {
  console.error("Model options failed to load", error);
  predictionSubmit.disabled = true;
  const message = document.createElement("span");
  message.textContent = "The estimator configuration is unavailable.";
  showPredictionResult(message, true);
});
