#!/usr/bin/env node
// Compose exact vector branding over the owner's pug-inspired Imagegen portrait.
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'../..');
const {Resvg}=require(path.join(root,'build/rebrand-kurtz/tools/node_modules/@resvg/resvg-js'));
const art=fs.readFileSync(path.join(root,'marketing/dmg/kurtz-pug-art.png')).toString('base64');
const word=fs.readFileSync(path.join(root,'marketing/brand/kurtz-wordmark-dark.svg'),'utf8').replace(/<svg[^>]+>|<\/svg>/g,'');
const svg=`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1536 1024" width="1536" height="1024">
<image width="1536" height="1024" xlink:href="data:image/png;base64,${art}"/>
<g transform="translate(96 106) scale(1.3)">${word}</g>
<text x="96" y="318" font-family="Sora" font-size="28" fill="#FAF8F1">Good videos go further.</text>
<!-- Real Finder icons sit at (128,254) and (316,254) points. Only the
     contrasting label backgrounds and drag arrow are part of the artwork. -->
<g fill="#FAF8F1">
  <rect x="114" y="621" width="284" height="72" rx="22"/>
  <rect x="490" y="621" width="284" height="72" rx="22"/>
</g>
<path d="M412 508 H472 M454 490 L472 508 L454 526" fill="none" stroke="#FFE600" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
<!-- The two yellow rays echo the supplied brand sheet's pug treatment. -->
<path d="M1305 180 L1325 136 M1357 204 L1405 186" fill="none" stroke="#FFE600" stroke-width="12" stroke-linecap="round"/>
<text x="96" y="856" font-family="Sora" font-size="26" fill="#FAF8F1">Drag kurtz into Applications.</text>
</svg>`;
fs.writeFileSync(path.join(root,'marketing/dmg/background.svg'),svg);
fs.writeFileSync(path.join(root,'marketing/dmg/background@2x.png'),new Resvg(svg,{font:{fontFiles:[path.join(root,'Shared/Resources/Fonts/Sora-Regular.ttf')],loadSystemFonts:false}}).render().asPng());
console.log('Composed 1536×1024 kurtz installer background.');
