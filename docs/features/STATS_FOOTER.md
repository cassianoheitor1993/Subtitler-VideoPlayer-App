# Stats Footer Dashboard

The Stats Footer embeds long-running player tasks directly into the status bar so you can monitor and control background activity without extra pop-ups.

## Overview

| Chip | Triggered By | Default Action Button | Cancel Button |
|------|--------------|-----------------------|----------------|
| 🤖 AI | Whisper subtitle generation dialog | Abrir (reopen dialog) | Cancela geração |
| 🌐 Tradução | Legacy translation dialog | Abrir (reopen dialog) | Cancela tradução |
| 📡 Casting | HLS network casting session | Abrir (analytics dialog) | Encerra cast |

Each chip shows the latest status message, a normalized percentage when available, and optional action/cancel buttons.

## User Workflow

1. **Begin a Task** – when AI generation, translation, or casting starts, the footer adds a chip and hides the idle text.
2. **Background Mode** – minimize the dialog or close the prompt; the process keeps running and the chip updates automatically.
3. **Interact** – click **Abrir** to reopen the original dialog or **✕** to cancel directly from the footer.
4. **Completion** – successful or failed tasks remain for a few seconds before auto-clearing. You can also manually dismiss them via the cancel icon once complete.

## Translation Safeguards

- Closing the translation dialog while a job is active prompts you to cancel; if confirmed, the UI hides and waits for a safe shutdown before closing.
- Partial results can still be saved when cancellations happen. The footer message reflects whether a file was produced.
- The footer chip continues to surface progress and cancellation status even when the dialog is hidden.

## AI Generation Behavior

- Minimizing the Whisper dialog hides it instead of disabling the window, keeping menu shortcuts responsive.
- The `🤖` chip mirrors the progress bar and remains interactive after generation finishes so you can reopen the summary.

## Casting Visibility

- Casting chips show the active stream URL and provide a quick link to the streaming analytics dialog.
- Stopping a cast removes the chip immediately; restarting refreshes the display with the new URL.

## Troubleshooting

| Symptom | What to Check |
|---------|----------------|
| Chip does not appear | Ensure the corresponding dialog is using the shared `BackgroundTaskManager` or emits translation signals. |
| Chip stays at 0% | The upstream callback might not provide progress percentages; review the task’s progress emission. |
| Reopen button disabled | Completed tasks may schedule auto-clear; reopen the dialog before the chip disappears if you need the UI again. |

---

For implementation details, see `src/stats_footer.py` and the footer integration points inside `video_player.py`.
