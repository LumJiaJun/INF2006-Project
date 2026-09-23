"use strict";

const currentPage = window.location.pathname.split("/").pop() || "index.html";

const pageGreetings = {
  "index.html": "I can help you build an estimate, understand the result, or find another page.",
  "markets.html": "I can explain the city summaries or carry a market into the estimator.",
  "project.html": "I can explain the cloud architecture, security, or model workflow.",
};

const guideAnswers = [
  {
    patterns: ["estimate", "prediction", "price", "model"],
    response:
      "The estimator sends your listing details to a trained scikit-learn pipeline in AWS Lambda. The result is a supported nightly-price estimate, not a guaranteed market price.",
    action: { label: "Open estimator", href: "index.html#estimator" },
  },
  {
    patterns: ["market", "city", "compare", "analytics"],
    response:
      "The market guide shows historical median prices, listing counts, and ratings for ten cities. Keep each city's currency local when reading the results.",
    action: { label: "View city guide", href: "markets.html" },
  },
  {
    patterns: ["sign", "account", "login", "register", "history"],
    response:
      "Use Sign in on the estimator page to open Cognito. New users can create an account, verify their email, and then save predictions to private history.",
    action: { label: "Go to sign in", href: "index.html?signin=1" },
  },
  {
    patterns: ["architecture", "aws", "cloud", "terraform", "serverless"],
    response:
      "The platform uses CloudFront, S3, API Gateway, Lambda, Cognito, DynamoDB, Glue, Athena, ECR, and CloudWatch. Terraform manages the deployed resources.",
    action: { label: "See architecture", href: "project.html#architecture-heading" },
  },
  {
    patterns: ["safe", "security", "private", "jwt"],
    response:
      "The S3 origins remain private, API history routes require Cognito JWTs, IAM permissions are scoped per service, and operational alerts are encrypted.",
    action: { label: "Read security overview", href: "project.html" },
  },
  {
    patterns: ["hello", "hi", "hey", "help"],
    response:
      "Hello. Ask me about estimates, city markets, sign-up, architecture, or security. You can also switch to Navigate for page shortcuts.",
  },
];

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) {
    element.className = className;
  }
  if (text) {
    element.textContent = text;
  }
  return element;
}

function buildGuide() {
  const launcher = createElement("button", "guide-launcher");
  launcher.type = "button";
  launcher.setAttribute("aria-label", "Open market guide");
  launcher.setAttribute("aria-expanded", "false");
  launcher.innerHTML = `
    <svg aria-hidden="true" viewBox="0 0 24 24" width="24" height="24">
      <path d="M5 5.75h14A2.25 2.25 0 0 1 21.25 8v7A2.25 2.25 0 0 1 19 17.25h-7.1l-4.65 3v-3H5A2.25 2.25 0 0 1 2.75 15V8A2.25 2.25 0 0 1 5 5.75Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
      <circle cx="8" cy="11.5" r="1" fill="currentColor"/>
      <circle cx="12" cy="11.5" r="1" fill="currentColor"/>
      <circle cx="16" cy="11.5" r="1" fill="currentColor"/>
    </svg>
    <span>Ask the guide</span>
    <i aria-hidden="true"></i>
  `;

  const panel = createElement("aside", "market-guide");
  panel.hidden = true;
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "Market intelligence guide");

  const header = createElement("header", "guide-header");
  const headingGroup = createElement("div");
  const kicker = createElement("span", "guide-kicker", "Market intelligence");
  const heading = createElement("h2", null, "How can I help?");
  headingGroup.append(kicker, heading);
  const closeButton = createElement("button", "guide-close", "Close");
  closeButton.type = "button";
  closeButton.setAttribute("aria-label", "Close market guide");
  header.append(headingGroup, closeButton);

  const tabs = createElement("div", "guide-tabs");
  tabs.setAttribute("role", "tablist");
  const chatTab = createElement("button", "is-active", "Chat");
  const navigateTab = createElement("button", null, "Navigate");
  [chatTab, navigateTab].forEach((tab, index) => {
    tab.type = "button";
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", index === 0 ? "true" : "false");
  });
  tabs.append(chatTab, navigateTab);

  const chatView = createElement("div", "guide-view guide-chat-view");
  const messages = createElement("div", "guide-messages");
  messages.setAttribute("aria-live", "polite");
  const quickReplies = createElement("div", "guide-quick-replies");
  ["How do estimates work?", "Compare city markets", "How do I sign up?"].forEach((prompt) => {
    const button = createElement("button", null, prompt);
    button.type = "button";
    quickReplies.append(button);
  });

  const form = createElement("form", "guide-form");
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "Ask about the platform";
  input.autocomplete = "off";
  input.maxLength = 160;
  input.setAttribute("aria-label", "Message the market guide");
  const sendButton = createElement("button", null, "Send");
  sendButton.type = "submit";
  form.append(input, sendButton);
  chatView.append(messages, quickReplies, form);

  const navigationView = createElement("nav", "guide-view guide-navigation-view");
  navigationView.hidden = true;
  navigationView.setAttribute("aria-label", "Page shortcuts");
  const pageLinks = [
    ["Estimator dashboard", "Build and save a nightly-price estimate.", "index.html#estimator", "01"],
    ["City market guide", "Filter and compare all ten supported markets.", "markets.html", "02"],
    ["Project story", "Explore the architecture, security, and stack.", "project.html", "03"],
  ];
  pageLinks.forEach(([title, description, href, number]) => {
    const link = createElement("a", "guide-page-link");
    link.href = href;
    const marker = createElement("span", null, number);
    const copy = createElement("div");
    copy.append(createElement("strong", null, title), createElement("small", null, description));
    link.append(marker, copy);
    navigationView.append(link);
  });

  panel.append(header, tabs, chatView, navigationView);
  document.body.append(panel, launcher);
  return { launcher, panel, closeButton, chatTab, navigateTab, chatView, navigationView, messages, quickReplies, form, input };
}

const guide = buildGuide();

function addMessage(text, sender, action) {
  const wrapper = createElement("div", `guide-message guide-message-${sender}`);
  wrapper.append(createElement("p", null, text));
  if (action) {
    const link = createElement("a", null, action.label);
    link.href = action.href;
    wrapper.append(link);
  }
  guide.messages.append(wrapper);
  guide.messages.scrollTop = guide.messages.scrollHeight;
}

function answerQuestion(question) {
  const normalized = question.toLowerCase();
  const answer = guideAnswers.find((item) => item.patterns.some((pattern) => normalized.includes(pattern)));
  window.setTimeout(() => {
    if (answer) {
      addMessage(answer.response, "guide", answer.action);
    } else {
      addMessage(
        "I am a lightweight site guide for now. Try asking about estimates, city markets, sign-up, architecture, or security.",
        "guide",
      );
    }
  }, 280);
}

function submitQuestion(question) {
  const trimmed = question.trim();
  if (!trimmed) {
    return;
  }
  addMessage(trimmed, "user");
  guide.quickReplies.hidden = true;
  answerQuestion(trimmed);
}

function setGuideOpen(open) {
  guide.panel.hidden = !open;
  guide.launcher.setAttribute("aria-expanded", String(open));
  guide.launcher.classList.toggle("is-open", open);
  if (open) {
    guide.launcher.querySelector("i").hidden = true;
    const focusTarget = guide.chatView.hidden ? guide.navigateTab : guide.input;
    window.setTimeout(() => focusTarget.focus(), 50);
  } else {
    guide.launcher.focus();
  }
}

function switchView(showChat) {
  guide.chatView.hidden = !showChat;
  guide.navigationView.hidden = showChat;
  guide.chatTab.classList.toggle("is-active", showChat);
  guide.navigateTab.classList.toggle("is-active", !showChat);
  guide.chatTab.setAttribute("aria-selected", String(showChat));
  guide.navigateTab.setAttribute("aria-selected", String(!showChat));
}

guide.launcher.addEventListener("click", () => setGuideOpen(guide.panel.hidden));
guide.closeButton.addEventListener("click", () => setGuideOpen(false));
guide.chatTab.addEventListener("click", () => switchView(true));
guide.navigateTab.addEventListener("click", () => switchView(false));
guide.form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion(guide.input.value);
  guide.input.value = "";
});
guide.quickReplies.addEventListener("click", (event) => {
  if (event.target.matches("button")) {
    submitQuestion(event.target.textContent);
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !guide.panel.hidden) {
    setGuideOpen(false);
  }
});

// Start with a short message that reflects the page the visitor is viewing.
addMessage(pageGreetings[currentPage] || pageGreetings["index.html"], "guide");

// Query options make the two guide views easy to share and test.
const initialGuideView = new URLSearchParams(window.location.search).get("guide");
if (initialGuideView === "navigate") {
  switchView(false);
}
if (initialGuideView === "open" || initialGuideView === "navigate") {
  setGuideOpen(true);
}
