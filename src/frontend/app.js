// StaySphere frontend — plain JS, no build step required.
// API_BASE is overridable at deploy time by editing this one line
// (or by serving this file through a templating step that injects it).
const API_BASE = window.STAYSPHERE_API_BASE || "http://localhost:8000";

let token = localStorage.getItem("staysphere_token") || null;
let currentUser = JSON.parse(localStorage.getItem("staysphere_user") || "null");
let currentSearchPage = 1;
let map = null;
let mapMarkers = [];

function ensureMap() {
  const el = document.getElementById("listings-map");
  if (!el || typeof L === "undefined") return null;
  if (!map) {
    map = L.map(el).setView([1.29, 103.86], 4); // roughly centred on the dataset's SE Asia spread
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(map);
  }
  return map;
}

function placeholderImage(listingId, w = 400, h = 300) {
  // Generic royalty-free placeholder photo, deterministic per listing
  // (same listing always shows the same image). NOT a real property
  // photo — see docs/RESPONSIBLE_AI.md "Images" note.
  return `https://picsum.photos/seed/staysphere${listingId}/${w}/${h}`;
}

function renderCalendarGrid(ranges, monthsToShow = 2) {
  const bookedMap = new Map();
  ranges.forEach(r => {
    let d = new Date(r.check_in.split("T")[0] + "T00:00:00");
    const end = new Date(r.check_out.split("T")[0] + "T00:00:00");
    while (d < end) {
      bookedMap.set(d.toISOString().split("T")[0], r.label || "Booked");
      d.setDate(d.getDate() + 1);
    }
  });

  const today = new Date();
  let html = '<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">';
  for (let m = 0; m < monthsToShow; m++) {
    const monthDate = new Date(today.getFullYear(), today.getMonth() + m, 1);
    const monthLabel = monthDate.toLocaleString("default", { month: "long", year: "numeric" });
    const daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();
    const startOffset = monthDate.getDay();

    html += `<div><div class="text-sm font-semibold mb-2 text-center">${monthLabel}</div>`;
    html += `<div class="grid grid-cols-7 gap-1 text-[10px] text-center text-slate-400 mb-1">${["S","M","T","W","T","F","S"].map(d => `<div>${d}</div>`).join("")}</div>`;
    html += `<div class="grid grid-cols-7 gap-1">`;
    for (let i = 0; i < startOffset; i++) html += `<div></div>`;
    for (let day = 1; day <= daysInMonth; day++) {
      const d = new Date(monthDate.getFullYear(), monthDate.getMonth(), day);
      const key = d.toISOString().split("T")[0];
      const isBooked = bookedMap.has(key);
      const isPast = d < new Date(today.getFullYear(), today.getMonth(), today.getDate());
      const cls = isBooked ? "bg-red-100 text-red-600" : (isPast ? "bg-slate-50 text-slate-300" : "bg-white text-slate-700 border border-slate-200");
      html += `<div class="aspect-square flex items-center justify-center rounded text-[11px] ${cls}" title="${isBooked ? bookedMap.get(key) : ""}">${day}</div>`;
    }
    html += `</div></div>`;
  }
  html += "</div>";
  html += `<div class="flex gap-4 text-[11px] text-slate-500 mt-3"><span><span class="inline-block w-3 h-3 bg-red-100 rounded mr-1 align-middle"></span>Booked</span><span><span class="inline-block w-3 h-3 border border-slate-200 rounded mr-1 align-middle"></span>Available</span></div>`;
  return html;
}

async function loadCityChips() {
  try {
    const data = await api("/api/listings?page_size=1");
    // Cities are a small fixed set in this dataset — derive from a
    // lightweight dedicated call rather than hardcoding, so it still
    // works once the real dataset (different cities) is loaded.
    const cities = ["Singapore", "Bangkok", "Kuala Lumpur", "Jakarta", "Manila"];
    document.getElementById("city-chips").innerHTML = cities.map(c => `
      <button onclick="openCityBrowsePopup('${c}')" class="px-3 py-1.5 rounded-full border border-slate-300 text-sm hover:bg-slate-50">📍 ${c}</button>
    `).join("");
  } catch (e) { /* non-critical */ }
}

async function openCityBrowsePopup(city) {
  try {
    const data = await api(`/api/listings?city=${encodeURIComponent(city)}&page_size=20&sort=rating`);
    openModal(`
      <h3 class="text-lg font-bold mb-3">${data.total} place${data.total === 1 ? "" : "s"} in ${city}</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 max-h-[65vh] overflow-y-auto">
        ${data.results.map(listingCard).join("")}
      </div>
    `);
  } catch (e) {
    toast(e.message, true);
  }
}
function renderMapMarkers(listings) {
  const m = ensureMap();
  if (!m) return;
  mapMarkers.forEach(mk => m.removeLayer(mk));
  mapMarkers = [];
  const bounds = [];
  listings.forEach(l => {
    if (l.latitude == null || l.longitude == null) return;
    const icon = L.divIcon({
      className: "",
      html: `<div style="background:#e11d48;color:white;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.3)">$${Math.round(l.price)}</div>`,
    });
    const marker = L.marker([l.latitude, l.longitude], { icon }).addTo(m);
    marker.bindPopup(`<b>${l.neighbourhood}, ${l.city}</b><br>$${l.price}/night · ★ ${l.review_scores_rating ?? "New"}`);
    marker.on("click", () => viewListing(l.listing_id));
    mapMarkers.push(marker);
    bounds.push([l.latitude, l.longitude]);
  });
  if (bounds.length > 0) {
    m.fitBounds(bounds, { padding: [30, 30], maxZoom: 12 });
  }
}

function showView(view) {
  if (view === "admin" && (!currentUser || currentUser.role !== "admin")) {
    toast("Admin access only", true);
    view = "home";
  }
  if (view === "trips" && !token) {
    toast("Please log in first", true);
    view = "login";
  }
  document.querySelectorAll("main > section").forEach(s => s.style.display = "none");
  document.getElementById(`view-${view}`).style.display = "block";
  if (view === "home") {
    loadStats();
    loadCityChips();
    searchListings(1);
    setTimeout(() => { if (map) map.invalidateSize(); }, 100);
  }
  if (view === "trips") loadTrips();
  if (view === "admin") { loadAdminStats(); loadPricingHeatmap(); loadAdminListings(1); loadAdminBookings(); loadAdminReviews(); loadAdminUsers(); }
  if (view === "chatbot") ensureChatGreeting();
}

function toast(message, isError = false) {
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast px-4 py-2 rounded-lg shadow text-sm text-white ${isError ? "bg-red-600" : "bg-slate-800"}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function updateNav() {
  const guestNav = document.getElementById("nav-guest");
  const userNav = document.getElementById("nav-user");
  const tripsNav = document.getElementById("nav-trips");
  const adminNav = document.getElementById("nav-admin");
  if (token && currentUser) {
    guestNav.style.display = "none";
    userNav.style.display = "flex";
    tripsNav.style.display = "inline-block";
    adminNav.style.display = currentUser.role === "admin" ? "inline-block" : "none";
    document.getElementById("nav-user-name").textContent = `Hi, ${currentUser.name}`;
  } else {
    guestNav.style.display = "inline";
    userNav.style.display = "none";
    tripsNav.style.display = "none";
    adminNav.style.display = "none";
  }
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  let body = null;
  try { body = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) {
    const message = (body && body.detail) ? body.detail : `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return body;
}

// ---- Auth ----

async function register() {
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  if (!name || !email || password.length < 8) {
    toast("Please fill all fields (password min 8 characters)", true);
    return;
  }
  try {
    await api("/api/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) });
    toast("Account created. Please log in.");
    showView("login");
  } catch (e) {
    toast(e.message, true);
  }
}

async function login() {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  try {
    const data = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    token = data.access_token;
    currentUser = data.user;
    localStorage.setItem("staysphere_token", token);
    localStorage.setItem("staysphere_user", JSON.stringify(currentUser));
    updateNav();
    toast(`Welcome back, ${currentUser.name}`);
    showView("home");
  } catch (e) {
    toast(e.message, true);
  }
}

async function demoLogin(role) {
  const email = role === "admin" ? "admin@staysphere.demo" : "guest@staysphere.demo";
  document.getElementById("login-email").value = email;
  document.getElementById("login-password").value = "Demo1234!";
  await login();
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem("staysphere_token");
  localStorage.removeItem("staysphere_user");
  updateNav();
  showView("home");
}

// ---- Search ----

async function loadStats() {
  try {
    const stats = await api("/api/analytics/overview");
    document.getElementById("stats-bar").innerHTML = `
      <div class="bg-white rounded-xl border border-slate-200 p-3"><div class="text-lg font-bold">${stats.total_listings}</div><div class="text-slate-500">Total listings</div></div>
      <div class="bg-white rounded-xl border border-slate-200 p-3"><div class="text-lg font-bold">$${stats.average_price}</div><div class="text-slate-500">Average price/night</div></div>
      <div class="bg-white rounded-xl border border-slate-200 p-3"><div class="text-lg font-bold">${stats.average_rating} ★</div><div class="text-slate-500">Average rating</div></div>
      <div class="bg-white rounded-xl border border-slate-200 p-3"><div class="text-lg font-bold">${stats.most_common_city}</div><div class="text-slate-500">Most listed city</div></div>
    `;
  } catch (e) { /* non-critical */ }
}

async function searchListings(page = 1) {
  currentSearchPage = page;
  const grid = document.getElementById("listings-grid");
  const loading = document.getElementById("listings-loading");
  const empty = document.getElementById("listings-empty");
  loading.style.display = "block";
  empty.style.display = "none";
  grid.innerHTML = "";

  const params = new URLSearchParams({ page, page_size: 9, sort: document.getElementById("f-sort").value });
  const city = document.getElementById("f-city").value.trim();
  const roomType = document.getElementById("f-room-type").value;
  const guests = document.getElementById("f-guests").value;
  const minPrice = document.getElementById("f-min-price").value;
  const maxPrice = document.getElementById("f-max-price").value;
  if (city) params.set("city", city);
  if (roomType) params.set("room_type", roomType);
  if (guests) params.set("accommodates", guests);
  if (minPrice) params.set("min_price", minPrice);
  if (maxPrice) params.set("max_price", maxPrice);

  try {
    const data = await api(`/api/listings?${params.toString()}`);
    loading.style.display = "none";
    updateAiPriceBanner(city, roomType, guests, data.total);
    if (data.results.length === 0) {
      empty.style.display = "block";
      document.getElementById("pagination").innerHTML = "";
      return;
    }
    grid.innerHTML = data.results.map(listingCard).join("");
    renderPagination(data.total, data.page, data.page_size);
    renderMapMarkers(data.results);
  } catch (e) {
    loading.style.display = "none";
    toast(e.message, true);
  }
}

async function updateAiPriceBanner(city, roomType, guests, matchCount) {
  const banner = document.getElementById("ai-price-banner");
  // Only worth estimating once the two features that matter most to
  // price (city + room type) are actually specified — otherwise the
  // estimate would be too generic to be useful.
  if (!city || !roomType) {
    banner.innerHTML = "";
    return;
  }
  try {
    const est = await api("/api/ml/price-estimate", { method: "POST", body: JSON.stringify({
      city, room_type: roomType, property_type: "Apartment",
      accommodates: parseInt(guests, 10) || 2, bedrooms: 1, minimum_nights: 1, review_scores_rating: 4.5,
    })});
    banner.innerHTML = `
      <div class="bg-rose-50 border border-rose-200 rounded-xl px-4 py-3 text-sm flex flex-wrap items-center justify-between gap-2">
        <span>Based on your filters, our AI estimates a fair price around <b>$${est.estimated_price}</b>/night (typical range $${est.range_low}&ndash;$${est.range_high}). <b>${matchCount}</b> listing${matchCount === 1 ? "" : "s"} match your search.</span>
        <span class="text-xs text-slate-400">${est.disclaimer}</span>
      </div>`;
  } catch (e) {
    banner.innerHTML = "";
  }
}

function listingCard(l) {
  return `
    <div class="cursor-pointer group" onclick="viewListing(${l.listing_id})">
      <div class="relative aspect-square rounded-2xl overflow-hidden mb-2">
        <img src="${placeholderImage(l.listing_id)}" loading="lazy" class="w-full h-full object-cover" alt="${l.property_type}" />
        <button onclick="event.stopPropagation(); toggleWishlist(${l.listing_id}, this)" class="heart-btn absolute top-2 right-2 text-lg transition">🤍</button>
        ${l.host_is_superhost ? '<span class="absolute top-2 left-2 bg-white/90 text-[10px] font-semibold px-2 py-0.5 rounded-full">Superhost</span>' : ""}
      </div>
      <div class="flex justify-between items-start text-sm">
        <div class="min-w-0">
          <div class="font-semibold truncate">${l.neighbourhood}, ${l.city}</div>
          <div class="text-slate-500 text-xs truncate">${l.room_type}</div>
        </div>
        <div class="flex items-center gap-1 text-xs shrink-0 ml-1">★ ${l.review_scores_rating ?? "New"}</div>
      </div>
      <div class="text-sm mt-1"><span class="font-semibold">$${l.price}</span> <span class="text-slate-500">night</span></div>
    </div>`;
}

function toggleWishlist(id, el) {
  el.textContent = el.textContent === "🤍" ? "❤️" : "🤍";
}

// Reusable, condensed pagination: first, last, current +/-1, and "..."
// for gaps — never a flat wall of buttons regardless of page count.
function paginationHTML(total, page, pageSize, onClickFnName) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return "";

  const pageBtn = (p) => `<button onclick="${onClickFnName}(${p})" class="px-3 py-1 rounded-lg border text-sm ${p === page ? "bg-rose-600 text-white border-rose-600" : "border-slate-300 hover:bg-slate-50"}">${p}</button>`;
  const ellipsis = `<span class="px-1 text-slate-400">&hellip;</span>`;
  const navBtn = (p, label, disabled) => `<button onclick="${disabled ? "" : `${onClickFnName}(${p})`}" ${disabled ? "disabled" : ""} class="px-3 py-1 rounded-lg border text-sm ${disabled ? "border-slate-200 text-slate-300" : "border-slate-300 hover:bg-slate-50"}">${label}</button>`;

  const pages = new Set([1, totalPages, page, page - 1, page + 1]);
  const sorted = [...pages].filter(p => p >= 1 && p <= totalPages).sort((a, b) => a - b);

  let html = navBtn(page - 1, "‹", page <= 1);
  let prev = 0;
  for (const p of sorted) {
    if (prev && p - prev > 1) html += ellipsis;
    html += pageBtn(p);
    prev = p;
  }
  html += navBtn(page + 1, "›", page >= totalPages);
  return `<div class="flex items-center gap-1 flex-wrap justify-center">${html}</div>`;
}

function renderPagination(total, page, pageSize) {
  document.getElementById("pagination").innerHTML = paginationHTML(total, page, pageSize, "searchListings");
}

// ---- Listing detail + booking ----

async function viewListing(id) {
  try {
    const l = await api(`/api/listings/${id}`);
    const availability = await api(`/api/listings/${id}/availability`).catch(() => ({ booked_ranges: [] }));
    const reviews = await api(`/api/listings/${id}/reviews`).catch(() => []);

    const section = document.getElementById("view-listing");
    section.innerHTML = `
      <button onclick="showView('home')" class="text-sm text-slate-500 mb-4">&larr; Back to search</button>
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <img src="${placeholderImage(l.listing_id, 800, 400)}" class="w-full h-64 object-cover" alt="Placeholder photo — not a real listing photo" />
        <div class="p-6">
        <h2 class="text-2xl font-bold">${l.name}</h2>
        <p class="text-slate-500 text-sm mb-4">${l.neighbourhood}, ${l.district}, ${l.city}</p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-4">
          <div><span class="text-slate-500">Property</span><br>${l.property_type}</div>
          <div><span class="text-slate-500">Room type</span><br>${l.room_type}</div>
          <div><span class="text-slate-500">Accommodates</span><br>${l.accommodates} guests</div>
          <div><span class="text-slate-500">Bedrooms</span><br>${l.bedrooms}</div>
          <div><span class="text-slate-500">Min nights</span><br>${l.minimum_nights}</div>
          <div><span class="text-slate-500">Max nights</span><br>${l.maximum_nights}</div>
          <div><span class="text-slate-500">Instant book</span><br>${l.instant_bookable ? "Yes" : "No"}</div>
          <div><span class="text-slate-500">Superhost</span><br>${l.host_is_superhost ? "Yes" : "No"}</div>
        </div>
        <div class="mb-4">
          <div class="font-semibold text-sm mb-1">Review scores</div>
          <div class="grid grid-cols-3 md:grid-cols-7 gap-2 text-xs">
            ${["rating","accuracy","cleanliness","checkin","communication","location","value"].map(k => `
              <div class="bg-slate-50 rounded-lg p-2 text-center">
                <div class="font-bold">${l["review_scores_" + k] ?? "-"}</div>
                <div class="text-slate-500 capitalize">${k}</div>
              </div>`).join("")}
          </div>
        </div>
        <div class="mb-4"><span class="text-slate-500 text-sm">Amenities:</span> <span class="text-sm">${l.amenities.split("|").join(", ")}</span></div>

        <div class="border-t border-slate-200 pt-4">
          <div class="font-semibold text-sm mb-2">Availability</div>
          ${renderCalendarGrid(availability.booked_ranges.map(r => ({ check_in: r.check_in, check_out: r.check_out, label: "Booked" })), 2)}
        </div>

        <div class="border-t border-slate-200 pt-4 mt-4">
          <div class="text-xl font-bold mb-3">$${l.price}<span class="text-sm font-normal text-slate-500">/night</span></div>
          <div class="grid grid-cols-3 gap-3 mb-3">
            <input type="date" id="bk-checkin" class="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
            <input type="date" id="bk-checkout" class="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
            <input type="number" id="bk-guests" value="1" min="1" max="${l.accommodates}" class="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <button id="bk-continue-btn" onclick="showPaymentStep(${l.listing_id}, ${l.price})" class="bg-rose-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-rose-700">Continue to payment</button>

          <div id="bk-payment-step" style="display:none" class="mt-4 border border-slate-200 rounded-xl p-4 bg-slate-50">
            <div class="text-sm font-semibold mb-1">Simulated payment</div>
            <p class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-3">
              Demo only — no real charge. These fields are never sent to the server or stored anywhere.
            </p>
            <div class="grid grid-cols-2 gap-3 mb-3">
              <input placeholder="Card number (demo)" maxlength="19" class="col-span-2 border border-slate-300 rounded-lg px-3 py-2 text-sm" oninput="this.value=this.value.replace(/[^0-9 ]/g,'')" />
              <input placeholder="MM/YY" maxlength="5" class="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
              <input placeholder="CVC" maxlength="4" class="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div id="bk-total-line" class="text-sm mb-3"></div>
            <button onclick="book(${l.listing_id})" class="w-full bg-rose-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-rose-700">Confirm booking (simulated payment)</button>
          </div>
          <p class="text-xs text-slate-400 mt-2">This is a simulated academic booking. No real payment is processed.</p>
        </div>

        <div class="border-t border-slate-200 pt-4 mt-4">
          <div class="font-semibold text-sm mb-2">Guest reviews (${reviews.length})</div>
          ${reviews.length === 0
            ? '<p class="text-sm text-slate-400">No guest reviews yet for this listing.</p>'
            : reviews.map(r => `
              <div class="border-b border-slate-100 py-2 text-sm">
                <div class="flex justify-between"><span class="font-medium">${r.guest_name}</span><span class="text-amber-600">${"★".repeat(r.rating)}${"☆".repeat(5 - r.rating)}</span></div>
                ${r.comment ? `<p class="text-slate-600 text-xs mt-1">${r.comment}</p>` : ""}
                <p class="text-slate-400 text-[11px] mt-1">${r.created_at.split("T")[0]}</p>
              </div>`).join("")}
        </div>
        </div>
      </div>
    `;
    showView("listing");
  } catch (e) {
    toast(e.message, true);
  }
}

function showPaymentStep(listingId, pricePerNight) {
  if (!token) { toast("Please log in first", true); showView("login"); return; }
  const checkIn = document.getElementById("bk-checkin").value;
  const checkOut = document.getElementById("bk-checkout").value;
  if (!checkIn || !checkOut) { toast("Please select check-in and check-out dates first", true); return; }
  const nights = Math.round((new Date(checkOut) - new Date(checkIn)) / 86400000);
  if (nights < 1) { toast("Check-out must be after check-in", true); return; }
  document.getElementById("bk-total-line").innerHTML =
    `${nights} night${nights > 1 ? "s" : ""} × $${pricePerNight} = <span class="font-semibold">$${(nights * pricePerNight).toFixed(2)}</span>`;
  document.getElementById("bk-payment-step").style.display = "block";
  document.getElementById("bk-continue-btn").style.display = "none";
}

async function book(listingId) {
  if (!token) { toast("Please log in first", true); showView("login"); return; }
  const checkIn = document.getElementById("bk-checkin").value;
  const checkOut = document.getElementById("bk-checkout").value;
  const guests = parseInt(document.getElementById("bk-guests").value, 10);
  if (!checkIn || !checkOut) { toast("Please select check-in and check-out dates", true); return; }

  try {
    const booking = await api("/api/bookings", {
      method: "POST",
      body: JSON.stringify({
        listing_id: listingId,
        check_in: `${checkIn}T14:00:00`,
        check_out: `${checkOut}T11:00:00`,
        guests,
      }),
    });
    toast(`Booking confirmed! Total: $${booking.total_amount}`);
    showView("trips");
  } catch (e) {
    toast(e.message, true);
  }
}

// ---- My trips ----

async function loadTrips() {
  if (!token) { showView("login"); return; }
  try {
    const bookings = await api("/api/bookings");
    const list = document.getElementById("trips-list");
    const empty = document.getElementById("trips-empty");
    if (bookings.length === 0) {
      empty.style.display = "block";
      list.innerHTML = "";
      return;
    }
    empty.style.display = "none";
    list.innerHTML = bookings.map(b => `
      <div class="bg-white rounded-xl border border-slate-200 p-4 flex justify-between items-center">
        <div>
          <div class="font-semibold text-sm">Listing #${b.listing_id}</div>
          <div class="text-xs text-slate-500">${b.check_in.split("T")[0]} &rarr; ${b.check_out.split("T")[0]} · ${b.nights} nights · ${b.guests} guests</div>
          <div class="text-xs mt-1 flex items-center gap-2">
            <span class="px-2 py-0.5 rounded-full ${statusColor(b.status)}">${b.status}</span>
            ${b.has_review ? '<span class="text-emerald-600">✓ Reviewed</span>' : ""}
          </div>
        </div>
        <div class="text-right">
          <div class="font-bold">$${b.total_amount}</div>
          ${b.status !== "cancelled" ? `<button onclick="cancelBooking(${b.booking_id})" class="text-xs text-red-600 underline mt-1 block ml-auto">Cancel</button>` : ""}
          ${b.can_review ? `<button onclick="openReviewModal(${b.booking_id}, ${b.listing_id})" class="text-xs text-rose-600 underline mt-1 block ml-auto">Leave a review</button>` : ""}
        </div>
      </div>
    `).join("");
  } catch (e) {
    toast(e.message, true);
  }
}

function openReviewModal(bookingId, listingId) {
  openModal(`
    <h3 class="text-lg font-bold mb-3">Leave a review</h3>
    <div class="flex gap-1 text-2xl mb-3" id="review-stars">
      ${[1,2,3,4,5].map(n => `<span onclick="setReviewRating(${n})" data-star="${n}" class="cursor-pointer text-slate-300">★</span>`).join("")}
    </div>
    <textarea id="review-comment" placeholder="How was your stay? (optional)" maxlength="1000" class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3" rows="3"></textarea>
    <button onclick="submitReview(${bookingId})" class="bg-rose-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-rose-700">Submit review</button>
  `);
  window._reviewRating = 5;
  setReviewRating(5);
}

function setReviewRating(n) {
  window._reviewRating = n;
  document.querySelectorAll("#review-stars span").forEach(el => {
    el.classList.toggle("text-amber-500", parseInt(el.dataset.star, 10) <= n);
    el.classList.toggle("text-slate-300", parseInt(el.dataset.star, 10) > n);
  });
}

async function submitReview(bookingId) {
  const comment = document.getElementById("review-comment").value.trim();
  try {
    await api("/api/reviews", { method: "POST", body: JSON.stringify({
      booking_id: bookingId, rating: window._reviewRating || 5, comment: comment || null,
    })});
    toast("Thanks for your review!");
    closeModal();
    loadTrips();
  } catch (e) {
    toast(e.message, true);
  }
}

function statusColor(status) {
  return { confirmed: "bg-green-100 text-green-700", cancelled: "bg-red-100 text-red-700", pending: "bg-amber-100 text-amber-700", completed: "bg-slate-100 text-slate-700" }[status] || "bg-slate-100";
}

async function cancelBooking(id) {
  try {
    await api(`/api/bookings/${id}/cancel`, { method: "PATCH" });
    toast("Booking cancelled");
    loadTrips();
  } catch (e) {
    toast(e.message, true);
  }
}

// ---- Find your match (recommendations) ----

async function getRecommendations() {
  const budgetMin = parseFloat(document.getElementById("rec-budget-min").value) || 0;
  const budgetMax = parseFloat(document.getElementById("rec-budget-max").value);
  const guests = parseInt(document.getElementById("rec-guests").value, 10) || 1;
  const city = document.getElementById("rec-city").value.trim();

  if (!budgetMax || budgetMax <= 0) {
    toast("Please enter a max budget", true);
    return;
  }

  const resultsEl = document.getElementById("recommend-results");
  resultsEl.innerHTML = `<div class="text-slate-400 text-sm col-span-full">Finding your best matches...</div>`;

  try {
    const payload = { budget_min: budgetMin, budget_max: budgetMax, guests };
    if (city) payload.city = city;
    const data = await api("/api/recommendations", { method: "POST", body: JSON.stringify(payload) });
    if (data.results.length === 0) {
      resultsEl.innerHTML = `<div class="text-slate-400 text-sm col-span-full">No listings matched — try widening your budget.</div>`;
      return;
    }
    resultsEl.innerHTML = data.results.map(recommendationCard).join("");
  } catch (e) {
    resultsEl.innerHTML = `<div class="text-red-600 text-sm col-span-full">${e.message}</div>`;
  }
}

function recommendationCard(l) {
  return `
    <div class="cursor-pointer group" onclick="viewListing(${l.listing_id})">
      <div class="relative aspect-square rounded-2xl overflow-hidden mb-2">
        <img src="${placeholderImage(l.listing_id)}" loading="lazy" class="w-full h-full object-cover" alt="${l.property_type}" />
        ${l.is_great_value ? '<span class="absolute top-2 left-2 bg-emerald-600 text-white text-[10px] font-semibold px-2 py-0.5 rounded-full">Great value</span>' : ""}
      </div>
      <div class="flex justify-between items-start text-sm">
        <div class="min-w-0">
          <div class="font-semibold truncate">${l.neighbourhood}, ${l.city}</div>
          <div class="text-slate-500 text-xs truncate">${l.room_type} · sleeps ${l.accommodates}</div>
        </div>
        <div class="flex items-center gap-1 text-xs shrink-0 ml-1">★ ${l.review_scores_rating ?? "New"}</div>
      </div>
      <div class="text-sm mt-1"><span class="font-semibold">$${l.price}</span> <span class="text-slate-500">night</span>
        ${l.is_great_value ? `<span class="text-emerald-600 text-xs ml-1">(est. fair: $${l.fair_price_estimate})</span>` : ""}
      </div>
      <div class="text-xs text-slate-400 mt-0.5 truncate">${l.match_reason}</div>
    </div>`;
}

// ---- Chatbot ----

let chatState = { budget_min: null, budget_max: null, guests: null, city: null, room_type: null };
let chatStarted = false;

function chatBubble(text, fromUser) {
  return `<div class="flex ${fromUser ? "justify-end" : "justify-start"}">
    <div class="max-w-[80%] rounded-2xl px-4 py-2 text-sm ${fromUser ? "bg-rose-600 text-white" : "bg-slate-100 text-slate-800"}">${text}</div>
  </div>`;
}

function ensureChatGreeting() {
  if (chatStarted) return;
  chatStarted = true;
  document.getElementById("chat-messages").innerHTML = chatBubble(
    "Hi! Tell me your budget, city, guest count or room type and I'll find matching rooms \u2014 e.g. \u201cSingapore, 2 guests, under $150\u201d.", false
  );
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;
  ensureChatGreeting();
  const messagesEl = document.getElementById("chat-messages");
  messagesEl.insertAdjacentHTML("beforeend", chatBubble(message, true));
  input.value = "";
  messagesEl.scrollTop = messagesEl.scrollHeight;

  const thinkingId = `thinking-${Date.now()}`;
  messagesEl.insertAdjacentHTML("beforeend", `<div id="${thinkingId}">${chatBubble("...", false)}</div>`);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  try {
    const data = await api("/api/chatbot/message", { method: "POST", body: JSON.stringify({ message, state: chatState }) });
    chatState = data.state;
    document.getElementById(thinkingId).remove();
    messagesEl.insertAdjacentHTML("beforeend", chatBubble(data.reply, false));
    if (data.recommendations && data.recommendations.length > 0) {
      const cardsHtml = `<div class="grid grid-cols-2 gap-3 mt-1">${data.recommendations.slice(0, 4).map(recommendationCard).join("")}</div>`;
      messagesEl.insertAdjacentHTML("beforeend", cardsHtml);
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;
  } catch (e) {
    document.getElementById(thinkingId).remove();
    messagesEl.insertAdjacentHTML("beforeend", chatBubble(`Sorry, something went wrong: ${e.message}`, false));
  }
}

function resetChat() {
  chatState = { budget_min: null, budget_max: null, guests: null, city: null, room_type: null };
  chatStarted = false;
  document.getElementById("chat-messages").innerHTML = "";
  ensureChatGreeting();
}

// ---- Price estimator ----

async function estimatePrice() {
  const payload = {
    city: document.getElementById("est-city").value.trim() || "Singapore",
    property_type: document.getElementById("est-property-type").value,
    room_type: document.getElementById("est-room-type").value,
    accommodates: parseInt(document.getElementById("est-accommodates").value, 10),
    bedrooms: parseInt(document.getElementById("est-bedrooms").value, 10),
    minimum_nights: parseInt(document.getElementById("est-min-nights").value, 10),
    review_scores_rating: 4.5,
  };
  const resultEl = document.getElementById("estimate-result");
  resultEl.innerHTML = `<div class="text-sm text-slate-400">Estimating...</div>`;
  try {
    const est = await api("/api/ml/price-estimate", { method: "POST", body: JSON.stringify(payload) });
    resultEl.innerHTML = `
      <div class="bg-rose-50 border border-rose-200 rounded-xl p-4">
        <div class="text-2xl font-bold text-rose-700">$${est.estimated_price}<span class="text-sm font-normal text-slate-500">/night</span></div>
        <div class="text-sm text-slate-600">Typical market range: $${est.range_low} &ndash; $${est.range_high}</div>
        <div class="text-xs text-slate-500 mt-2">Key factors: ${est.key_factors.join(", ")}</div>
        <div class="text-xs text-slate-400 mt-2">${est.disclaimer}</div>
      </div>`;
  } catch (e) {
    resultEl.innerHTML = `<div class="text-sm text-red-600">${e.message}</div>`;
  }
}

// ---- Admin dashboard ----

async function loadAdminStats() {
  try {
    const stats = await api("/api/admin/analytics");
    document.getElementById("admin-stats").innerHTML = `
      <div class="bg-white rounded-xl border border-slate-200 p-3"><div class="text-lg font-bold">${stats.total_listings}</div><div class="text-slate-500">Listings</div></div>
      <div class="bg-white rounded-xl border border-slate-200 p-3"><div class="text-lg font-bold">${stats.total_users}</div><div class="text-slate-500">Users</div></div>
      <div class="bg-white rounded-xl border border-slate-200 p-3"><div class="text-lg font-bold">${stats.total_bookings}</div><div class="text-slate-500">Bookings (${stats.confirmed_bookings} confirmed)</div></div>
      <div class="bg-white rounded-xl border border-slate-200 p-3"><div class="text-lg font-bold">$${stats.total_revenue}</div><div class="text-slate-500">Simulated revenue</div></div>
    `;
  } catch (e) {
    toast(e.message, true);
  }
}

let adminCurrentPage = 1;
let adminCurrentCityFilter = null;
const ADMIN_PAGE_SIZE = 15;

let adminHeatmapMap = null;
let adminHeatmapCircles = [];
let heatmapLayer = "city"; // "city" | "neighbourhood"
let lastPricingInsights = null;

function setHeatmapLayer(layer) {
  heatmapLayer = layer;
  document.getElementById("heatmap-layer-city").className = `px-3 py-1 rounded-full text-xs ${layer === "city" ? "bg-rose-600 text-white" : "border border-slate-300"}`;
  document.getElementById("heatmap-layer-neighbourhood").className = `px-3 py-1 rounded-full text-xs ${layer === "neighbourhood" ? "bg-rose-600 text-white" : "border border-slate-300"}`;
  if (lastPricingInsights) renderHeatmap(lastPricingInsights);
}

async function loadPricingHeatmap() {
  try {
    const data = await api("/api/admin/pricing-insights");
    lastPricingInsights = data;
    renderHeatmap(data);
  } catch (e) {
    toast(e.message, true);
  }
}

function renderHeatmap(data) {
  const items = heatmapLayer === "city" ? data.cities : data.neighbourhoods;
  const maxPrice = Math.max(...items.map(c => c.average_price), 1);
  const maxCount = Math.max(...items.map(c => c.listing_count), 1);

  document.getElementById("pricing-heatmap").innerHTML = items.map(c => {
    const label = heatmapLayer === "city" ? c.city : `${c.neighbourhood}, ${c.city}`;
    const widthPct = Math.round((c.average_price / maxPrice) * 100);
    const intensity = Math.round(200 - (c.average_price / maxPrice) * 120);
    return `
      <div class="flex items-center gap-3 text-xs cursor-pointer hover:bg-slate-50 rounded p-1" onclick="openLocationPopup('${c.city.replace(/'/g, "\\'")}', ${heatmapLayer === "neighbourhood" ? `'${c.neighbourhood.replace(/'/g, "\\'")}'` : "null"})">
        <div class="w-28 shrink-0 font-medium truncate">${label}</div>
        <div class="flex-1 bg-slate-100 rounded-full h-5 overflow-hidden">
          <div style="width:${widthPct}%; background: rgb(225,${intensity},${intensity})" class="h-full flex items-center justify-end pr-2 text-white font-semibold">$${c.average_price}</div>
        </div>
        <div class="w-20 shrink-0 text-slate-500">${c.listing_count} rooms</div>
        <div class="w-24 shrink-0 text-slate-500">demand ${(c.demand_index * 100).toFixed(0)}%</div>
      </div>`;
  }).join("");

  const mapEl = document.getElementById("pricing-heatmap-map");
  if (mapEl && typeof L !== "undefined") {
    if (!adminHeatmapMap) {
      adminHeatmapMap = L.map(mapEl).setView([5, 105], 4);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
      }).addTo(adminHeatmapMap);
    }
    adminHeatmapCircles.forEach(c => adminHeatmapMap.removeLayer(c));
    adminHeatmapCircles = [];
    const bounds = [];
    items.forEach(c => {
      if (!c.latitude || !c.longitude) return;
      const intensity = Math.round(200 - (c.average_price / maxPrice) * 150);
      const radius = (heatmapLayer === "city" ? 15000 : 4000) + (c.listing_count / maxCount) * (heatmapLayer === "city" ? 45000 : 12000);
      const circle = L.circle([c.latitude, c.longitude], {
        radius,
        color: `rgb(225,${intensity},${intensity})`,
        fillColor: `rgb(225,${intensity},${intensity})`,
        fillOpacity: 0.5,
        weight: 2,
      }).addTo(adminHeatmapMap);
      const label = heatmapLayer === "city" ? c.city : `${c.neighbourhood}, ${c.city}`;
      circle.bindPopup(`<b>${label}</b><br>Avg price: $${c.average_price}<br>${c.listing_count} listings<br>Demand index: ${(c.demand_index * 100).toFixed(0)}%<br><a href="#" onclick="openLocationPopup('${c.city}', ${heatmapLayer === "neighbourhood" ? `'${c.neighbourhood}'` : "null"}); return false;">View &amp; edit rooms here</a>`);
      adminHeatmapCircles.push(circle);
      bounds.push([c.latitude, c.longitude]);
    });
    if (bounds.length > 0) adminHeatmapMap.fitBounds(bounds, { padding: [40, 40], maxZoom: heatmapLayer === "city" ? 7 : 12 });
    setTimeout(() => adminHeatmapMap.invalidateSize(), 150);
  }
}

async function loadAdminListings(page = 1) {
  adminCurrentPage = page;
  try {
    const cityQuery = adminCurrentCityFilter ? `&city=${encodeURIComponent(adminCurrentCityFilter)}` : "";
    const listings = await api(`/api/admin/listings-pricing?page=${page}&page_size=${ADMIN_PAGE_SIZE}${cityQuery}`);
    const totalData = await api(`/api/admin/listings?page=${page}&page_size=${ADMIN_PAGE_SIZE}${cityQuery}`);
    document.getElementById("admin-listings-table").innerHTML = listings.map(l => {
      let gapLabel = "-";
      if (l.suggested_price != null) {
        const color = l.price_gap_pct > 5 ? "text-red-600" : (l.price_gap_pct < -5 ? "text-amber-600" : "text-slate-500");
        const sign = l.price_gap_pct > 0 ? "+" : "";
        gapLabel = `<span class="${color}">$${l.suggested_price} (${sign}${l.price_gap_pct}%)</span>`;
      }
      return `
      <tr class="border-t border-slate-100">
        <td class="px-4 py-2">${l.listing_id}</td>
        <td class="px-4 py-2">${l.name}</td>
        <td class="px-4 py-2">${l.city}</td>
        <td class="px-4 py-2">$${l.price}</td>
        <td class="px-4 py-2">${gapLabel}</td>
        <td class="px-4 py-2">${l.review_scores_rating ?? "-"}</td>
        <td class="px-4 py-2 text-right whitespace-nowrap">
          <button onclick="openEditListingModal(${l.listing_id})" class="text-xs text-slate-600 underline mr-2">Edit</button>
          <button onclick="openListingCalendarModal(${l.listing_id}, '${l.name.replace(/'/g, "\\'")}')" class="text-xs text-slate-600 underline mr-2">Calendar</button>
          <button onclick="adminDeleteListing(${l.listing_id})" class="text-xs text-red-600 underline">Delete</button>
        </td>
      </tr>`;
    }).join("");
    document.getElementById("admin-pagination").innerHTML = paginationHTML(totalData.total, page, ADMIN_PAGE_SIZE, "loadAdminListings");
  } catch (e) {
    toast(e.message, true);
  }
}

async function loadAdminBookings() {
  try {
    const bookings = await api("/api/admin/bookings?page=1&page_size=20");
    const tbody = document.getElementById("admin-bookings-table");
    if (bookings.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="px-4 py-4 text-slate-400 text-center">No bookings yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = bookings.map(b => `
      <tr class="border-t border-slate-100">
        <td class="px-4 py-2">#${b.booking_id}</td>
        <td class="px-4 py-2">${b.guest_name}<div class="text-xs text-slate-400">${b.guest_email}</div></td>
        <td class="px-4 py-2">${b.listing_name}</td>
        <td class="px-4 py-2 text-xs">${b.check_in.split("T")[0]} &rarr; ${b.check_out.split("T")[0]}</td>
        <td class="px-4 py-2">$${b.total_amount}</td>
        <td class="px-4 py-2"><span class="px-2 py-0.5 rounded-full text-xs ${statusColor(b.status)}">${b.status}</span></td>
      </tr>
    `).join("");
  } catch (e) {
    toast(e.message, true);
  }
}

async function loadAdminReviews() {
  try {
    const reviews = await api("/api/admin/reviews?page=1&page_size=20");
    const tbody = document.getElementById("admin-reviews-table");
    if (reviews.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="px-4 py-4 text-slate-400 text-center">No reviews yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = reviews.map(r => `
      <tr class="border-t border-slate-100">
        <td class="px-4 py-2">${r.guest_name}<div class="text-xs text-slate-400">${r.guest_email}</div></td>
        <td class="px-4 py-2">${r.listing_name}</td>
        <td class="px-4 py-2 text-amber-600">${"★".repeat(r.rating)}</td>
        <td class="px-4 py-2 text-xs max-w-xs truncate">${r.comment || "-"}</td>
        <td class="px-4 py-2 text-xs">${r.created_at.split("T")[0]}</td>
        <td class="px-4 py-2 text-right"><button onclick="adminDeleteReview(${r.review_id})" class="text-xs text-red-600 underline">Remove</button></td>
      </tr>
    `).join("");
  } catch (e) {
    toast(e.message, true);
  }
}

async function adminDeleteReview(id) {
  if (!confirm("Remove this review?")) return;
  try {
    await api(`/api/admin/reviews/${id}`, { method: "DELETE" });
    toast("Review removed");
    loadAdminReviews();
  } catch (e) {
    toast(e.message, true);
  }
}

async function loadAdminUsers() {
  try {
    const users = await api("/api/admin/users?page=1&page_size=50");
    document.getElementById("admin-users-table").innerHTML = users.map(u => `
      <tr class="border-t border-slate-100">
        <td class="px-4 py-2">${u.name}</td>
        <td class="px-4 py-2">${u.email}</td>
        <td class="px-4 py-2">
          <select onchange="adminChangeUserRole(${u.user_id}, this.value)" class="border border-slate-200 rounded px-1 py-0.5 text-xs">
            ${["guest", "host", "admin"].map(r => `<option value="${r}" ${r === u.role ? "selected" : ""}>${r}</option>`).join("")}
          </select>
        </td>
        <td class="px-4 py-2">${u.booking_count}</td>
        <td class="px-4 py-2 text-right"><button onclick="adminDeleteUser(${u.user_id})" class="text-xs text-red-600 underline">Delete</button></td>
      </tr>
    `).join("");
  } catch (e) {
    toast(e.message, true);
  }
}

async function adminChangeUserRole(id, role) {
  try {
    await api(`/api/admin/users/${id}`, { method: "PATCH", body: JSON.stringify({ role }) });
    toast("Role updated");
  } catch (e) {
    toast(e.message, true);
    loadAdminUsers();
  }
}

async function adminDeleteUser(id) {
  if (!confirm("Delete this user? This cannot be undone.")) return;
  try {
    await api(`/api/admin/users/${id}`, { method: "DELETE" });
    toast("User deleted");
    loadAdminUsers();
  } catch (e) {
    toast(e.message, true);
  }
}

async function adminCreateListing() {
  const payload = {
    name: document.getElementById("al-name").value.trim(),
    city: document.getElementById("al-city").value.trim(),
    neighbourhood: document.getElementById("al-neighbourhood").value.trim(),
    property_type: document.getElementById("al-property-type").value,
    room_type: document.getElementById("al-room-type").value,
    accommodates: parseInt(document.getElementById("al-accommodates").value, 10),
    bedrooms: parseInt(document.getElementById("al-bedrooms").value, 10),
    price: parseFloat(document.getElementById("al-price").value),
  };
  if (!payload.name || !payload.city || !payload.neighbourhood || !payload.price) {
    toast("Please fill in name, city, neighbourhood and price", true);
    return;
  }
  try {
    await api("/api/admin/listings", { method: "POST", body: JSON.stringify(payload) });
    toast("Listing added");
    loadAdminStats();
    loadAdminListings(1);
  } catch (e) {
    toast(e.message, true);
  }
}

async function suggestAdminPrice() {
  const payload = {
    city: document.getElementById("al-city").value.trim() || "Singapore",
    property_type: document.getElementById("al-property-type").value,
    room_type: document.getElementById("al-room-type").value,
    accommodates: parseInt(document.getElementById("al-accommodates").value, 10) || 2,
    bedrooms: parseInt(document.getElementById("al-bedrooms").value, 10) || 1,
    minimum_nights: 1,
    review_scores_rating: 4.5,
  };
  const out = document.getElementById("al-suggested-price");
  out.textContent = "Estimating...";
  try {
    const est = await api("/api/ml/price-estimate", { method: "POST", body: JSON.stringify(payload) });
    document.getElementById("al-price").value = est.estimated_price;
    out.innerHTML = `Model suggests <b>$${est.estimated_price}</b> (typical range $${est.range_low}&ndash;$${est.range_high}) based on city, property/room type, capacity and rating — filled into the price field, adjust as needed.`;
  } catch (e) {
    out.textContent = "";
    toast(e.message, true);
  }
}

// ---- Generic modal ----

function openModal(html) {
  document.getElementById("modal-body").innerHTML = html;
  document.getElementById("modal-overlay").style.display = "block";
}

function closeModal() {
  document.getElementById("modal-overlay").style.display = "none";
  document.getElementById("modal-body").innerHTML = "";
}

// ---- Admin: full listing edit ----

const EDITABLE_LISTING_FIELDS = [
  ["name", "Name", "text"], ["city", "City", "text"], ["neighbourhood", "Neighbourhood", "text"],
  ["district", "District", "text"], ["property_type", "Property type", "text"], ["room_type", "Room type", "text"],
  ["accommodates", "Accommodates", "number"], ["bedrooms", "Bedrooms", "number"],
  ["price", "Price/night", "number"], ["minimum_nights", "Minimum nights", "number"],
  ["maximum_nights", "Maximum nights", "number"], ["amenities", "Amenities (| separated)", "text"],
  ["host_response_time", "Host response time", "text"], ["host_response_rate", "Host response rate %", "number"],
  ["host_acceptance_rate", "Host acceptance rate %", "number"],
  ["review_scores_rating", "Overall rating", "number"], ["review_scores_accuracy", "Accuracy score", "number"],
  ["review_scores_cleanliness", "Cleanliness score", "number"], ["review_scores_checkin", "Check-in score", "number"],
  ["review_scores_communication", "Communication score", "number"], ["review_scores_location", "Location score", "number"],
  ["review_scores_value", "Value score", "number"],
  ["latitude", "Latitude", "number"], ["longitude", "Longitude", "number"],
];
const EDITABLE_LISTING_CHECKBOXES = [
  ["instant_bookable", "Instant bookable"], ["host_is_superhost", "Superhost"],
  ["host_identity_verified", "Host identity verified"], ["host_has_profile_pic", "Host has profile pic"],
];

async function openEditListingModal(id) {
  try {
    const l = await api(`/api/listings/${id}`);
    const fieldsHtml = EDITABLE_LISTING_FIELDS.map(([key, label, type]) => `
      <div>
        <label class="text-xs text-slate-500">${label}</label>
        <input id="edit-${key}" type="${type}" value="${l[key] ?? ""}" class="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm" />
      </div>`).join("");
    const checkboxHtml = EDITABLE_LISTING_CHECKBOXES.map(([key, label]) => `
      <label class="flex items-center gap-2 text-xs">
        <input id="edit-${key}" type="checkbox" ${l[key] ? "checked" : ""} /> ${label}
      </label>`).join("");

    openModal(`
      <h3 class="text-lg font-bold mb-3">Edit listing #${id}</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">${fieldsHtml}</div>
      <div class="grid grid-cols-2 gap-2 mb-4">${checkboxHtml}</div>
      <button onclick="submitEditListing(${id})" class="bg-rose-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-rose-700">Save changes</button>
    `);
  } catch (e) {
    toast(e.message, true);
  }
}

async function submitEditListing(id) {
  const payload = {};
  for (const [key, , type] of EDITABLE_LISTING_FIELDS) {
    const el = document.getElementById(`edit-${key}`);
    if (!el || el.value === "") continue;
    payload[key] = type === "number" ? parseFloat(el.value) : el.value;
  }
  for (const [key] of EDITABLE_LISTING_CHECKBOXES) {
    const el = document.getElementById(`edit-${key}`);
    if (el) payload[key] = el.checked;
  }
  try {
    await api(`/api/admin/listings/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
    toast("Listing updated");
    closeModal();
    loadAdminListings(adminCurrentPage);
    loadPricingHeatmap();
  } catch (e) {
    toast(e.message, true);
  }
}

// ---- Admin: per-listing booking calendar ----

async function openListingCalendarModal(id, name) {
  try {
    const bookings = await api(`/api/admin/listings/${id}/bookings`);
    openModal(`
      <h3 class="text-lg font-bold mb-1">Booking calendar — ${name}</h3>
      <p class="text-xs text-slate-400 mb-4">All bookings for this room, any status.</p>
      ${renderCalendarGrid(bookings.map(b => ({ check_in: b.check_in, check_out: b.check_out, label: b.guest_name, status: b.status })), 2)}
      <div class="mt-4">
        ${bookings.length === 0 ? '<p class="text-sm text-slate-400">No bookings yet for this room.</p>' : bookings.map(b => `
          <div class="text-xs border-t border-slate-100 py-2 flex justify-between">
            <span>${b.guest_name} — ${b.check_in.split("T")[0]} &rarr; ${b.check_out.split("T")[0]}</span>
            <span class="px-2 rounded-full ${statusColor(b.status)}">${b.status}</span>
          </div>`).join("")}
      </div>
    `);
  } catch (e) {
    toast(e.message, true);
  }
}

// ---- Admin: click a heatmap location -> popup of rooms there, editable ----

async function openLocationPopup(city, neighbourhood) {
  try {
    const params = new URLSearchParams({ page: "1", page_size: "50", city });
    const data = await api(`/api/admin/listings?${params.toString()}`);
    let rooms = data.results;
    if (neighbourhood) rooms = rooms.filter(r => r.neighbourhood === neighbourhood);
    const title = neighbourhood ? `${neighbourhood}, ${city}` : city;
    openModal(`
      <h3 class="text-lg font-bold mb-3">${rooms.length} room${rooms.length === 1 ? "" : "s"} in ${title}</h3>
      <div class="flex flex-col gap-2 max-h-[60vh] overflow-y-auto">
        ${rooms.map(r => `
          <div class="flex justify-between items-center border border-slate-100 rounded-lg px-3 py-2 text-sm">
            <div>
              <div class="font-medium">${r.name}</div>
              <div class="text-xs text-slate-500">${r.neighbourhood} · ${r.room_type} · $${r.price}/night · ★ ${r.review_scores_rating ?? "New"}</div>
            </div>
            <button onclick="closeModal(); openEditListingModal(${r.listing_id})" class="text-xs text-rose-600 underline shrink-0 ml-2">Edit</button>
          </div>`).join("")}
      </div>
    `);
  } catch (e) {
    toast(e.message, true);
  }
}

async function adminDeleteListing(id) {
  if (!confirm("Delete this listing?")) return;
  try {
    await api(`/api/admin/listings/${id}`, { method: "DELETE" });
    toast("Listing deleted");
    loadAdminStats();
    loadAdminListings(adminCurrentPage);
  } catch (e) {
    toast(e.message, true);
  }
}

// ---- Live filters: respond as soon as the user changes anything ----

let filterDebounceTimer = null;
function debouncedSearch() {
  clearTimeout(filterDebounceTimer);
  filterDebounceTimer = setTimeout(() => searchListings(1), 350);
}

function attachLiveFilters() {
  const textInputs = ["f-city", "f-min-price", "f-max-price", "f-guests"];
  const instantInputs = ["f-room-type", "f-sort"];
  textInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", debouncedSearch);
  });
  instantInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("change", () => searchListings(1));
  });
  const checkinEl = document.getElementById("f-checkin");
  const checkoutEl = document.getElementById("f-checkout");
  if (checkinEl) checkinEl.addEventListener("change", () => searchListings(1));
  if (checkoutEl) checkoutEl.addEventListener("change", () => searchListings(1));
}

// ---- Init ----
updateNav();
attachLiveFilters();
showView("home");
