(function () {
    const player = document.getElementById("player");
    const playBtn = document.getElementById("playBtn");
    const stopBtn = document.getElementById("stopBtn");
    const urlInput = document.getElementById("streamUrl");
    const message = document.getElementById("message");

    const STORAGE_KEY = "subtitle_cast_url";
    const DEFAULT_URL = "http://10.0.0.59:8080/stream.m3u8";

    let lastErrorTimestamp = 0;

    function loadStoredUrl() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                urlInput.value = stored;
                return;
            }
        } catch (err) {
            console.warn("Unable to read stored URL", err);
        }

        urlInput.value = DEFAULT_URL;
    }

    function persistUrl(url) {
        try {
            localStorage.setItem(STORAGE_KEY, url);
        } catch (err) {
            console.warn("Unable to store URL", err);
        }
    }

    function normalizeUrl(rawUrl) {
        const trimmed = (rawUrl || "").trim();
        if (!trimmed) {
            return "";
        }

        if (trimmed.startsWith("http://0.0.0.0") || trimmed.startsWith("https://0.0.0.0")) {
            try {
                const currentHost = window.location.host;
                if (currentHost) {
                    const inputUrl = new URL(trimmed);
                    const [hostName, hostPort] = currentHost.split(":");
                    inputUrl.hostname = hostName;
                    if (!inputUrl.port && hostPort) {
                        inputUrl.port = hostPort;
                    }
                    return inputUrl.toString();
                }
            } catch (err) {
                console.warn("Unable to resolve host for 0.0.0.0 replacement", err);
            }
        }

        return trimmed;
    }

    function describeMediaError(mediaError) {
        if (!mediaError) {
            return "Unknown error";
        }

        switch (mediaError.code) {
            case mediaError.MEDIA_ERR_ABORTED:
                return "Playback aborted";
            case mediaError.MEDIA_ERR_NETWORK:
                return "Network error";
            case mediaError.MEDIA_ERR_DECODE:
                return "Decode error";
            case mediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                return "Stream not supported";
            default:
                return `Error code ${mediaError.code}`;
        }
    }

    player.addEventListener("error", () => {
        const now = Date.now();
        if (now - lastErrorTimestamp < 500) {
            return;
        }
        lastErrorTimestamp = now;

        const err = player.error;
        const details = describeMediaError(err);
        message.textContent = `Playback error: ${details}`;
        console.error("Player error", err);
    });

    function destroyHlsAttachment() {
        if (!player.getAttribute("data-hls")) {
            return;
        }

        try {
            window.__subtitleCastDestroyHls?.();
        } catch (err) {
            console.warn("Unable to destroy previous HLS instance", err);
        }

        player.removeAttribute("data-hls");
    }

    function playStream() {
        const normalized = normalizeUrl(urlInput.value || DEFAULT_URL);
        if (!normalized) {
            message.textContent = "Enter a valid stream URL";
            return;
        }

        urlInput.value = normalized;
        persistUrl(normalized);

        destroyHlsAttachment();

        const isHls = normalized.toLowerCase().includes(".m3u8");
        const canPlayNative = player.canPlayType("application/vnd.apple.mpegurl");

        if (isHls && !canPlayNative) {
            message.textContent = "HLS not supported natively. Add hls.js for fallback.";
            return;
        }

        message.textContent = "Loading stream...";
        player.src = normalized;
        player.load();

        const playPromise = player.play();
        if (playPromise && typeof playPromise.then === "function") {
            playPromise.then(() => {
                message.textContent = `Playing ${normalized}`;
            }).catch((err) => {
                console.error("Playback error", err);
                message.textContent = `Playback error: ${err.message}`;
            });
        } else {
            message.textContent = `Playing ${normalized}`;
        }
    }

    function stopStream() {
        destroyHlsAttachment();
        player.pause();
        player.removeAttribute("src");
        player.load();
        message.textContent = "Stopped";
    }

    function onKeyDown(event) {
        switch (event.keyCode) {
            case 13: // OK
                playStream();
                break;
            case 8: // Back
            case 461: // Return on many remotes
                stopStream();
                break;
            default:
                break;
        }
    }

    playBtn.addEventListener("click", playStream);
    stopBtn.addEventListener("click", stopStream);
    document.addEventListener("keydown", onKeyDown);

    loadStoredUrl();
})();
