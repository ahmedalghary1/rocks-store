const fs = require('fs');
const vm = require('vm');

const iconNames = [
  'arrow-left', 'arrow-right', 'badge-check', 'badge-help', 'banknote',
  'bell-ring', 'box', 'boxes', 'building-2', 'cable', 'chevron-left',
  'chevron-right', 'circle-user-round', 'download', 'external-link', 'eye',
  'facebook', 'file-pen-line', 'gallery-horizontal', 'gallery-thumbnails',
  'gauge', 'globe-2', 'handshake', 'headphones', 'heart', 'house', 'images',
  'inbox', 'info', 'instagram', 'lamp', 'languages', 'layout-grid',
  'layout-template', 'leaf', 'lightbulb', 'linkedin', 'list-checks',
  'list-filter', 'log-out', 'mail', 'mail-open', 'map-pin', 'menu',
  'message-circle', 'messages-square', 'package', 'package-check',
  'package-open', 'package-search', 'package-x', 'pencil', 'phone', 'plug',
  'plug-zap', 'plus', 'ruler', 'save', 'scan-eye', 'search', 'send',
  'settings', 'shield', 'shield-check', 'shopping-bag', 'shopping-cart',
  'sliders-horizontal', 'ticket-percent', 'toggle-left', 'trash-2',
  'triangle-alert', 'truck', 'users', 'wrench', 'x', 'youtube', 'zap',
  'zoom-in',
];

const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(__dirname + '/lucide.min.js', 'utf8'), context);

const exportName = name => name.split('-').map(part => part[0].toUpperCase() + part.slice(1)).join('');
const icons = Object.fromEntries(iconNames.map(name => {
  const icon = context.lucide.icons[exportName(name)];
  if (!icon) throw new Error(`Missing Lucide icon: ${name}`);
  return [name, icon];
}));

const runtime = `(()=>{const icons=${JSON.stringify(icons)};const ns='http://www.w3.org/2000/svg';const set=(el,attrs)=>Object.entries(attrs||{}).forEach(([key,value])=>el.setAttribute(key,String(value)));const make=([tag,attrs,children=[]])=>{const el=document.createElementNS(ns,tag);set(el,attrs);children.forEach(child=>el.append(make(child)));return el};window.lucide={createIcons:({root=document,attrs={}}={})=>{const nodes=[...(root.matches?.('[data-lucide]')?[root]:[]),...root.querySelectorAll('[data-lucide]')];nodes.forEach(node=>{const name=node.getAttribute('data-lucide');const icon=icons[name];if(!icon)return;const svg=make(icon);set(svg,attrs);for(const attr of node.attributes)if(attr.name!=='data-lucide'&&attr.name!=='class')svg.setAttribute(attr.name,attr.value);svg.setAttribute('class',('lucide lucide-'+name+' '+(node.getAttribute('class')||'')).trim());node.replaceWith(svg)})}}})();`;

fs.writeFileSync(__dirname + '/lucide-storefront.min.js', runtime);
console.log(`Built ${iconNames.length} storefront icons (${Buffer.byteLength(runtime)} bytes).`);
