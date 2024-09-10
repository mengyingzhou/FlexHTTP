#!/usr/bin/env node

const fs = require("fs");
const lighthouse = require("lighthouse");

var program = require("commander");
program.option("-u, --url <url>").option("-o, --output <output file>");
program.parse(process.argv);
const commandOptions = program.opts();

(async () => {
  const options = { output: "json", port: 9222 };
  const runnerResult = await lighthouse(commandOptions.url, options, {
    extends: "lighthouse:default",
    settings: {
      preset: "desktop",
      disableStorageReset: true,
      onlyAudits: [
        "first-contentful-paint",
        "speed-index",
        "interactive",
        "metrics",
      ],
    },
  });

  // `.report` is the Json report as a string
  const reportJson = runnerResult.report;
  fs.writeFileSync(commandOptions.output, reportJson);
})();
