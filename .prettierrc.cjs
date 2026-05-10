/** @type {import("prettier").Options} */
module.exports = {
  endOfLine: "auto",
  experimentalOperatorPosition: "start",
  importOrder: ["^[./]"],
  importOrderSeparation: true,
  plugins: [
    // https://dev.to/javien/how-to-use-prettier-plugin-with-yarn-pnp-in-vscode-4pf8
    require.resolve("prettier-plugin-packagejson"),
    require.resolve("@trivago/prettier-plugin-sort-imports"),
  ],
};
