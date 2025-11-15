module.exports = [
"[turbopack-node]/transforms/postcss.ts { CONFIG => \"[project]/frontend/postcss.config.cjs [postcss] (ecmascript)\" } [postcss] (ecmascript, async loader)", ((__turbopack_context__) => {

__turbopack_context__.v((parentImport) => {
    return Promise.all([
  "chunks/9e883__pnpm_3a66f5db._.js",
  "chunks/[root-of-the-server]__8131b9bf._.js"
].map((chunk) => __turbopack_context__.l(chunk))).then(() => {
        return parentImport("[turbopack-node]/transforms/postcss.ts { CONFIG => \"[project]/frontend/postcss.config.cjs [postcss] (ecmascript)\" } [postcss] (ecmascript)");
    });
});
}),
];