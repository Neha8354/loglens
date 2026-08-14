let selectedFile = null;


function byId(id) {
    return document.getElementById(id);
}


function setText(id, value) {
    const element = byId(id);

    if (element) {
        element.textContent = value;
    }
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("loglens-theme", theme);

    byId("theme-toggle").textContent =
        theme === "dark" ? "☼" : "◐";
}


function configureTheme() {
    const savedTheme = localStorage.getItem("loglens-theme");

    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        const preferredTheme = window.matchMedia(
            "(prefers-color-scheme: dark)"
        ).matches
            ? "dark"
            : "light";

        setTheme(preferredTheme);
    }

    byId("theme-toggle").addEventListener("click", () => {
        const currentTheme =
            document.documentElement.getAttribute("data-theme");

        setTheme(currentTheme === "dark" ? "light" : "dark");
    });
}


function setSelectedFile(file) {
    selectedFile = file;

    if (!file) {
        setText("selected-file", "No file selected");
        byId("upload-button").disabled = true;
        return;
    }

    setText("selected-file", file.name);
    byId("upload-button").disabled = false;
}


async function loadSummary() {
    const response = await fetch("/api/summary");
    const data = await response.json();

    setText("total-events", data.total);
    setText("critical-events", data.critical);
    setText("warning-events", data.warnings);
    setText("failed-logins", data.failed_logins);
}


async function populateSelect(url, selectId, firstOption) {
    const response = await fetch(url);
    const values = await response.json();

    const select = byId(selectId);
    const currentValue = select.value;

    select.innerHTML = `<option value="">${firstOption}</option>`;

    values.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
    });

    select.value = currentValue;
}


async function loadFilters() {
    await Promise.all([
        populateSelect(
            "/api/services",
            "service-filter",
            "All services"
        ),
        populateSelect(
            "/api/sources",
            "source-filter",
            "All sources"
        )
    ]);
}


async function loadEvents() {
    const parameters = new URLSearchParams({
        search: byId("search-input").value.trim(),
        severity: byId("severity-filter").value,
        service: byId("service-filter").value,
        source: byId("source-filter").value
    });

    const response = await fetch(`/api/events?${parameters}`);
    const events = await response.json();
    const eventList = byId("event-list");

    if (events.length === 0) {
        eventList.innerHTML = `
            <tr>
                <td colspan="7">No events match the selected filters.</td>
            </tr>
        `;
        return;
    }

    eventList.innerHTML = events.map((event) => `
        <tr>
            <td>${escapeHtml(event.timestamp)}</td>
            <td>${escapeHtml(event.service)}</td>
            <td>${escapeHtml(event.message)}</td>
            <td>${escapeHtml(event.source_file)}</td>
            <td>
                <span class="badge ${event.severity.toLowerCase()}">
                    ${escapeHtml(event.severity)}
                </span>
            </td>
            <td>
                <span class="badge ${event.status.toLowerCase()}">
                    ${escapeHtml(event.status)}
                </span>
            </td>
            <td>
                <button
                    class="event-action"
                    onclick="updateEventStatus(${event.id}, 'ACKNOWLEDGED')"
                    ${event.status !== "OPEN" ? "disabled" : ""}
                >
                    Acknowledge
                </button>
                <button
                    class="event-action"
                    onclick="updateEventStatus(${event.id}, 'RESOLVED')"
                    ${event.status === "RESOLVED" ? "disabled" : ""}
                >
                    Resolve
                </button>
            </td>
        </tr>
    `).join("");
}


async function updateEventStatus(eventId, status) {
    const response = await fetch(`/api/events/${eventId}/status`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ status })
    });

    if (!response.ok) {
        alert("Unable to update the event.");
        return;
    }

    await loadEvents();
}


async function importSampleLogs() {
    const button = byId("import-button");
    button.disabled = true;
    button.textContent = "Processing…";

    await fetch("/api/import", {
        method: "POST"
    });

    await refreshDashboard();

    button.disabled = false;
    button.textContent = "Process Sample Logs";
}


async function uploadLogFile() {
    if (!selectedFile) {
        return;
    }

    const uploadStatus = byId("upload-status");
    const uploadButton = byId("upload-button");
    const formData = new FormData();

    formData.append("log_file", selectedFile);

    uploadButton.disabled = true;
    uploadStatus.textContent = "Processing uploaded log file…";

    try {
        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            uploadStatus.textContent = data.error;
            return;
        }

        uploadStatus.textContent =
            `${data.inserted_count} new events imported from ${data.source_file}.`;

        byId("log-file").value = "";
        setSelectedFile(null);

        await refreshDashboard();
    } catch (error) {
        uploadStatus.textContent = "Unable to upload the file.";
    } finally {
        uploadButton.disabled = false;
    }
}


function clearFilters() {
    byId("search-input").value = "";
    byId("severity-filter").value = "";
    byId("service-filter").value = "";
    byId("source-filter").value = "";

    loadEvents();
}


async function refreshDashboard() {
    try {
        await loadSummary();
        await loadFilters();
        await loadEvents();
    } catch (error) {
        console.error("Unable to refresh LogLens:", error);
    }
}


function configureUploadZone() {
    const uploadZone = byId("upload-zone");
    const fileInput = byId("log-file");

    fileInput.addEventListener("change", () => {
        setSelectedFile(fileInput.files[0]);
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        uploadZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            uploadZone.classList.add("drag-over");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        uploadZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            uploadZone.classList.remove("drag-over");
        });
    });

    uploadZone.addEventListener("drop", (event) => {
        const file = event.dataTransfer.files[0];

        if (file) {
            setSelectedFile(file);
        }
    });
}


configureTheme();
configureUploadZone();

byId("filter-button").addEventListener("click", loadEvents);
byId("clear-button").addEventListener("click", clearFilters);
byId("import-button").addEventListener("click", importSampleLogs);
byId("upload-button").addEventListener("click", uploadLogFile);

byId("search-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        loadEvents();
    }
});

refreshDashboard();