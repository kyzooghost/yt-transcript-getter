// State management
let lastRequestTime = 0;
const THROTTLE_DELAY = 2000; // 2 seconds between requests

// DOM elements
const formSection = document.getElementById("form-section");
const loadingSection = document.getElementById("loading-section");
const errorSection = document.getElementById("error-section");
const resultsSection = document.getElementById("results-section");
const transcriptForm = document.getElementById("transcript-form");
const urlInput = document.getElementById("url-input");
const submitBtn = document.getElementById("submit-btn");
const toast = document.getElementById("toast");

// Error elements
const errorMessage = document.getElementById("error-message");
const errorSuggestion = document.getElementById("error-suggestion");
const retryBtn = document.getElementById("retry-btn");

// Results elements
const newVideoBtn = document.getElementById("new-video-btn");
const videoIdSpan = document.getElementById("video-id");
const languageSpan = document.getElementById("language");
const generatedBadge = document.getElementById("generated-badge");
const snippetsContainer = document.getElementById("snippets-container");
const fullTranscript = document.getElementById("full-transcript");
const copyFullBtn = document.getElementById("copy-full-btn");
const downloadFullBtn = document.getElementById("download-full-btn");

// Utility functions
function showSection(section) {
    [formSection, loadingSection, errorSection, resultsSection].forEach((s) => {
        s.classList.add("hidden");
    });
    section.classList.remove("hidden");
}

function showToast(message = "Copied!") {
    toast.textContent = message;
    toast.classList.remove("hidden");
    setTimeout(() => {
        toast.classList.add("hidden");
    }, 2000);
}

function validateURL(url) {
    const patterns = [
        /(?:https?:\/\/)?(?:www\.)?youtu\.be\/[a-zA-Z0-9_-]{11}/,
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?.*v=[a-zA-Z0-9_-]{11}/,
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/live\/[a-zA-Z0-9_-]{11}/,
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/[a-zA-Z0-9_-]{11}/,
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/[a-zA-Z0-9_-]{11}/,
    ];

    return patterns.some((pattern) => pattern.test(url));
}

function checkThrottle() {
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;

    if (timeSinceLastRequest < THROTTLE_DELAY) {
        const remainingTime = Math.ceil((THROTTLE_DELAY - timeSinceLastRequest) / 1000);
        return { allowed: false, remainingTime };
    }

    return { allowed: true };
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast("Copied!");
    } catch (err) {
        console.error("Failed to copy:", err);
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand("copy");
            showToast("Copied!");
        } catch (e) {
            showToast("Copy failed");
        }
        document.body.removeChild(textArea);
    }
}

function downloadMarkdown(content, filename) {
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function createSnippetElement(snippet) {
    const snippetDiv = document.createElement("div");
    snippetDiv.className = "snippet-item";

    const header = document.createElement("div");
    header.className = "snippet-header";

    const titleDiv = document.createElement("div");
    const title = document.createElement("div");
    title.className = "snippet-title";
    const startMinute = Math.floor((parseInt(snippet.start_time.split(":")[0]) * 60 + parseInt(snippet.start_time.split(":")[1])));
    const endMinute = Math.ceil((parseInt(snippet.end_time.split(":")[0]) * 60 + parseInt(snippet.end_time.split(":")[1])));
    title.textContent = `Minutes ${startMinute}-${endMinute}`;

    const meta = document.createElement("div");
    meta.className = "snippet-meta";
    meta.textContent = `${snippet.start_time} - ${snippet.end_time} (${snippet.duration_minutes} min)`;

    titleDiv.appendChild(title);
    titleDiv.appendChild(meta);

    const expandIcon = document.createElement("div");
    expandIcon.className = "expand-icon";
    expandIcon.textContent = "▼";

    header.appendChild(titleDiv);
    header.appendChild(expandIcon);

    const content = document.createElement("div");
    content.className = "snippet-content";

    const body = document.createElement("div");
    body.className = "snippet-body";

    const controls = document.createElement("div");
    controls.className = "snippet-controls";

    const copyBtn = document.createElement("button");
    copyBtn.className = "action-btn";
    copyBtn.textContent = "Copy Snippet";
    copyBtn.onclick = () => copyToClipboard(snippet.markdown);

    const downloadBtn = document.createElement("button");
    downloadBtn.className = "action-btn";
    downloadBtn.textContent = "Download Snippet";
    downloadBtn.onclick = () => downloadMarkdown(snippet.markdown, `snippet-${snippet.index}.md`);

    controls.appendChild(copyBtn);
    controls.appendChild(downloadBtn);

    const text = document.createElement("pre");
    text.className = "snippet-text";
    text.textContent = snippet.markdown;

    body.appendChild(controls);
    body.appendChild(text);
    content.appendChild(body);

    snippetDiv.appendChild(header);
    snippetDiv.appendChild(content);

    // Toggle accordion
    header.onclick = () => {
        snippetDiv.classList.toggle("expanded");
    };

    return snippetDiv;
}

function renderResults(data) {
    // Update video info
    videoIdSpan.textContent = data.video_id;
    languageSpan.textContent = data.language;

    if (data.is_generated) {
        generatedBadge.textContent = "Auto-generated";
        generatedBadge.style.display = "inline-block";
    } else {
        generatedBadge.style.display = "none";
    }

    // Clear and populate snippets
    snippetsContainer.innerHTML = "";
    data.snippets.forEach((snippet) => {
        const snippetElement = createSnippetElement(snippet);
        snippetsContainer.appendChild(snippetElement);
    });

    // Set full transcript
    fullTranscript.textContent = data.full_transcript;

    // Show results and scroll to them
    showSection(resultsSection);
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function showError(error, suggestion) {
    errorMessage.textContent = error;
    errorSuggestion.textContent = suggestion;
    showSection(errorSection);
}

async function processTranscript(url) {
    try {
        const response = await fetch("/api/transcript", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (data.success) {
            renderResults(data);
        } else {
            showError(data.error, data.suggestion);
        }
    } catch (error) {
        console.error("Network error:", error);
        showError("Network error occurred.", "Please check your connection and try again.");
    }
}

function resetForm() {
    urlInput.value = "";
    showSection(formSection);
    urlInput.focus();
}

// Event listeners
transcriptForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const url = urlInput.value.trim();

    // Validate URL
    if (!validateURL(url)) {
        showError("Invalid YouTube URL", "Please provide a valid YouTube video URL (e.g., youtube.com/watch?v=... or youtu.be/...)");
        return;
    }

    // Check throttle
    const throttleCheck = checkThrottle();
    if (!throttleCheck.allowed) {
        showError(`Please wait ${throttleCheck.remainingTime} second(s) before making another request.`, "This prevents overwhelming the server.");
        return;
    }

    // Update last request time
    lastRequestTime = Date.now();

    // Show loading state
    submitBtn.disabled = true;
    showSection(loadingSection);

    // Process transcript
    await processTranscript(url);

    // Re-enable button
    submitBtn.disabled = false;
});

retryBtn.addEventListener("click", resetForm);
newVideoBtn.addEventListener("click", resetForm);

copyFullBtn.addEventListener("click", () => {
    copyToClipboard(fullTranscript.textContent);
});

downloadFullBtn.addEventListener("click", () => {
    downloadMarkdown(fullTranscript.textContent, "full-transcript.md");
});

// Focus input on load
urlInput.focus();
