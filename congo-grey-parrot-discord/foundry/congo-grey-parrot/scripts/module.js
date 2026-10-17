const MODULE_ID = "congo-grey-parrot";
const DEFAULT_RELAY = "http://127.0.0.1:7477";

globalThis.__congoFoundryModule = true;

function relayBase() {
    const raw = game.settings.get(MODULE_ID, "relayUrl") || DEFAULT_RELAY;
    let url;
    try {
        url = new URL(raw);
    } catch (error) {
        return "";
    }
    const local = url.hostname === "127.0.0.1" || url.hostname === "localhost";
    if (url.protocol !== "http:" || !local) {
        return "";
    }
    return url.origin;
}

function isRelayClient() {
    const active = game.users.activeGM;
    return Boolean(active && active.id === game.user.id);
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function mediaSources(html) {
    const found = [];
    const pattern = /<(?:img|video|audio|source|a)\b[^>]*\b(?:src|href)=["']([^"']+)["']/gi;
    let match = pattern.exec(html);
    while (match) {
        const source = match[1];
        if (source && !source.startsWith("javascript:") && !found.includes(source)) {
            found.push(source);
        }
        match = pattern.exec(html);
    }
    return found;
}

function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
    });
}

async function fileFromSource(source) {
    const response = await fetch(source);
    if (!response.ok) {
        return null;
    }
    const blob = await response.blob();
    if (!blob.size || blob.size > 8 * 1024 * 1024) {
        return null;
    }
    const name = decodeURIComponent(source.split("/").pop().split("?")[0] || "arquivo");
    return { name, type: blob.type || "application/octet-stream", data: await blobToBase64(blob) };
}

async function uploadToFoundry(blob, filename, mediaType) {
    const file = new File([blob], filename, { type: mediaType || "application/octet-stream" });
    try {
        await FilePicker.createDirectory("data", "congo-grey-parrot", {});
    } catch (error) {
        // A pasta já existe quando o segundo arquivo chega.
    }
    const uploaded = await FilePicker.upload("data", "congo-grey-parrot", file, {}, { notify: false });
    return typeof uploaded === "string" ? uploaded : uploaded.path;
}

function mediaHtml(path, mediaType, filename) {
    const src = encodeURI(path);
    const name = escapeHtml(filename);
    if (mediaType.startsWith("image/")) {
        return `<img src="${src}" alt="${name}">`;
    }
    if (mediaType.startsWith("video/")) {
        return `<video src="${src}" controls></video>`;
    }
    if (mediaType.startsWith("audio/")) {
        return `<audio src="${src}" controls></audio>`;
    }
    return `<p><a href="${src}">${name}</a></p>`;
}

function describe(message) {
    const rolls = message.rolls || (message.roll ? [message.roll] : []);
    const expression = rolls.map((roll) => roll.formula).filter(Boolean).join(" | ");
    const total = rolls
        .map((roll) => roll.total)
        .filter((value) => value !== undefined && value !== null)
        .join(" | ");
    const detail = `${message.flavor || ""} ${message.content || ""}`
        .replace(/<[^>]+>/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .slice(0, 400);
    const author = message.author?.id ? game.users.get(message.author.id) : null;
    const player = message.alias || message.speaker?.alias || author?.name || "Foundry";
    return { player, expression, total, detail };
}

function isPublic(message) {
    if (message.getFlag(MODULE_ID, "origin") === "discord") {
        return false;
    }
    if (message.blind) {
        return false;
    }
    return !(message.whisper && message.whisper.length);
}

Hooks.once("init", () => {
    game.settings.register(MODULE_ID, "relayUrl", {
        name: "Endereço do bot",
        hint: "Só http://127.0.0.1 ou http://localhost. O padrão é a porta 7477.",
        scope: "world",
        config: true,
        type: String,
        default: DEFAULT_RELAY,
        restricted: true,
    });
});

Hooks.once("ready", () => {
    let warned = false;

    Hooks.on("createChatMessage", (message) => {
        if (!isRelayClient() || !isPublic(message)) {
            return;
        }
        const base = relayBase();
        if (!base) {
            return;
        }
        const roll = describe(message);
        const sources = mediaSources(message.content || "");
        if (!roll.expression && !roll.total && !roll.detail && sources.length === 0) {
            return;
        }
        const send = (body) => fetch(`${base}/roll`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const deliveries = [Promise.all(sources.map(fileFromSource)).then(async (files) => {
            const ready = files.filter(Boolean);
            if (ready.length === 0) {
                if (roll.expression || roll.total || roll.detail) {
                    await send({ vtt: "foundry", ...roll });
                }
                return;
            }
            for (const file of ready) {
                await send({ vtt: "foundry", ...roll, file });
            }
        })];
        Promise.all(deliveries).catch(() => {
            if (!warned) {
                warned = true;
                ui.notifications.warn(
                    "Congo Grey Parrot não alcançou o bot. Use /navegador ligar no Discord, no mesmo computador."
                );
            }
        });
    });

    window.setInterval(async () => {
        if (!isRelayClient()) {
            return;
        }
        const base = relayBase();
        if (!base) {
            return;
        }
        let response;
        try {
            response = await fetch(`${base}/foundry/pending`);
        } catch (error) {
            if (!warned) {
                warned = true;
                ui.notifications.warn(
                    "Congo Grey Parrot não alcançou o bot em " +
                        base +
                        ". Se o Foundry estiver em HTTPS, o navegador bloqueia este endereço HTTP."
                );
            }
            return;
        }
        if (!response.ok) {
            return;
        }
        warned = false;
        const payload = await response.json();
        for (const item of payload.items || []) {
            const lines = [];
            if (item.expression || item.total) {
                lines.push(
                    `<p><strong>${escapeHtml(item.expression || "rolagem")}</strong> = ${escapeHtml(item.total || "?")}</p>`
                );
            }
            if (item.text) {
                lines.push(`<p>${escapeHtml(item.text)}</p>`);
            }
            if (item.file_id) {
                const fileResponse = await fetch(`${base}/foundry/file/${item.file_id}`);
                if (fileResponse.ok) {
                    const blob = await fileResponse.blob();
                    const path = await uploadToFoundry(blob, item.filename || "arquivo", item.media_type);
                    lines.push(mediaHtml(path, item.media_type || "", item.filename || "arquivo"));
                }
            }
            await ChatMessage.create({
                speaker: { alias: item.player || "Discord" },
                content: lines.join("") || "<p>Discord</p>",
                flags: { [MODULE_ID]: { origin: "discord", id: String(item.id) } },
            });
            await fetch(`${base}/foundry/ack`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: item.id }),
            });
        }
    }, 2000);
});
