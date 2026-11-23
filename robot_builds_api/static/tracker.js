const byId = id => document.getElementById(id);
const editor = byId("editor");
const form = byId("project-form");
const deleteButton = byId("delete");
let editingId = null;
let builds = [];
let draggedId = null;

const dateFormat = new Intl.DateTimeFormat(undefined, {month: "short", day: "numeric", year: "numeric"});

function showAccount() {
  sessionStorage.removeItem("buildToken");
  if (editor.open) editor.close();
  builds = [];
  byId("projects").hidden = true;
  byId("logout").hidden = true;
  byId("account").hidden = false;
}

async function request(path, method = "GET", body) {
  const headers = {};
  const token = sessionStorage.getItem("buildToken");
  if (token) headers.Authorization = "Bearer " + token;
  if (body) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {method, headers, body: body ? JSON.stringify(body) : undefined});
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && token) showAccount();
    const fields = Object.values(data.error?.fields || {});
    throw new Error(fields.join(" ") || data.error?.message || "Something went wrong. Try again.");
  }
  return data;
}

function makeCard(build) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = "card";
  card.draggable = true;
  card.dataset.id = build.id;

  const title = document.createElement("strong");
  title.textContent = build.name;
  card.append(title);

  if (build.description) {
    const notes = document.createElement("span");
    notes.className = "notes";
    notes.textContent = build.description;
    card.append(notes);
  }

  const added = document.createElement("time");
  added.dateTime = build.created_at;
  added.textContent = "Added " + dateFormat.format(new Date(build.created_at));
  card.append(added);

  card.onclick = () => edit(build);
  card.ondragstart = event => {
    draggedId = build.id;
    event.dataTransfer.effectAllowed = "move";
    card.classList.add("dragging");
  };
  card.ondragend = () => {
    draggedId = null;
    card.classList.remove("dragging");
  };
  return card;
}

function render() {
  const query = byId("search").value.trim().toLowerCase();
  const visible = builds.filter(build =>
    !query || (build.name + " " + (build.description || "")).toLowerCase().includes(query));

  for (const lane of document.querySelectorAll(".lane")) {
    const inLane = visible.filter(build => build.stage === lane.dataset.stage);
    lane.querySelector(".count").textContent = inLane.length;
    lane.querySelector(".cards").replaceChildren(...inLane.map(makeCard));
  }

  const done = builds.filter(build => build.stage === "Complete").length;
  const active = builds.filter(build => build.stage === "Building" || build.stage === "Testing").length;
  const percent = builds.length ? Math.round(done / builds.length * 100) : 0;
  byId("stat-total").textContent = builds.length;
  byId("stat-active").textContent = active;
  byId("stat-done").textContent = percent + "%";
  byId("progress-bar").style.width = percent + "%";
}

async function loadBoard() {
  const {robot_builds} = await request("/robot-builds");
  builds = robot_builds;
  render();
  byId("account").hidden = true;
  byId("projects").hidden = false;
  byId("logout").hidden = false;
  byId("message").textContent = "";
}

function resetDelete() {
  deleteButton.classList.remove("confirm");
  deleteButton.textContent = "Delete";
}

function edit(build = {}) {
  editingId = build.id ?? null;
  byId("form-title").textContent = editingId ? "Edit project" : "Add project";
  form.elements.name.value = build.name || "";
  form.elements.stage.value = build.stage || "Planned";
  form.elements.description.value = build.description || "";
  byId("form-meta").textContent = build.created_at ? "Added " + dateFormat.format(new Date(build.created_at)) : "";
  byId("form-error").textContent = "";
  deleteButton.hidden = !editingId;
  resetDelete();
  editor.showModal();
  form.elements.name.focus();
}

async function moveBuild(id, stage) {
  const build = builds.find(item => item.id === id);
  if (!build || build.stage === stage) return;
  const previous = build.stage;
  build.stage = stage;
  render();
  try {
    await request("/robot-builds/" + id, "PATCH", {stage});
  } catch (error) {
    build.stage = previous;
    render();
    byId("message").textContent = error.message;
  }
}

for (const lane of document.querySelectorAll(".lane")) {
  lane.ondragover = event => {
    if (draggedId === null) return;
    event.preventDefault();
    lane.classList.add("drop");
  };
  lane.ondragleave = event => {
    if (!lane.contains(event.relatedTarget)) lane.classList.remove("drop");
  };
  lane.ondrop = event => {
    event.preventDefault();
    lane.classList.remove("drop");
    if (draggedId !== null) moveBuild(draggedId, lane.dataset.stage);
  };
}

byId("login").onsubmit = async event => {
  event.preventDefault();
  const credentials = Object.fromEntries(new FormData(event.target));
  byId("login-error").textContent = "";
  try {
    if (event.submitter?.value === "register") await request("/registration", "POST", credentials);
    const result = await request("/login", "POST", credentials);
    sessionStorage.setItem("buildToken", result.access_token);
    event.target.reset();
    await loadBoard();
  } catch (error) {
    byId("login-error").textContent = error.message;
  }
};

form.onsubmit = async event => {
  event.preventDefault();
  const save = byId("save");
  save.disabled = true;
  try {
    const path = editingId ? "/robot-builds/" + editingId : "/robot-builds";
    await request(path, editingId ? "PATCH" : "POST", Object.fromEntries(new FormData(form)));
    editor.close();
    await loadBoard();
  } catch (error) {
    byId(editor.open ? "form-error" : "message").textContent = error.message;
  } finally {
    save.disabled = false;
  }
};

deleteButton.onclick = async () => {
  if (!deleteButton.classList.contains("confirm")) {
    deleteButton.classList.add("confirm");
    deleteButton.textContent = "Click again to delete";
    return;
  }
  deleteButton.disabled = true;
  try {
    await request("/robot-builds/" + editingId, "DELETE");
    editor.close();
    await loadBoard();
  } catch (error) {
    byId("form-error").textContent = error.message;
  } finally {
    deleteButton.disabled = false;
    resetDelete();
  }
};

byId("search").oninput = render;
byId("add").onclick = () => edit();
byId("cancel").onclick = () => editor.close();
byId("logout").onclick = showAccount;
document.addEventListener("keydown", event => {
  if (event.key === "n" && !editor.open && !byId("projects").hidden && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) {
    event.preventDefault();
    edit();
  }
});

if (sessionStorage.getItem("buildToken")) {
  loadBoard().catch(error => { byId("message").textContent = error.message; });
}
