"use strict";

const menuToggle = document.querySelector("#menu-toggle");
const primaryNav = document.querySelector("#primary-nav");
const accountLabel = document.querySelector("#account-label");
const signInButton = document.querySelector("#sign-in");
const signOutButton = document.querySelector("#sign-out");

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

function updateAccountControls() {
  const user = window.Auth.getUser();
  if (accountLabel) accountLabel.textContent = user?.email || "Not signed in";
  if (signInButton) signInButton.hidden = Boolean(user);
  if (signOutButton) signOutButton.hidden = !user;
}

signInButton?.addEventListener("click", () => window.Auth.signIn());
signOutButton?.addEventListener("click", () => window.Auth.signOut());

window.Auth.ready
  .then(updateAccountControls)
  .catch((error) => {
    if (accountLabel) accountLabel.textContent = error.message;
  });

updateAccountControls();
