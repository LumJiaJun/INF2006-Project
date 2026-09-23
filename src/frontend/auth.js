"use strict";

const authConfig = window.AUTH_CONFIG;
const sessionKeys = {
  verifier: "auth.pkce_verifier",
  state: "auth.oauth_state",
  idToken: "auth.id_token",
  expiresAt: "auth.expires_at",
};

function base64Url(bytes) {
  return btoa(String.fromCharCode(...bytes))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}

function randomValue(length = 32) {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return base64Url(bytes);
}

async function sha256(value) {
  const bytes = new TextEncoder().encode(value);
  return new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
}

function decodeJwtPayload(token) {
  try {
    const encoded = token.split(".")[1].replaceAll("-", "+").replaceAll("_", "/");
    const payload = encoded.padEnd(encoded.length + ((4 - (encoded.length % 4)) % 4), "=");
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}

function clearSession() {
  Object.values(sessionKeys).forEach((key) => sessionStorage.removeItem(key));
}

function getIdToken() {
  const token = sessionStorage.getItem(sessionKeys.idToken);
  const expiresAt = Number(sessionStorage.getItem(sessionKeys.expiresAt));
  if (!token || !expiresAt || Date.now() >= expiresAt) {
    clearSession();
    return null;
  }
  return token;
}

function getUser() {
  const token = getIdToken();
  if (!token) {
    return null;
  }
  const payload = decodeJwtPayload(token);
  return payload ? { email: payload.email, subject: payload.sub } : null;
}

async function signIn() {
  // PKCE keeps the authorization code unusable without this browser's verifier.
  const state = randomValue();
  const verifier = randomValue(64);
  const challenge = base64Url(await sha256(verifier));
  sessionStorage.setItem(sessionKeys.state, state);
  sessionStorage.setItem(sessionKeys.verifier, verifier);

  const parameters = new URLSearchParams({
    response_type: "code",
    client_id: authConfig.clientId,
    redirect_uri: authConfig.redirectUri,
    scope: "openid email profile",
    state,
    code_challenge_method: "S256",
    code_challenge: challenge,
  });
  location.assign(`${authConfig.domain}/oauth2/authorize?${parameters}`);
}

function signOut() {
  clearSession();
  const parameters = new URLSearchParams({
    client_id: authConfig.clientId,
    logout_uri: authConfig.logoutUri,
  });
  location.assign(`${authConfig.domain}/logout?${parameters}`);
}

async function exchangeCode(code) {
  const verifier = sessionStorage.getItem(sessionKeys.verifier);
  if (!verifier) {
    throw new Error("The sign-in verifier is missing. Please sign in again.");
  }
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: authConfig.clientId,
    code,
    redirect_uri: authConfig.redirectUri,
    code_verifier: verifier,
  });
  const response = await fetch(`${authConfig.domain}/oauth2/token`, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!response.ok) {
    throw new Error("The sign-in code could not be exchanged.");
  }
  const tokens = await response.json();
  sessionStorage.setItem(sessionKeys.idToken, tokens.id_token);
  sessionStorage.setItem(
    sessionKeys.expiresAt,
    String(Date.now() + Number(tokens.expires_in) * 1000 - 30_000),
  );
  sessionStorage.removeItem(sessionKeys.state);
  sessionStorage.removeItem(sessionKeys.verifier);
}

async function initialize() {
  if (!authConfig) {
    return;
  }
  const parameters = new URLSearchParams(location.search);
  const code = parameters.get("code");
  const returnedState = parameters.get("state");
  const error = parameters.get("error_description") || parameters.get("error");
  if (error) {
    history.replaceState({}, document.title, location.pathname);
    throw new Error(error);
  }
  if (!code) {
    return;
  }
  const expectedState = sessionStorage.getItem(sessionKeys.state);
  // Reject callbacks that do not belong to the sign-in request started in this tab.
  if (!expectedState || returnedState !== expectedState) {
    clearSession();
    throw new Error("The sign-in state did not match. Please sign in again.");
  }
  await exchangeCode(code);
  history.replaceState({}, document.title, location.pathname);
}

window.Auth = Object.freeze({
  ready: initialize(),
  getIdToken,
  getUser,
  signIn,
  signOut,
});
