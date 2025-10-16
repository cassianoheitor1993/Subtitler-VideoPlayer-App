(function () {
    const player = document.getElementById("player");
    const playBtn = document.getElementById("playBtn");
    const stopBtn = document.getElementById("stopBtn");
    const urlInput = document.getElementById("streamUrl");
    const message = document.getElementById("message");

    const STORAGE_KEY = "subtitle_cast_url";

    function loadStoredUrl() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                urlInput.value = stored;
            }
        } catch (err) {
            console.warn("Unable to read stored URL", err);
        }
    }

    function persistUrl(url) {
        try {
            localStorage.setItem(STORAGE_KEY, url);
        } catch (err) {
            console.warn("Unable to store URL", err);
        }
    }

    function playStream() {
        const url = urlInput.value.trim();
        if (!url) {
            message.textContent = "Enter a valid stream URL";
            return;
        }

        persistUrl(url);
        player.src = url;
        player.load();
        const playPromise = player.play();
        if (playPromise && typeof playPromise.then === "function") {
            playPromise.then(() => {
                message.textContent = `Playing ${url}`;
            }).catch((err) => {
                console.error("Playback error", err);
                message.textContent = `Playback error: ${err.message}`;
            });
        } else {
            message.textContent = `Playing ${url}`;
        }
    }

    function stopStream() {
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
