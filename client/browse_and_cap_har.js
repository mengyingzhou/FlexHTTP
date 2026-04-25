#!/usr/bin/env node

var fs = require('fs');
var program = require('commander');
var chc = require('chrome-har-capturer');


program
    .option('-u, --url <url>')
    .option('-o, --output <output file>');

program.parse(process.argv);
const options = program.opts();

var c = chc.run([options.url], {timeout: 300000});


c.on('har', function (har) {
    fs.writeFileSync(options.output, JSON.stringify(har, null, '\t'));
});

