import assert from "node:assert/strict";
import test from "node:test";

import {
    escapeHtml,
    mediaHtml,
    mediaSources,
    safeSource,
} from "../foundry/congo-grey-parrot/scripts/helpers.js";

const ORIGIN = "http://localhost:30000";

test("escapeHtml fecha aspas, que antes abriam atributo no alt da imagem", () => {
    assert.equal(escapeHtml(`a"b'c<d>&`), "a&quot;b&#39;c&lt;d&gt;&amp;");
});

test("nome de arquivo vindo do Discord não injeta atributo", () => {
    const html = mediaHtml("congo-grey-parrot/x.png", "image/png", 'x" onerror="alert(1)');
    assert.ok(!html.includes('" onerror="'));
    assert.ok(html.includes("&quot; onerror=&quot;"));
});

test("só busca mídia do próprio Foundry", () => {
    assert.equal(safeSource("worlds/a/img.png", ORIGIN), `${ORIGIN}/worlds/a/img.png`);
    assert.equal(safeSource("https://outro.site/x.png", ORIGIN), "");
    assert.equal(safeSource("javascript:alert(1)", ORIGIN), "");
    assert.equal(safeSource("data:image/png;base64,AAAA", ORIGIN), "");
    assert.equal(safeSource("//outro.site/x.png", ORIGIN), "");
});

test("mediaSources ignora links de fora e repetidos", () => {
    const html = '<img src="a.png"><img src="a.png"><a href="https://outro.site/b">b</a>';
    assert.deepEqual(mediaSources(html, ORIGIN), [`${ORIGIN}/a.png`]);
});
