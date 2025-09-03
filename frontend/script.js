// === CONFIG ===
const API = "http://127.0.0.1:8000";


function getSessionId() {
  let id = localStorage.getItem("session_id");
  if (!id) { id = crypto.randomUUID(); localStorage.setItem("session_id", id); }
  return id;
}
const SESSION_ID = getSessionId();
document.getElementById("sid").textContent = SESSION_ID;

// === I18N ===
const I18N = {
  ru: {
    choose_button: "Выбрать файлы",
  no_file: "Файл не выбран",
  files_selected: "Выбрано файлов: {n}",
    lang_title: "Язык интерфейса",
    message_placeholder: "Задайте вопрос по загруженным файлам...",
    send_button: "Отправить",
    upload_title: "Загрузить файлы",
    index_button: "Индексировать",
    server_label: "Сервер:",
    endpoints_label: "Эндпоинты:",
    session_label: "Сессия:",
    greeting: "Привет! Загрузите файлы справа и задавайте вопросы по их содержимому.",
    uploading: "Загрузка…",
    choose_files_alert: "Выберите файлы.",
    ok_upload: "OK: {name} → {chunks} фрагм. ({ftype}, {bytes} байт)",
    fail_upload: "Не удалось: {name} → {error} (bytes={bytes}, ftype={ftype})",
    net_error: "Сетевая ошибка",
    ask_error: "Ошибка: {error}",
    no_answer: "Ответа в загруженных материалах не найдено.",
    sources_label: "Источники: "
  },
  en: {
    choose_button: "Choose files",
  no_file: "No file selected",
  files_selected: "Selected: {n} file(s)",
    lang_title: "Interface language",
    message_placeholder: "Ask a question about the uploaded files…",
    send_button: "Send",
    upload_title: "Upload files",
    index_button: "Index",
    server_label: "Server:",
    endpoints_label: "Endpoints:",
    session_label: "Session:",
    greeting: "Hello! Upload files on the right and ask questions about their content.",
    uploading: "Uploading…",
    choose_files_alert: "Choose files.",
    ok_upload: "OK: {name} → {chunks} chunks ({ftype}, {bytes} bytes)",
    fail_upload: "Failed: {name} → {error} (bytes={bytes}, ftype={ftype})",
    net_error: "Network error",
    ask_error: "Error: {error}",
    no_answer: "No answer found in the uploaded materials.",
    sources_label: "Sources: "
  },
  pl: {
    choose_button: "Wybierz pliki",
  no_file: "Nie wybrano pliku",
  files_selected: "Wybrano plików: {n}",
    lang_title: "Język interfejsu",
    message_placeholder: "Zadaj pytanie dotyczące wgranych plików…",
    send_button: "Wyślij",
    upload_title: "Prześlij pliki",
    index_button: "Indeksuj",
    server_label: "Serwer:",
    endpoints_label: "Endpointy:",
    session_label: "Sesja:",
    greeting: "Cześć! Prześlij pliki po prawej i zadawaj pytania o ich treść.",
    uploading: "Wysyłanie…",
    choose_files_alert: "Wybierz pliki.",
    ok_upload: "OK: {name} → {chunks} fragmentów ({ftype}, {bytes} bajtów)",
    fail_upload: "Nie udało się: {name} → {error} (bytes={bytes}, ftype={ftype})",
    net_error: "Błąd sieci",
    ask_error: "Błąd: {error}",
    no_answer: "Brak odpowiedzi w przesłanych materiałach.",
    sources_label: "Źródła: "
  }
};

function currentLang() {
  return localStorage.getItem("ui_lang") || document.getElementById("lang").value || "ru";
}
function t(key, vars = {}) {
  const lang = currentLang();
  let s = (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
  for (const [k, v] of Object.entries(vars)) {
    s = s.replaceAll(`{${k}}`, String(v));
  }
  return s;
}
function applyLang(lang) {
  localStorage.setItem("ui_lang", lang);
  document.documentElement.lang = lang;
  document.getElementById("lang").value = lang;

  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });

  // плейсхолдеры/тайтлы
  document.getElementById("message").placeholder = t("message_placeholder");
  document.getElementById("lang").title = t("lang_title");

  // подпись к выбору файлов
  const namesEl = document.getElementById("fileNames");
  const files = document.getElementById("files").files;
  namesEl.textContent = files.length ? t("files_selected", { n: files.length }) : t("no_file");
}


// === UI helpers ===
const chatbox = document.getElementById("chatbox");
function addMessage(text, who = "bot") {
  const el = document.createElement("div");
  el.className = `message ${who}`;
  el.textContent = text;
  chatbox.appendChild(el);
  chatbox.scrollTop = chatbox.scrollHeight;
}
let typing;
function showTyping() {
  typing = document.createElement("div");
  typing.className = "message bot";
  typing.textContent = "…";
  chatbox.appendChild(typing);
  chatbox.scrollTop = chatbox.scrollHeight;
}
function hideTyping() { if (typing) typing.remove(); }

// === ASK ===
async function sendMessage() {
  const input = document.getElementById("message");
  const btn   = document.getElementById("sendBtn");
  const text  = (input.value || "").trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = ""; input.disabled = true; btn.disabled = true; showTyping();

  try {
    const res = await fetch(`${API}/ask`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ query: text, top_k: 5 })
    });
    const data = await res.json();
    hideTyping();

    if (data.error) {
      addMessage(t("ask_error", { error: data.error }), "bot");
      console.error(data.trace || data.error);
      return;
    }

    const msg = (data.answer || "").trim() || t("no_answer");
    addMessage(msg, "bot");

    if (Array.isArray(data.sources) && data.sources.length) {
      addMessage(t("sources_label") + data.sources.join(", "), "bot");
    }
  } catch (e) {
    hideTyping();
    addMessage(t("net_error"), "bot");
  } finally {
    input.disabled = false; btn.disabled = false; input.focus();
  }
}

// === UPLOAD ===
async function uploadOne(f) {
  const fd = new FormData();
  fd.append("file", f, f.name);
  const res = await fetch(`${API}/upload`, { method: "POST", body: fd });
  const data = await res.json();
  console.log("UPLOAD_RESPONSE", data);

  if (data.ok) {
    addMessage(t("ok_upload", { name: f.name, chunks: data.chunks, ftype: data.ftype, bytes: data.bytes }), "bot");
  } else {
    addMessage(
      t("fail_upload", { name: f.name, error: data.error, bytes: data.bytes ?? "?", ftype: data.ftype ?? "?" })
      + (data.preview ? ` preview="${String(data.preview).replace(/\s+/g,' ').slice(0,80)}"` : ""),
      "bot"
    );
  }
}

async function indexFiles() {
  const input = document.getElementById("files");
  if (!input.files.length) { alert(t("choose_files_alert")); return; }

  const btn = document.getElementById("indexBtn");
  btn.disabled = true;

  try {
    for (const f of input.files) {
      await uploadOne(f);
    }
  } catch (e) {
    console.error(e);
    addMessage(t("net_error"), "bot");
  } finally {
    btn.disabled = false;
  }
}

// === Events  initial ===
document.getElementById("sendBtn").addEventListener("click", sendMessage);
document.getElementById("message").addEventListener("keydown", (e)=>{ if(e.key==="Enter") sendMessage(); });
document.getElementById("indexBtn").addEventListener("click", indexFiles);
document.getElementById("lang").addEventListener("change", (e)=> applyLang(e.target.value));


applyLang(localStorage.getItem("ui_lang") || "ru");
addMessage(t("greeting"), "bot");



// сразу после объявления других listeners:
const chooseBtn = document.getElementById("chooseBtn");
const filesInput = document.getElementById("files");
const fileNames = document.getElementById("fileNames");

chooseBtn.addEventListener("click", () => filesInput.click());
filesInput.addEventListener("change", () => {
  fileNames.textContent = filesInput.files.length
    ? t("files_selected", { n: filesInput.files.length })
    : t("no_file");
});
