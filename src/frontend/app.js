"use strict";

document.documentElement.dataset.application = "airbnb-market-intelligence";

const statusMessage = document.querySelector("#status-message");
const statusIndicator = document.querySelector("#status-indicator");
const apiBaseUrl = window.APP_CONFIG?.apiBaseUrl;

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
