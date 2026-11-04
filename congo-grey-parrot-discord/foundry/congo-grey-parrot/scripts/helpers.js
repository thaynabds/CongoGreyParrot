// Funções sem dependência do Foundry. O teste em tests/foundry_helpers.test.mjs roda com node --test.

export function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

// Só busca mídia do próprio Foundry. Um jogador não consegue fazer o navegador do mestre
// baixar um endereço de outro site, data:, blob: ou javascript: e mandar para o Discord.
export function safeSource(source, origin) {
    let url;
    try {
        url = new URL(source, origin);
    } catch (error) {
        return "";
    }
    if (url.origin !== new URL(origin).origin) {
        return "";
    }
    if (url.protocol !== "http:" && url.protocol !== "https:") {
        return "";
    }
    return url.href;
}

export function mediaSources(html, origin) {
    const found = [];
    const pattern = /<(?:img|video|audio|source|a)\b[^>]*\b(?:src|href)=["']([^"']+)["']/gi;
    let match = pattern.exec(html);
    while (match) {
        const source = safeSource(match[1], origin);
        if (source && !found.includes(source)) {
            found.push(source);
        }
        match = pattern.exec(html);
    }
    return found;
}

export function mediaHtml(path, mediaType, filename) {
    const src = escapeHtml(encodeURI(path));
    const name = escapeHtml(filename);
    const type = String(mediaType || "");
    if (type.startsWith("image/")) {
        return `<img src="${src}" alt="${name}">`;
    }
    if (type.startsWith("video/")) {
        return `<video src="${src}" controls></video>`;
    }
    if (type.startsWith("audio/")) {
        return `<audio src="${src}" controls></audio>`;
    }
    return `<p><a href="${src}">${name}</a></p>`;
}
