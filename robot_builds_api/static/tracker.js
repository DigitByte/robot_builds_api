const byId = id => document.getElementById(id);
const editor = byId("editor");
const form = byId("project-form");
let editingId = null;

function showAccount() {
  sessionStorage.removeItem("buildToken");
  if (editor.open) editor.close();
  byId("projects").hidden = true;
  byId("logout").hidden = true;
  byId("account").hidden = false;
}

async function request(path, method = "GET", body) {
  const headers = {};
  const token = sessionStorage.getItem("buildToken");
  if (token) headers.Authorization = "Bearer " + token;
  if (body) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {method, headers, body: JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && token) showAccount();
    const fields = Object.values(data.error.fields || {});
    throw new Error(fields.join(" ") || data.error.message);
  }
  return data;
}

function edit(build = {}) {
  editingId = build.id ?? null;
  byId("form-title").textContent = editingId ? "Edit project" : "Add project";
  form.elements.name.value = build.name || "";
  form.elements.stage.value = build.stage || "Planned";
  form.elements.description.value = build.description || "";
  byId("form-error").textContent = "";
  editor.showModal();
  form.elements.name.focus();
}

async function loadBoard() {
  const {robot_builds} = await request("/robot-builds");
  for (const lane of document.querySelectorAll(".lane")) {
    const builds = robot_builds.filter(build => build.stage === lane.dataset.stage);
    lane.querySelector(".count").textContent = builds.length;
    const cards = lane.querySelector(".cards");
    cards.replaceChildren();
    for (const build of builds) {
      const card = document.createElement("button");
      card.className = "card";
      card.textContent = build.name;
      if (build.description) {
        const notes = document.createElement("small");
        notes.textContent = build.description;
        card.append(notes);
      }
      card.onclick = () => edit(build);
      cards.append(card);
    }
  }
  byId("account").hidden = true;
  byId("projects").hidden = false;
  byId("logout").hidden = false;
  byId("message").textContent = "";
}

byId("login").onsubmit = async event => {
  event.preventDefault();
  const credentials = Object.fromEntries(new FormData(event.target));
  try {
    if (event.submitter?.value === "register") await request("/registration", "POST", credentials);
    const result = await request("/login", "POST", credentials);
    sessionStorage.setItem("buildToken", result.access_token);
    event.target.reset();
    await loadBoard();
  } catch (error) {
    byId("message").textContent = error.message;
  }
};

form.onsubmit = async event => {
  event.preventDefault();
  const save = form.querySelector("button");
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

byId("add").onclick = () => edit();
byId("cancel").onclick = () => editor.close();
byId("logout").onclick = showAccount;
if (sessionStorage.getItem("buildToken")) {
  loadBoard().catch(error => { byId("message").textContent = error.message; });
}
