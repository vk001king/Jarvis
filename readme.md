# ⚙️ MARK LV (55)
### The Ultimate Cross-Platform Personal AI Assistant — By FatihMakes

> 📺 **[Watch the full setup video on YouTube](https://www.youtube.com/@FatihMakes)**

A real-time voice AI that can hear, see, speak, and control your computer — on any OS. Supports Windows, macOS, and Linux. Built on the Gemini Live API for native audio streaming, delivering zero subscriptions and total digital autonomy.

---

## ✨ Overview

Mark LIV gave the assistant a face. **Mark LV gives it a screen — and the stamina to keep working when a model goes down.**

Say "play the new Dune trailer" and the video appears **where the avatar was**, in the HUD itself, muted until you ask for sound. A YouTube link, a local file, a direct URL or just a description to search for: they all land in the same place, and JARVIS tells you it is coming *before* the picture arrives instead of going quiet for five seconds.

Underneath, every Gemini call in the app now goes through **one ladder of nine models**, ordered by measured response time rather than guesswork. When a model hits its quota, times out or disappears, the next rung takes the call and the dead one is put on a cooldown so nobody pays for it twice. Before this release, sixteen files named their own model, twenty-six times, with **no timeout at all** — one unwell alias could hang a request forever.

The release also draws a line through the bundled skill list. **Everything JARVIS ships with now drives the computer** — applications, files, the browser, the desktop, the screen. Five skills that served one hobby or one trade left the list, which is a thousand tokens the model no longer reads on every connection, and five fewer wrong tools for it to reach for.

It's not just an assistant — it's an extension of your digital life.

---

## 🚀 Capabilities

### Core Features
| Feature | Description |
|---|---|
| 🧑‍🎤 Holographic Avatar | An animated human head in the HUD — real facial geometry, lit and drawn in software, no GPU or extra packages |
| 👄 Real Lip-Sync | ~50 mouth shapes a second from the audio's formants **and** the transcript — closures, spreads and rounds, not a volume meter |
| 🌍 Language-Free Mouth | Articulation is derived by Unicode reduction, so Latin, Cyrillic and Greek scripts all work from one rule set — and scripts that hide pronunciation fall back cleanly |
| 🙂 Facial Acting | Brows track the phrase, gaze saccades between fixations, natural blinking, a small nod on stressed syllables |
| 😐 Face as Status | Looks away while thinking, meets your eyes while listening, lids fall while asleep, glances down at new content |
| 🎚️ Push-to-Talk | Hold **Ctrl+Space** and the mic opens — closed the rest of the time. Truly global on Windows, window-scoped elsewhere |
| 🔇 Self-Echo Guard | Never answers its own last sentence: the tail of its own voice is recognised and dropped without muting you |
| 🪪 Runtime Self-Knowledge | Name, OS, abilities **and limits** are generated from the live system each session — rename it or add a plugin and it knows |
| 🎙️ Wake Word | Local **"Hey Jarvis"** detection — sleeps until called, auto-sleeps after 2 min of silence, and never streams audio while asleep |
| ⚡ Instant Acknowledgment | Speaks a short, context-aware reply in **your language** the instant a longer task starts — no more silent waiting |
| 🚀 Faster Live Engine | Runs on **Gemini 3.1 Flash Live** — roughly 2× faster time-to-first-word than the previous model |
| 🧩 Self-Describing Skills | Every bundled skill declares its own `TOOL` dict + handler and is auto-discovered at launch — adding one is a single file |
| 🧠 Recallable Memory | No size limit and nothing silently forgotten — the prompt carries what fits, the rest is looked up on demand from a local search |
| 👁️ Memory Panel | See every fact JARVIS has stored about you, when it learned it, and delete any of it in one click |
| ↩️ Undo | Take back what the assistant did — files it moved, renamed, created or wrote, and settings it changed |
| ⚠️ Real Confirmation | Shutdown, restart and WiFi wait for a button **you** press — the model cannot confirm its own irreversible actions |
| 🎧 Audio Device Picker | Choose the microphone and speakers by name, filtered to the short list your OS shows — and measured, so every entry actually works |
| 🔗 Session Continuity | A dropped connection, a voice change or a device change no longer wipes the conversation |
| 🧩 Plugin System | Drop a single `.py` file into `plugins/` — JARVIS learns a new skill on next launch |
| 🔌 MCP Servers | Connect trusted local stdio or remote Streamable HTTP MCP servers; tools join Gemini's live tool list |
| 📺 Video on the HUD | Plays YouTube, a local file or any video URL **where the avatar sits** — starts muted, sound on request |
| 🪜 Model Ladder | Nine Gemini models in one measured order — a quota, a timeout or an outage steps to the next rung instead of failing |
| 🎙️ Real-time Voice | Ultra-low latency conversation in any language via Gemini Live API |
| 🎨 Live Theming | Recolour the entire HUD from a hue wheel or hex — the avatar retints with it |
| 🖥️ Command Center UI | Multi-panel desktop dashboard for live system health, voice activity, tools, quick commands, file handoff, and emergency controls |
| 🌐 God's Eye Observatory | A separate desktop workspace for public ISS orbital telemetry, NOAA Kp/GOES space-weather readings, an optional muted NASA live-video corner, and informational market charts |
| 〰️ Reactive HUD | Waveform pulses to real audio — your mic while listening, JARVIS while speaking |
| 🎙️ Voice Picker | Choose from 5 native Gemini voices and switch live from the UI — no restart |
| ♾️ Unlimited Sessions | Sliding-window context compression — one conversation can last for hours |
| 🖥️ System Control | Launch apps, adjust volume/brightness, WiFi, shortcuts, power — all by voice |
| 🧩 Autonomous Tasks | High-level planning for complex multi-step goals via agent mode |
| 👁️ Visual Awareness | Screen capture and webcam vision piped into your main Gemini session, labelled by source |
| 🧠 Persistent Memory | Deeply remembers projects, preferences, and personal context across sessions |
| ⌨️ Hybrid Input | Seamlessly switch between keyboard typing and voice commands |
| 🌅 Morning Briefing | On first boot: greets you, reads the time, recaps yesterday, and fetches live news |
| 🔔 Proactive 2.0 | Time-aware, context-aware check-ins — knows the time of day, your projects, and what you've been discussing |
| 🗓️ Session Memory | Summarises each conversation and mentions it naturally next morning — consumed after use, never repeats |
| 👁️‍🗨️ Background Monitoring | User-configured topic watching — checks for new headlines once a day and alerts naturally |
| 📊 Hardware Monitoring | Continuous CPU, RAM, GPU and temperature telemetry with localized voice alerts |
| 🌤️ Weather Report | Live weather data for your city, personalized from memory |
| 🗺️ Dynamic Content Panel | Scrollable display layer beneath the HUD that renders web results, news, and search data |
| 🔍 Multi-Mode Web Search | `news` / `research` / `price` / `compare` / `search` — Gemini Grounded first, DDG fallback |
| ⏰ Smart Reminders | OS-native scheduled notifications (Windows Task Scheduler / macOS LaunchAgent / Linux systemd) |
| 📂 File Processor | Read, summarize, and answer questions about local files |
| 🌐 Browser Control | Open URLs, navigate tabs, and interact with the browser by voice |
| 📨 Send Message | Compose and send messages through WhatsApp, Telegram, and more |
| 🖱️ Desktop Control | Taskbar, window management, and desktop-level operations |
| 🧑‍💻 Silent Language Memory | Detects spoken language on first use — all future sessions adapt automatically |
| 📱 Remote Dashboard | Control the assistant from your phone via QR code pairing |
| ⚡ Auto-Start on Boot | Registers with the OS startup system (registry / LaunchAgent / .desktop) |
| 📋 Clipboard Intelligence | Copy any text → floating panel with Translate / Summarise / Explain / Fix |
| 🪪 Assistant Customization | Change the assistant name, your name, voice, and colour from the UI — takes effect immediately |

---

### 📱 Install the mobile app

The remote dashboard installs as a home-screen app (PWA), so no app-store download is needed. Start JARVIS on your computer, open **Remote Control**, then scan its QR code with your phone while both devices are on the same network. Keep the desktop app running. In the dashboard, tap **INSTALL** and follow the browser-specific steps; supported Android browsers can show a direct install prompt. On iPhone/iPad, open the paired dashboard in Safari and use **Share → Add to Home Screen → Add**. The first visit must be online and complete any local HTTPS certificate confirmation shown by the browser.

The installed app includes a JARVIS-style animated command center, quick desktop actions, wake/sleep/interrupt controls, file sharing, and an optional two-way voice call that plays JARVIS's replies on the phone. During a call, JARVIS audio is routed exclusively to the phone (never falls back to the computer speaker), desktop-microphone audio and unrelated automatic alerts are paused, and other remote text commands are ignored. Live call transcripts are also kept out of the phone's command chat so replies are not duplicated there while being spoken. To start a call from the computer, use **CALL MY PHONE** in the desktop command center; answer in the phone app to grant microphone access and begin two-way conversation. The call screen shows its duration and connection state, and provides microphone mute, end-call, retry, and—where the browser exposes output routing—speaker/headset selection. You can also ask JARVIS to call your paired phone when a task finishes. Enable phone alerts to receive an in-app attention/call prompt while the phone dashboard is connected. These are app calls, not cellular calls: the desktop must be running, and mobile browsers may pause the connection in the background or stop it after the app closes. The app shell can reopen offline, but assistant features still require the desktop connection; credentials and conversation data are never cached for offline use.

## 🆕 What's New in Mark LV

The original Mark LV release added `yt-dlp` only to turn a YouTube page into something Qt can play. The MCP manager in this update also uses the official `mcp` Python SDK for local stdio and remote Streamable HTTP connections.

### The display

#### 📺 Video where the face is
The HUD already had a surface that takes the centre of the screen and gives it back: the camera. Video shares that same stack, so the avatar, the live camera and a video can never be on screen at once — and a video always lands exactly where you are already looking.

It accepts **a local file, a direct media URL, a YouTube link, or just a description** ("play the new Dune trailer") and searches for it. It **starts muted every time**, because a soundtrack talking over the assistant is the one way this feature could make JARVIS worse rather than better. You turn the sound on by asking, or from the button in the video header.

**It answers before it opens.** Resolving what to play takes seconds nothing can remove — measured at 2.0s for a link and 3.3s for a spoken phrase, plus buffering. Restricting yt-dlp to a lighter client was tried and made it worse: the fast clients came back with zero usable formats. So the seconds stay, and what changed is where you spend them — listening to JARVIS say it is coming, instead of watching nothing happen. Say "stop" during those seconds and the video is cancelled before it ever reaches the screen.

#### 🔀 Two streams, one picture
The first version asked YouTube for a format carrying both picture and sound and got *"Requested format is not available"*. That was not a bad selector; it was a wrong assumption. Checked against three videos — including the oldest upload on the site — **every one offered zero combined formats.** Picture and sound are separate streams now.

So there are two players running together, with a timer that corrects any drift over 300 ms. And the audio track is chosen on **language first, bitrate second** — because YouTube auto-dubs a great many videos and ships every dub at the *same* bitrate as the original: measured on one video, English at 129.483 and Arabic, Bangla, German, Spanish, French, Hindi and Indonesian all at 129.482. Sorting on bitrate alone came down to a thousandth of a kilobit, so the same video would play in Arabic one time and English the next for no reason you could see. It now reads YouTube's own original-track marker first.

#### 🔇 It stopped hearing the film
The microphone is open while a video plays, so the moment you turn the sound on, JARVIS starts answering the film. The mic now mutes itself when the video's sound goes on and unmutes when it goes off — and it says so in the activity log rather than going deaf silently.

#### 🖥️ Command center, at a glance
The desktop opens to a responsive, neon-blue command center: live CPU, memory, storage, network and GPU meters; an animated reactor core; voice activity; the actual MCP/plugin connection state; recent activity; file handoff; one-tap system/screen checks; and stop/remote controls. A live four-stage workflow trace follows listening, thinking, tool use and response, while subtle gradient accents distinguish dashboard cards. The reactor is the default centerpiece, and the animated face remains available from the controls drawer. Narrower screens scroll the side panels instead of hiding controls.

#### 🌐 God's Eye observatory
Open **GOD'S EYE** from the desktop header for a separate orbital workspace. Its schematic globe marks the public ISS position and shows altitude, velocity, footprint, and visibility; NOAA SWPC provides the planetary K-index and GOES X-ray class; and a corner player can resolve NASA's public live channel when one is available. If no channel is live or Qt playback is unavailable, the official NASA Live schedule opens in the browser. NASA's ISS-view streams and Astronomy Picture of the Day are linked from the workspace.

The market panel plots five-minute history for common index, crypto, commodity, and equity symbols, with a ticker field for other Yahoo Finance symbols. Quotes are informational and may be delayed; JARVIS does not place trades or provide investment advice. Feed requests begin only when the workspace is opened or refreshed, use public endpoints without credentials, and report unavailable sources instead of showing invented values. The globe is schematic and is not a navigation or people-tracking map.

#### 📚 Research & Office Studio
Open **RESEARCH STUDIO** for PhD-oriented proposal, literature-review, study-comparison, methods/survey, dataset-analysis, image-to-table, Word-paper, Excel-workbook, and defense-presentation workflows. The shortcuts send structured requests to JARVIS; research tasks are expected to use the available web-search and file-processing actions before writing. The app uses its configured Gemini model/fallback ladder and available tools, not an independent multi-vendor model ensemble.

The `office_studio` action creates editable `.docx`, `.xlsx`, and `.pptx` files with sections, tables, user-provided figures, references, and charts. It can import CSV/XLSX data into a new workbook and extend an existing Office file as a separate revision copy. Existing files are never overwritten. The workspace can open a generated file in the operating system's default Office application for live user editing; it does not silently automate or modify an already-open document.

Academic accuracy is not guaranteed by an AI system. The workflows ask JARVIS to avoid invented citations, distinguish evidence from interpretation, flag uncertainty, and preserve source links. Verify references, quotations, calculations, study methods, and institutional ethics requirements before relying on or submitting generated work. Review files for sensitive information before sending them to any configured AI or search service.

#### 🎛 Two drawers instead of one
⚙ **SETUP** holds the things you set once — remote control, desktop shortcut, auto-start and customisation. 🎛 **CONTROLS** holds the switches you flick daily — fullscreen, morning brief, wake word, sleep, push-to-talk, HUD style. Only one is open at a time, and each sits under its own header button.

The panel used to stutter when it opened, and the obvious explanation — too many buttons — was wrong. Measured, the **first** wake-word state check took **2.104 seconds**, because it imported `openwakeword` on the UI thread the moment the drawer was built. That import now happens off-thread at boot, and the drawer opens instantly whether it has six buttons or sixteen.

> The drawer also used to vanish *behind* the video. `QVideoWidget` creates a native child window, and no Qt overlay can be drawn on top of one. The video is now a `QGraphicsVideoItem` inside a graphics view — same picture, and the interface stays where it belongs.

### Staying up

#### 🪜 Every Gemini model, in one ladder
Every one-shot Gemini call in the app now goes through `core/gemini.py`. Before this, **sixteen files named their own model — twenty-six times — and not one of them set a timeout.** When a single alias went unwell, the call did not fail; it hung.

The ladder is nine models deep, ordered by **measurement rather than guesswork**:

| Model | Measured | Model | Measured |
|---|---|---|---|
| `gemini-3.5-flash-lite` | 0.56s | `gemini-2.5-flash` | 0.67s |
| `gemini-3.1-flash-lite` | 0.60s | `gemini-2.5-flash-lite` | 0.74s |
| `gemini-flash-lite-latest` | 0.60s | `gemini-3.5-flash` | 1.13s |
| `gemini-3-flash-preview` | 504 after 14.7s | `gemini-3.6-flash` | 504 after 12.0s |
| `gemini-flash-latest` | 503 UNAVAILABLE | | |

The three that fail were **not deleted** — a model that is unwell today is a real rung tomorrow. They sit at the bottom, and a **cooldown** decides how long a failure is believed:

| What happened | Rested for | Why |
|---|---|---|
| Quota exhausted (429) | 5 minutes | Quotas refill |
| No answer (503 / 504 / DEADLINE_EXCEEDED) | 30 minutes | An outage outlasts a retry |
| Not found, or no access (404) | 6 hours | Your key does not have it, and won't in a minute |

That middle row is where the time was going. Only quota and 404 used to be cooled, so the 14-second wait on a dead model was paid **on every single call**. Measured after the fix: first call 13.15s, second 1.98s, third 1.16s — **11.2 seconds saved on every call from then on.**

**The Live model is deliberately not on this ladder.** Live models are not drop-in replacements for one another; they accept different config fields, and the same API key also exposes transcribe-live, live-translate and robotics-streaming models that will happily connect and then not behave like an assistant. So Live has exactly **two** rungs — the current model, and the one this project used before it — and it steps only on quota or loss of access. Never on a network blip or a bad key, which would otherwise walk the whole list into the same wall.

### The shape

#### 🧩 Everything bundled drives the computer
The bundled skill list had grown to seventeen, and some of it was nobody's business but its author's. **Not everyone updates games; everyone opens applications.**

Mark LV trims it to **twelve**, and every one of them does the same kind of thing: drive this machine. Applications, the browser, files, the desktop, the screen, the clock, the weather, the display. The rule is written into the project tree, so the next skill lands in the right folder without anyone having to ask.

This is not only tidiness. Every bundled skill is declared to the model on **every** connection, whether you ever use it or not. The declarations sent at startup dropped from **16,827 characters to 12,907** — roughly a thousand tokens off every session, and five fewer wrong tools for the model to reach for.

### 🩹 Fixes
* An unanswering model was retried on **every call**, at 12–15 seconds a time, because only quota and 404 failures were ever cooled down. 503/504 now rest for 30 minutes — **11.2 seconds saved per call**.
* One-shot Gemini calls had **no timeout anywhere**, in any of the sixteen files that made them. Every call now carries a deadline of at least 10 seconds.
* YouTube playback failed outright with *"Requested format is not available"* — it was asking for a combined stream that no longer exists.
* Videos played in a **random language**, because YouTube's auto-dubs carry the same bitrate as the original track.
* The settings drawer **stuttered on first open** — a 2.1-second `openwakeword` import on the UI thread, not the button count it looked like.
* The settings drawer opened **underneath the video**, because `QVideoWidget` creates a native window.
* JARVIS **answered the video's soundtrack.** The microphone now follows the video's sound.
* Qt's multimedia backend printed an ffmpeg banner to the console on every play, containing the **signed streaming URL with the viewer's IP address in it**. Silenced at startup.
* **Every launch paid 201 ms for a plugin nobody had asked to use.** Discovery executes every file in `plugins/`, and `youtube_video` imported `requests` and `youtube_transcript_api` at module scope. Deferring one of them would have saved nothing — the transcript library imports `requests` itself. Both are now checked with `find_spec`, which answers "is it installed?" without executing anything, and loaded on first use: **plugin discovery 211 ms → 39 ms**.
* A plugin that needed a file from a **newer Mark** was rejected with *"pip install core"*. The loader could not tell this project's own packages from a third-party one, so it told people to install a same-named stranger from an index — wrong, and a supply-chain hazard dressed up as a fix. First-party names now say the app is behind the plugin and that there is nothing to install.

### 🛡️ Hardening

A pass over the parts that hold your data, each change covered by a test in `tests/`.

* **`.gitignore` was not ignoring the secrets.** Each rule had its explanation written after it on the same line, and git only reads `#` as a comment at the *start* of a line — so `config/api_keys.json          # your Gemini API key…` was one long pattern that matched nothing. The API key, MCP credentials, TLS private key and OAuth tokens were all offered to `git add`. The comments now sit above their rules, and a test asks git itself whether each secret path is ignored.
* **A damaged config no longer costs you the API key.** Every setter read the file, fell back to `{}` on any error, and wrote that back — so one bad byte, followed by one changed setting, replaced the key and every plugin token with a single field. Config and memory are now written atomically (temporary file, then rename), saved under one lock, and an unreadable file is copied to `<name>.corrupt-<time>` before anything replaces it. The saved files are owner-only on macOS and Linux.
* **Re-running setup kept nothing.** The setup screen wrote a fresh two-key file over the existing config. It appears whenever a field is missing, so that meant losing plugin tokens, voice and colour to fix one value. It merges now.
* **Saves could erase each other.** A fact stored while the daily topic check was on the network was overwritten when the check finished, and a topic added in that window disappeared. Every change to the memory file is now one locked read-modify-write.
* **Credentials are kept out of memory.** Telling the assistant a token used to file it in `memory/long_term.json` in plain text, list it in the memory panel and send it back to the model on every matching recall. Machine-issued credentials (GitHub, Google, Slack, AWS, JWTs, private keys) are now refused with a pointer to the plugin settings panel, and any already on disk are masked in recall. A password you ask it to remember is still your call — the guard matches formats, not key names.
* **Facts can no longer land in the bookkeeping.** `save_memory` accepted any category name, so a fact filed under `sessions` or `monitors` overwrote that section, and one filed under an invented name was stored but never shown to the model. Unknown categories go to `notes`.
* **The phone dashboard counts wrong keys.** The pairing key is six characters and the server listens on the whole LAN; nothing limited guesses. Eight failures from one address now lock it out for five minutes. Malformed request bodies answer `400` instead of crashing the handler, commands are capped at 8,000 characters, and the session table is bounded.
* **Topics in non-Latin scripts collided.** The monitor filed topics under an ASCII slug, so every topic written in Japanese, Arabic or Cyrillic reduced to the same empty key and the second one was reported as already monitored.
* **Two Research Studio cards had no styling.** A doubled `}}` outside an f-string made Qt reject both stylesheets on every launch.

> Built on the Mark LI–LIV foundation: the **🧑‍🎤 Holographic Avatar**, **👄 Lip-Sync**, **🎚️ Push-to-Talk**, **🔇 Self-Echo Guard**, **🧩 Plugin System**, **♾️ Unlimited Sessions**, **🎨 Live Theming** and **🎙️ Wake Word** are all still here.

---

## 🔄 The Foundation Update — in every Mark from LII

These four landed across **Mark LII, LIII, LIV and LV at the same time**, after each of those releases had already shipped. They are not what any one of those versions originally introduced; they are the floor all of them now stand on, so moving up a Mark never costs you something the one below it had.

No new dependencies. No bundled asset files. No hardcoded language, and nothing that assumes one operating system.

### 🧠 A memory that actually remembers

The store was capped at **2,200 characters — the whole memory, not per entry** — because all of it was pasted into the system prompt on every connect, so growing the memory grew every request. When it filled, the oldest entries were deleted and one line was printed to a console nobody reads. An assistant advertised as remembering "projects, preferences and personal context" was in practice a two-page notepad that quietly forgot your sister's name after a few weeks.

Storage and prompt budget are now separate problems:

* **Nothing is deleted.** The cap is a runaway guard normal use never approaches, and if it is ever hit it says so in the activity log instead of on stdout.
* **The prompt carries a core, not a dump.** Identity in full, then the most recently updated facts, budgeted — measured at **971 characters on a memory holding 62 stored facts.** That is *smaller* than the old whole-store cap, so sessions now connect with fewer tokens than before.
* **The rest is fetched on demand.** A `recall_memory` tool searches the full store locally — no network, no second model, well under a millisecond.

The part that is easy to get wrong: **a model cannot look something up if it doesn't know the thing exists.** So the prompt also carries an **index of the keys** it had no room for. Without it, "who is Ayşe?" gets "I don't know" while `ayse_sister` sits on disk unread. That index interleaves categories rather than sorting by recency — sorted like the core, a memory with forty preferences pushed the one entry the index existed for off the end.

⚙ → **🧠 MEMORY** shows every stored fact, when it was learned, and a ✕ to forget it. Everything stays in `memory/long_term.json` on your machine.

### ↩️ Undo — it can take back what it did

JARVIS moves files, renames them, writes to them and changes your settings. None of that had a way back; if it misheard you, the only remedy was to fix it by hand.

Say **"undo"** — in any language — and it reverses its own last action:

| | |
|---|---|
| **Files** | move · rename · create · copy · write · delete · organize desktop |
| **Settings** | volume · brightness · dark mode |

Three things it deliberately does *not* do:

* **It does not guess.** Settings undo reads the current value *before* changing it. Where a platform won't report that value, nothing is registered — an undo that restores a guess is worse than no undo.
* **It does not hoard.** Undoing a write means keeping the old contents in memory, so files over 1 MB are excluded and it says so rather than holding a 200 MB log for the session.
* **It does not delete your files to undo a copy.** The reverse of a copy is removing the copy; the reverse of "create a folder" is removing it *only while it's still empty*.

`organize_desktop` gets special treatment — one command that moves dozens of files, which made it the least reversible thing the assistant could do. It journals every move and puts all of them back in one go, cleaning up the folders it created if they're still empty.

**Undo costs nothing at runtime.** It appends a closure to a list; nothing in it runs unless you ask.

### ⚠️ A confirmation the model can't forge

The old gate read like this:

```python
if action in _DANGEROUS_ACTIONS:            # {"restart", "shutdown"}
    confirmed = str(params.get("confirmed", "")).lower()
```

`confirmed` is a **tool parameter, which means the model fills it in.** Nothing stopped it sending `confirmed=yes` on the first call and nothing checked that a human was ever involved. It was a convention, not a gate. And its coverage was two actions — so `toggle_wifi`, which cuts the assistant's own connection to the Live API and therefore *cannot be asked to undo itself*, went through with no gate at all.

The token is now issued by the interface. Shutdown, restart and WiFi put a banner on the HUD and **return immediately**; the action runs only if you press CONFIRM. Nothing blocks — JARVIS keeps talking while the banner is up — so this is **cheaper than the old gate**, which burned two tool round trips on every power command.

> The split between the two mechanisms is about reversibility, not about how alarming a word sounds. Anything undoable is done at once; only the genuinely irreversible asks. An assistant that checks with you before turning the volume down is one you stop talking to.

### 🎧 It finally asks which microphone

Both audio streams opened with no device argument at all, so they always took whatever the OS called "default" — and on Windows that *moves on its own* the moment you plug a headset in. "JARVIS can't hear me" almost always meant "JARVIS is listening to the webcam".

⚙ → **🎧 AUDIO DEVICES** lets you pick the microphone and the speakers by name. Two things matter more than the dropdown:

**The list is short.** `query_devices()` returns one entry per *device × host API*, not per device — measured on an ordinary Windows machine, **41 entries for what the sound settings show as 4 microphones and 4 speakers.** The same microphone appears four times, under MME, DirectSound, WASAPI and WDM-KS, with nothing to say which is which. That is not a choice, it's a quiz. The picker takes one host API per direction, drops the "Sound Mapper" and "Primary Sound Driver" pseudo-devices that just mean "default", and deduplicates. **41 → 8.**

**Every entry has been measured, not assumed.** The obvious approach is to pick the host API with the nicest names — WASAPI on Windows, which in shared mode **doesn't resample**, so with 16 kHz in and 24 kHz out against 48 kHz hardware every open failed. Adding a rate check and moving to DirectSound passes that test on both sides, and PortAudio's DirectSound **output is a silent sink**: the stream opens, every write returns success in ~0 ms, and not one sample reaches the speakers.

| | write(2.0 s) took | |
|---|---|---|
| MME | **2.02 s** | consumed in real time |
| DirectSound | **0.00 s** | swallowed instantly |

No capability flag reports that. So the app measures it — once per host API per direction, on a background thread at startup, using silence. Two consequences worth stating plainly:

* **Each direction picks its own host API.** On Windows this lands on DirectSound for the microphone and MME for the speakers — a split no amount of reasoning would have produced.
* **The probe runs in the mode the app actually ships.** DirectSound input passes a callback stream and fails a blocking read; probing the wrong mode rejected a microphone that works perfectly.

Your choice is stored **by name, not by index** — indices shift whenever something is plugged in. If the saved device is gone, it falls back to the system default and says so in the log rather than failing to start.

### 🔗 It stops forgetting the conversation when the connection drops

`session_resumption` was switched on in the config and the handle the server sent back was **never read** — so every reconnect started an empty session. A dropped packet, or simply changing the voice, wiped the conversation. "Unlimited sessions" leaked through exactly this hole.

The handle is captured and replayed now. A network blip, or switching your microphone, keeps the conversation intact.

It is held in memory only, deliberately: writing it to disk would make a fresh launch continue yesterday's chat, which sounds appealing but breaks the session-summary flow — a conversation that never ends never produces a summary, and the "yesterday we talked about…" line in the morning briefing silently disappears. Changing the **voice** also starts clean on purpose, since resuming restores the server's session state and would likely bring the old voice back with it.

### 🩹 Fixes that came with it

* **The assistant could die on a log line.** Status lines carry emoji and arrows (`📤 file_controller → Moved: a.txt → Documents/`). On a non-UTF-8 console — cp1254 on a Turkish Windows, cp1251 on a Russian one, cp932 on a Japanese one — printing one raises `UnicodeEncodeError`, and because that print sits *after* the tool's own `try/except`, it escaped into the receive loop and took the session down.
* **Every computer command paid for two model round trips.** `computer_settings` made an *entire second Gemini call, inside the tool*, purely to translate the request into one of its own action names — because the declaration only said "The action to perform", so the model rarely filled it in. When that second call failed, the fallback was `description.lower().replace(" ", "_")`, which turns the Turkish for "turn it down" into `sesi_kis` and straight into "Unknown action". The declaration now names all 56 actions and the rest is spelling tolerance handled locally by `difflib` in microseconds. When nothing matches it suggests real action names instead of dead-ending.
* An unresolvable saved audio device, or one the driver refuses to open, falls back to the system default and says so — on both the microphone and the speakers.
* A rejected session-resumption handle is dropped after one attempt, so an expired handle can never be replayed on every retry and prevent the reconnect it exists to protect.



---

## 🗺️ Mark Roadmap

| Mark | Focus |
|---|---|
| **XLIX** | Auto-start · clipboard intelligence · assistant customization |
| **L** | Session memory · background monitoring · proactive 2.0 · instant vision |
| **LI** | Plugin system · affective dialog · proactive audio · unlimited sessions |
| **LII** | Voice picker · live theming · reactive HUD · recallable memory · undo · real confirmation · audio device picker · session continuity |
| **LIII** | Wake word · Gemini 3.1 Flash Live · instant acknowledgment · self-describing action/plugin architecture |
| **LIV** | Holographic avatar · viseme lip-sync · facial acting · face-as-status · push-to-talk · self-echo guard · runtime self-knowledge & limits |
| **LV** | Video on the HUD · model ladder with measured fallback · split settings drawers · trimmed bundled skill list |
| *shared* | The last five above also shipped to LIII, LIV and LV at the same time — moving up a Mark never loses them |
| **LVI+** | Interrupt by voice · conversation history · Telegram remote · full file access · security camera · Obsidian |

---

## ⚡ Quick Start

```bash
git clone https://github.com/FatihMakes/Mark-LV.git
cd Mark-LV
python setup.py        # installs deps for YOUR OS + the browser automation engine
python main.py
```

`setup.py` only ever installs what your operating system needs — the Windows-only libraries are skipped automatically on macOS and Linux, and vice-versa. It also checks your Python version up front, so a wrong interpreter fails with a sentence instead of a wall of pip output. Prefer to do it by hand? `pip install -r requirements.txt` works too.

> ⚠️ **Installation Note:** If you hit a `ModuleNotFoundError` for an OS-specific package, install it with `pip install <module_name>`. The optional **wake word** engine is *not* installed here — grab it in one click from **⚙ → WAKE WORD** inside the app.

### Running the tests

The tests cover the parts with no window, microphone or model behind them — config and memory storage, the credential guard, dashboard authentication, the GitHub plugins, Office Studio and the observatory feeds — so they need neither PyQt6 nor an API key:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

### MCP servers and plugins

Open **⚙ → MCP SERVERS** (or **MANAGE MCP + PLUGINS** in the system panel) to add trusted MCP servers. The manager supports local `stdio` commands and remote Streamable HTTP endpoints, and includes starter presets for GitHub, filesystem, and Playwright. Add the credentials or allowed filesystem paths required by a server, then choose **APPLY & RECONNECT**; discovered tools are added to the next Gemini Live session. Failed connections are shown in the manager and the activity log.

Local stdio servers execute the configured command with your user permissions. MCP credentials are stored in `config/mcp_servers.json` in plain text, excluded from Git, and must be treated like passwords. Only connect to servers you trust. Existing Python plugins remain in `plugins/`; they are discovered at startup and can be enabled or disabled from **⚙ → PLUGINS**.

The bundled `github` and `github_insights` plugins add account/repository search, repository details, code/file lookup, issue and pull-request views, releases, workflow runs, commits, repository summaries, language/contributor/branch reports, file trees, and branch comparisons. Enable them under **⚙ → PLUGINS**, then open **⚙ → PLUGIN SETTINGS**, enter a GitHub personal access token, and select **TEST TOKEN**. The test authenticates with GitHub's `/user` endpoint; the token is never included in the response or application logs. Tokens are stored in `config/api_keys.json` in plain text, so use a least-privilege token and protect that file. Creating an issue is the only write operation; other bundled GitHub actions are read-only.

---

## 📋 Requirements

| Requirement | Details |
| --- | --- |
| **OS** | Windows 10/11, macOS, or Linux |
| **Python** | 3.11, 3.12 or 3.13 |
| **Microphone** | Required for voice interaction (and for the "Hey Jarvis" wake word) |
| **Speakers** | Required for voice replies |
| **API Key** | Free Gemini API key (entered on first launch → `config/api_keys.json`) |
| **GPU** | **Not required.** The avatar is rendered in software, and so is HUD video |
| **YouTube on the HUD** | `yt-dlp`, installed by `setup.py`. Without it, local files and direct URLs still play and YouTube links open in the browser with an explanation |
| **Wake word** *(optional)* | One-click download from ⚙ → WAKE WORD (`openwakeword`, a few MB, fully local) |

---

## 🗂️ Project Structure

```
Mark LV/
├── main.py                   # Core loop — Gemini Live session, audio I/O, viseme extraction, tool dispatch
├── ui.py                     # PyQt6 HUD — avatar canvas, waveform, log panel, settings drawer, camera feed
├── setup.py                  # OS-aware installer (skips wrong-OS dependencies, checks your Python)
├── .gitignore                # Keeps your API key, TLS key and memories out of the repository
├── requirements-dev.txt      # What the test suite needs — no GUI, audio or API key
├── tests/                    # python -m pytest
├── plugins/
│   └── _template.py          # Copy this to write a new skill — one file, drop in, done
├── actions/                  # Bundled skills — each self-describes via a TOOL dict + handler
│                             #   Everything here drives the COMPUTER, which is what decides
│                             #   whether a new skill belongs in this folder at all.
│   ├── web_search.py         # Gemini + DDG parallel search (news, research, price, compare)
│   ├── screen_processor.py   # Screen & webcam capture for vision
│   ├── background_monitor.py # User-configured topic watching — daily DDG check
│   ├── proactive.py          # Proactive 2.0 — time/context/rotation-aware check-ins
│   ├── reminder.py           # OS-native scheduled notifications
│   ├── system_monitor.py     # CPU / RAM / GPU / temperature telemetry
│   ├── computer_settings.py  # Volume, brightness, WiFi, power (per-OS)
│   ├── computer_control.py   # Keyboard shortcuts, mouse, window management
│   ├── open_app.py           # Application launcher (per-OS name map)
│   ├── browser_control.py    # Web browser control
│   ├── file_controller.py    # File system operations
│   ├── file_processor.py     # Document reading and summarization
│   ├── send_message.py       # Messaging integration
│   ├── weather_report.py     # Live weather data
│   ├── video_player.py       # Plays video on the HUD, where the avatar normally is
│   └── desktop.py            # Desktop and taskbar control
├── memory/
│   ├── memory_manager.py     # Load/save long_term.json — sessions, monitors, identity
│   ├── config_manager.py     # api_keys.json access — key, OS, name, voice, colour, toggles
│   └── long_term.json        # Persistent store — created on first run
├── core/
│   ├── observatory_data.py   # Public ISS, NOAA space-weather and market chart feeds
│   ├── gemini.py             # One place for every one-shot Gemini call — model ladder, timeouts, cooldowns
│   ├── prompt.txt            # All prompt wording — {tokens} are filled from the live system at startup
│   ├── avatar.py             # Avatar renderer — lighting, pose, expression, mouth (QPainter)
│   ├── avatar_mesh.py        # Head geometry — loads the face, generates skull/neck/rigs
│   ├── face_model.obj        # The face itself (MediaPipe canonical model, Apache-2.0, 25 KB)
│   ├── viseme.py             # Transcript → mouth shapes, fused with the audio's timing
│   ├── echo.py               # Tells your voice from the assistant's own echo; self-calibrating
│   ├── hotkey.py             # Push-to-talk chord — global on Windows, windowed fallback elsewhere
│   ├── undo.py               # One shared undo stack — actions register how to reverse themselves
│   ├── safe_io.py            # Atomic JSON saves; a damaged file is set aside, never overwritten
│   ├── secret_guard.py       # Recognises tokens and keys so they are not stored as memories
│   ├── confirm.py            # Irreversible-action gate — the token is issued by the UI, not the model
│   ├── audio_devices.py      # Microphone / speaker list — filtered, measured, resolved by name
│   ├── plugin_loader.py      # Plugin engine — discovery, validation, crash isolation
│   ├── mcp_manager.py        # stdio / Streamable HTTP MCP connections and tool dispatch
│   ├── action_loader.py      # Bundled-action engine — the built-in twin of plugin_loader
│   └── wake_word.py          # Local "Hey Jarvis" detector — own thread, offline, opt-in
└── config/
    ├── api_keys.json         # API key, name, voice, colour, toggles — created on first launch (git-ignored)
    ├── mcp_servers.json      # MCP server settings and credentials (git-ignored)
    └── certs/                # Self-signed TLS pair for the phone dashboard — generated locally (git-ignored)
```

---

## 🙏 Third-Party Assets

| Asset | Source | Licence |
| --- | --- | --- |
| `core/face_model.obj` | [MediaPipe](https://github.com/google-ai-edge/mediapipe) canonical face model — 468 vertices of measured human face geometry | Apache License 2.0 |

---

## 🔒 Your Data

JARVIS has no MARK server, telemetry service, or account. The assistant's local configuration remains on your machine, but features that you choose to use can contact their named providers:

| What | Where | Notes |
|---|---|---|
| Gemini API key, plugin credentials | `config/api_keys.json` | **Plaintext.** Anyone with your user account can read it. Treat it like a password file. |
| MCP server commands, URLs, credentials | `config/mcp_servers.json` | **Plaintext.** Excluded from Git; only configure servers you trust. |
| Dashboard TLS certificate + private key | `config/certs/` | Generated locally, self-signed, never leaves the machine. |
| What the assistant remembers about you | `memory/long_term.json` | **Plaintext.** Delete the file to make it forget everything. Tokens and API keys are refused here — they belong in plugin settings. |
| Observatory ISS / space-weather / market refresh | Public WhereTheISS.at, NOAA SWPC, and Yahoo Finance endpoints | Starts only when you open or refresh God's Eye; no account keys are sent. Yahoo receives the selected ticker. |
| NASA live video or external reference links | NASA and YouTube; TradingView when opened | Video resolution is user-triggered; in-app playback starts muted. |

These runtime files are listed in `.gitignore`, so a fork or a pull request cannot leak them by accident. **If you have already committed `config/api_keys.json` anywhere public, revoke that key** at [aistudio.google.com](https://aistudio.google.com/app/apikey) and generate a new one — removing the file in a later commit does not remove it from the history.

Your voice is streamed to Google's Gemini Live API while a session is open; that is the one thing that leaves your computer, and it stops when you mute or close the app.

---

## ⚠️ License

Personal and non-commercial use only.
Licensed under **[Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**.

---

## 👤 Connect with the Creator

Engineered by a developer building a real-world JARVIS-style assistant.
⭐ **Star the repository to support the journey to Mark 100.**

| Platform | Link |
| --- | --- |
| YouTube | [@FatihMakes](https://www.youtube.com/@FatihMakes) |
| Instagram | [@fatihmakes](https://www.instagram.com/fatihmakes) |