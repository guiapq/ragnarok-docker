#!/usr/bin/env node
const fs = require('fs');

const onlinePath = process.argv[2] || '/opt/roBrowserLegacy/Online.js';
console.log(`Patching ${onlinePath}...`);

const distWebPath = '/opt/roBrowserLegacy/dist/Web/Online.js';
const pristinePath = onlinePath + '.pristine';

if (fs.existsSync(distWebPath) && !fs.existsSync(pristinePath)) {
	fs.copyFileSync(distWebPath, pristinePath);
	console.log('✓ Created clean pristine backup from dist/Web/Online.js');
}

let content;
if (fs.existsSync(pristinePath)) {
	content = fs.readFileSync(pristinePath, 'utf8');
} else {
	content = fs.readFileSync(onlinePath, 'utf8');
}
let patches = 0;

// Patch 1: decodeItemStr in AddItem
const targetAddItem = `					ctx.AddItem = (
						ItemID,
						unidentifiedDisplayName,
						unidentifiedResourceName,
						identifiedDisplayName,
						identifiedResourceName,
						slotCount,
						ClassNum
					) => {
						ItemTable[ItemID] = {
							...(typeof ItemTable[ItemID] === 'object' && ItemTable[ItemID]),
							unidentifiedDisplayName: userStringDecoder.decode(unidentifiedDisplayName),
							unidentifiedResourceName: userStringDecoder.decode(unidentifiedResourceName),
							identifiedDisplayName: userStringDecoder.decode(identifiedDisplayName),
							identifiedResourceName: userStringDecoder.decode(identifiedResourceName),
							unidentifiedDescriptionName: [],
							identifiedDescriptionName: [],
							EffectID: null,
							costume: null,
							PackageID: null,
							slotCount: slotCount,
							ClassNum: ClassNum
						};

						return 1;
					};
					ctx.AddItemUnidentifiedDesc = (ItemID, v) => {
						ItemTable[ItemID].unidentifiedDescriptionName.push(userStringDecoder.decode(v));
						return 1;
					};
					ctx.AddItemIdentifiedDesc = (ItemID, v) => {
						ItemTable[ItemID].identifiedDescriptionName.push(userStringDecoder.decode(v));
						return 1;
					};`;


const replacementAddItem = `					const decodeItemStr = (v) => {
						if (typeof v === 'string') return v;
						if (v instanceof Uint8Array || v instanceof ArrayBuffer) {
							return userStringDecoder.decode(v instanceof ArrayBuffer ? new Uint8Array(v) : v);
						}
						return String(v ?? '');
					};
					const stripColorCode = (s) => (typeof s === 'string' ? s.replace(/\\^[0-9a-fA-F]{6}/g, '') : s);
					ctx.AddItem = (
						ItemID,
						unidentifiedDisplayName,
						unidentifiedResourceName,
						identifiedDisplayName,
						identifiedResourceName,
						slotCount,
						ClassNum
					) => {
						ItemTable[ItemID] = {
							...(typeof ItemTable[ItemID] === 'object' && ItemTable[ItemID]),
							unidentifiedDisplayName: stripColorCode(decodeItemStr(unidentifiedDisplayName)),
							unidentifiedResourceName: decodeItemStr(unidentifiedResourceName),
							identifiedDisplayName: stripColorCode(decodeItemStr(identifiedDisplayName)),
							identifiedResourceName: decodeItemStr(identifiedResourceName),
							unidentifiedDescriptionName: [],
							identifiedDescriptionName: [],
							EffectID: null,
							costume: null,
							PackageID: null,
							slotCount: slotCount,
							ClassNum: ClassNum
						};

						return 1;
					};
					ctx.AddItemUnidentifiedDesc = (ItemID, v) => {
						ItemTable[ItemID].unidentifiedDescriptionName.push(decodeItemStr(v));
						return 1;
					};
					ctx.AddItemIdentifiedDesc = (ItemID, v) => {
						ItemTable[ItemID].identifiedDescriptionName.push(decodeItemStr(v));
						return 1;
					};`;

// Fix broken decodeItemStr calls from old bad patches
if (content.includes('unidentifiedDisplayName: decodeItemStr(),')) {
	content = content.replace(/unidentifiedDisplayName: decodeItemStr\(\),/g, 'unidentifiedDisplayName: decodeItemStr(unidentifiedDisplayName),');
	content = content.replace(/identifiedDisplayName: decodeItemStr\(\),/g, 'identifiedDisplayName: decodeItemStr(identifiedDisplayName),');
	content = content.replace(/unidentifiedDescriptionName\.push\(decodeItemStr\(\)\);/g, 'unidentifiedDescriptionName.push(decodeItemStr(v));');
	content = content.replace(/identifiedDescriptionName\.push\(decodeItemStr\(\)\);/g, 'identifiedDescriptionName.push(decodeItemStr(v));');
	patches++;
	console.log('✓ Fixed empty decodeItemStr() calls');
}
if (content.includes('userCharpage')) {
	content = content.replace(/decodeItemStr\(([^,)]+),\s*userCharpage\)/g, 'decodeItemStr($1)');
	patches++;
	console.log('✓ Cleaned up userCharpage references');
}

// Upgrade: if already patched with decodeItemStr but missing stripColorCode, inject it
if (content.includes('const decodeItemStr') && !content.includes('stripColorCode')) {
	// Inject stripColorCode definition right after decodeItemStr closing brace
	content = content.replace(
		/(const decodeItemStr[\s\S]*?\};)/,
		"$1\n\t\t\t\t\tconst stripColorCode = (s) => (typeof s === 'string' ? s.replace(/\\^[0-9a-fA-F]{6}/g, '') : s);"
	);
	// Replace plain decodeItemStr calls on display name fields with stripColorCode-wrapped versions
	content = content.replace(
		/unidentifiedDisplayName: decodeItemStr\(unidentifiedDisplayName\)/g,
		'unidentifiedDisplayName: stripColorCode(decodeItemStr(unidentifiedDisplayName))'
	);
	content = content.replace(
		/identifiedDisplayName: decodeItemStr\(identifiedDisplayName\)/g,
		'identifiedDisplayName: stripColorCode(decodeItemStr(identifiedDisplayName))'
	);
	patches++;
	console.log('✓ Patch 1 upgrade (stripColorCode injected into existing decodeItemStr patch)');
}

for (const [oldStr, newStr] of [
	[targetAddItem.replace(/\n/g, '\r\n'), replacementAddItem.replace(/\n/g, '\r\n')],
	[targetAddItem, replacementAddItem]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 1 (decodeItemStr) applied');
		break;
	}
}

// Patch 2: Strip ^RRGGBB in getItemName
const targetGetName = '\t\tstr += it.identifiedDisplayName;\n';
const replaceGetName = "\t\tstr += it.identifiedDisplayName.replace(/\\^[0-9a-fA-F]{6}/g, '');\n";
for (const [oldStr, newStr] of [
	[targetGetName.replace(/\n/g, '\r\n'), replaceGetName.replace(/\n/g, '\r\n')],
	[targetGetName, replaceGetName]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 2 (strip ^RRGGBB in getItemName) applied');
		break;
	}
}

// Patch 3: Equipment window itemName strip ^RRGGBB directly in EquipmentCommon
const oldEq = `add3Dots(
						jQuery.escape(
							DB.getItemName(item, { showItemGrade: false, showItemSlots: false, showItemOptions: false })
						)`;
const newEq = `add3Dots(
						jQuery.escape(
							DB.getItemName(item, { showItemGrade: false, showItemSlots: false, showItemOptions: false }).replace(/\\^[0-9a-fA-F]{6}/g, '')
						)`;
for (const [oldStr, newStr] of [
	[oldEq.replace(/\n/g, '\r\n'), newEq.replace(/\n/g, '\r\n')],
	[oldEq, newEq]
]) {
	if (content.includes(oldStr)) {
		const count = content.split(oldStr).length - 1;
		content = content.split(oldStr).join(newStr);
		patches += count;
		console.log(`✓ Patch 3 (Equipment window itemName strip) applied to ${count} places`);
		break;
	}
}

// Patch 4: loadLuaTable error handling
const oldLlt = `		Client.loadFile(id_filename, async function (file) {
			try {
				// check if file is ArrayBuffer and convert to Uint8Array if necessary
				let buffer = file instanceof ArrayBuffer ? new Uint8Array(file) : file;
				// mount file
				lua.mountFile(id_filename, buffer);
				// execute file
				await lua.doFile(id_filename);
				loadValueTable();
			} catch (hException) {
				console.error(\`(\${id_filename}) error: \`, hException);
			}
		});`;

const newLlt = `		let ended = false;
		function finish(tbl) {
			if (ended) return;
			ended = true;
			if (callback) callback.call(null, tbl || {});
			if (onEnd) onEnd.call();
		}
		Client.loadFile(id_filename, async function (file) {
			try {
				let buffer = file instanceof ArrayBuffer ? new Uint8Array(file) : file;
				lua.mountFile(id_filename, buffer);
				await lua.doFile(id_filename);
				loadValueTable();
			} catch (hException) {
				console.error(\`(\${id_filename}) error: \`, hException);
				finish({});
			}
		}, function(err) {
			console.warn(\`(\${id_filename}) not found: \`, err);
			finish({});
		});`;

for (const [oldStr, newStr] of [
	[oldLlt.replace(/\n/g, '\r\n'), newLlt.replace(/\n/g, '\r\n')],
	[oldLlt, newLlt]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 4 (loadLuaTable error handling) applied');
		break;
	}
}

// Patch 5: loadLuaValue error handling
const oldLlv = `				} finally {
					if (onEnd) {
						onEnd.call();
					}
				}
			});
		} catch (e) {
			console.error('error: ', e);
			if (onEnd) {
				onEnd.call();
			}
		}`;

const newLlv = `				} finally {
					if (onEnd) {
						onEnd.call();
					}
				}
			}, function(err) {
				console.warn(\`(\${file_path}) not found: \`, err);
				if (callback) callback.call(null, null);
				if (onEnd) onEnd.call();
			});
		} catch (e) {
			console.error('error: ', e);
			if (onEnd) {
				onEnd.call();
			}
		}`;

for (const [oldStr, newStr] of [
	[oldLlv.replace(/\n/g, '\r\n'), newLlv.replace(/\n/g, '\r\n')],
	[oldLlv, newLlv]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 5 (loadLuaValue error handling) applied');
		break;
	}
}

// Patch 6: loadHatEffectInfo onError handling
const targetHat = `			// All files loaded
			onEnd && onEnd();
		});
	}`;

const replaceHat = `			// All files loaded
			onEnd && onEnd();
		}, function(err) {
			console.warn('[HatEffect] Not found:', err);
			onEnd && onEnd();
		});
	}`;

for (const [oldStr, newStr] of [
	[targetHat.replace(/\n/g, '\r\n'), replaceHat.replace(/\n/g, '\r\n')],
	[targetHat, replaceHat]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 6 (loadHatEffectInfo onError handling) applied');
		break;
	}
}

// Patch 7: DB.init Fail-Safe Watchdog (never hang at 84% on missing files)
const targetDbInit = `	DB.init = function init() {
		// Callback
		var index = 0,
			count = 0;
		function onLoad() {
			count++;
			return function OnLoadClosure() {
				index++;

				if (DB.onProgress) {
					DB.onProgress(index, count);
				}

				if (index === count && DB.onReady) {
					DB.onReady();
				}
			};
		}`;

const replaceDbInit = `	DB.init = function init() {
		// Callback
		var index = 0,
			count = 0;
		var watchdogTimer = null;
		function resetWatchdog() {
			if (watchdogTimer) clearTimeout(watchdogTimer);
			watchdogTimer = setTimeout(function () {
				if (index < count && DB.onReady) {
					console.warn('[DB.init Watchdog] Timeout waiting for DB tables (' + index + '/' + count + '). Auto-advancing.');
					index = count;
					if (DB.onProgress) DB.onProgress(count, count);
					DB.onReady();
				}
			}, 3000);
		}
		function onLoad() {
			count++;
			resetWatchdog();
			return function OnLoadClosure() {
				index++;
				resetWatchdog();

				if (DB.onProgress) {
					DB.onProgress(index, count);
				}

				if (index === count && DB.onReady) {
					if (watchdogTimer) clearTimeout(watchdogTimer);
					DB.onReady();
				}
			};
		}`;

for (const [oldStr, newStr] of [
	[targetDbInit.replace(/\n/g, '\r\n'), replaceDbInit.replace(/\n/g, '\r\n')],
	[targetDbInit, replaceDbInit]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 7 (DB.init Fail-Safe Watchdog) applied');
		break;
	}
}

// Patch 8: ItemInfo & ItemCompare Collection image fallback to Divine Pride
if (!content.includes("static.divine-pride.net/images/items/collection/' + item.ITID")) {
	const targetCollection = `				'collection/' +
				(item.IsIdentified ? it.identifiedResourceName : it.unidentifiedResourceName) +
				'.bmp',
			function (data) {
				ui.find('.collection').css('backgroundImage', 'url(' + data + ')');
			}
		);`;

	const replaceCollection = `				'collection/' +
				(item.IsIdentified ? it.identifiedResourceName : it.unidentifiedResourceName) +
				'.bmp',
			function (data) {
				ui.find('.collection').css('backgroundImage', 'url(' + data + ')');
			},
			function () {
				ui.find('.collection').css('backgroundImage', 'url(https://static.divine-pride.net/images/items/collection/' + item.ITID + '.png)');
			}
		);`;

	for (const [oldStr, newStr] of [
		[targetCollection.replace(/\n/g, '\r\n'), replaceCollection.replace(/\n/g, '\r\n')],
		[targetCollection, replaceCollection]
	]) {
		if (content.includes(oldStr)) {
			const count = content.split(oldStr).length - 1;
			content = content.split(oldStr).join(newStr);
			patches += count;
			console.log(`✓ Patch 8 (ItemInfo/Compare Collection Divine Pride fallback) applied to ${count} places`);
			break;
		}
	}
}

// Patch 9: Equipment & PlayerViewEquip item button fallback to Divine Pride
const targetEquipBtn = `		Client.loadFile(
			DB.INTERFACE_PATH + 'item/' + it.identifiedResourceName + '.bmp',
			function (data) {
				this.ui
					.find('.item[data-index="' + item.index + '"] button')
					.css('backgroundImage', 'url(' + data + ')');
			}.bind(this)
		);`;

const replaceEquipBtn = `		Client.loadFile(
			DB.INTERFACE_PATH + 'item/' + it.identifiedResourceName + '.bmp',
			function (data) {
				this.ui
					.find('.item[data-index="' + item.index + '"] button')
					.css('backgroundImage', 'url(' + data + ')');
			}.bind(this),
			function () {
				this.ui
					.find('.item[data-index="' + item.index + '"] button')
					.css('backgroundImage', 'url(https://static.divine-pride.net/images/items/item/' + item.ITID + '.png)');
			}.bind(this)
		);`;

for (const [oldStr, newStr] of [
	[targetEquipBtn.replace(/\n/g, '\r\n'), replaceEquipBtn.replace(/\n/g, '\r\n')],
	[targetEquipBtn, replaceEquipBtn]
]) {
	if (content.includes(oldStr)) {
		const count = content.split(oldStr).length - 1;
		content = content.split(oldStr).join(newStr);
		patches += count;
		console.log(`✓ Patch 9 (Equipment Divine Pride fallback) applied to ${count} places`);
		break;
	}
}

// Patch 10: Equipment Switch item button fallback to Divine Pride
const targetSwitchBtn = `		Client.loadFile(
			DB.INTERFACE_PATH + 'item/' + it.identifiedResourceName + '.bmp',
			function (data) {
				var button = this.ui.find('.item[data-index="' + item.index + '"] button');
				button.css('backgroundImage', 'url(' + data + ')');
				if (!inSwitchList) {
					button.css('filter', 'grayscale(100%)');
				}
			}.bind(this)
		);`;

const replaceSwitchBtn = `		Client.loadFile(
			DB.INTERFACE_PATH + 'item/' + it.identifiedResourceName + '.bmp',
			function (data) {
				var button = this.ui.find('.item[data-index="' + item.index + '"] button');
				button.css('backgroundImage', 'url(' + data + ')');
				if (!inSwitchList) {
					button.css('filter', 'grayscale(100%)');
				}
			}.bind(this),
			function () {
				var button = this.ui.find('.item[data-index="' + item.index + '"] button');
				button.css('backgroundImage', 'url(https://static.divine-pride.net/images/items/item/' + item.ITID + '.png)');
				if (!inSwitchList) {
					button.css('filter', 'grayscale(100%)');
				}
			}.bind(this)
		);`;

for (const [oldStr, newStr] of [
	[targetSwitchBtn.replace(/\n/g, '\r\n'), replaceSwitchBtn.replace(/\n/g, '\r\n')],
	[targetSwitchBtn, replaceSwitchBtn]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 10 (Equipment Switch Divine Pride fallback) applied');
		break;
	}
}

// Patch 11: Inventory item icon fallback to Divine Pride
const targetInvIcon = `			Client.loadFile(
				DB.INTERFACE_PATH +
					'item/' +
					(item.IsIdentified ? it.identifiedResourceName : it.unidentifiedResourceName) +
					'.bmp',
				function (data) {
					content
						.find('.item[data-index="' + item.index + '"] .icon')
						.css('backgroundImage', 'url(' + data + ')');
				}
			);`;

const replaceInvIcon = `			Client.loadFile(
				DB.INTERFACE_PATH +
					'item/' +
					(item.IsIdentified ? it.identifiedResourceName : it.unidentifiedResourceName) +
					'.bmp',
				function (data) {
					content
						.find('.item[data-index="' + item.index + '"] .icon')
						.css('backgroundImage', 'url(' + data + ')');
				},
				function () {
					content
						.find('.item[data-index="' + item.index + '"] .icon')
						.css('backgroundImage', 'url(https://static.divine-pride.net/images/items/item/' + item.ITID + '.png)');
				}
			);`;

for (const [oldStr, newStr] of [
	[targetInvIcon.replace(/\n/g, '\r\n'), replaceInvIcon.replace(/\n/g, '\r\n')],
	[targetInvIcon, replaceInvIcon]
]) {
	if (content.includes(oldStr)) {
		const count = content.split(oldStr).length - 1;
		content = content.split(oldStr).join(newStr);
		patches += count;
		console.log(`✓ Patch 11 (Inventory Divine Pride fallback) applied to ${count} places`);
		break;
	}
}

// Patch 12: ItemObtain item icon fallback to Divine Pride
const targetObtain = `		Client.loadFile(
			DB.INTERFACE_PATH + 'item/' + resource + '.bmp',
			function (url) {
				this.ui.find('img.' + item.ITID).attr('src', url);
			}.bind(this)
		);`;

const replaceObtain = `		Client.loadFile(
			DB.INTERFACE_PATH + 'item/' + resource + '.bmp',
			function (url) {
				this.ui.find('img.' + item.ITID).attr('src', url);
			}.bind(this),
			function () {
				this.ui.find('img.' + item.ITID).attr('src', 'https://static.divine-pride.net/images/items/item/' + item.ITID + '.png');
			}.bind(this)
		);`;

for (const [oldStr, newStr] of [
	[targetObtain.replace(/\n/g, '\r\n'), replaceObtain.replace(/\n/g, '\r\n')],
	[targetObtain, replaceObtain]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 12 (ItemObtain Divine Pride fallback) applied');
		break;
	}
}

// Patch 13: Cart & Storage item icon fallback to Divine Pride
const targetStorage = `			Client.loadFile(DB.INTERFACE_PATH + 'item/' + it.identifiedResourceName + '.bmp', function (data) {
				content.find('.item[data-index="' + i + '"] .icon').css('backgroundImage', 'url(' + data + ')');
			});`;

const replaceStorage = `			Client.loadFile(DB.INTERFACE_PATH + 'item/' + it.identifiedResourceName + '.bmp', function (data) {
				content.find('.item[data-index="' + i + '"] .icon').css('backgroundImage', 'url(' + data + ')');
			}, function () {
				content.find('.item[data-index="' + i + '"] .icon').css('backgroundImage', 'url(https://static.divine-pride.net/images/items/item/' + (it.ITID || item.ITID || i) + '.png)');
			});`;

for (const [oldStr, newStr] of [
	[targetStorage.replace(/\n/g, '\r\n'), replaceStorage.replace(/\n/g, '\r\n')],
	[targetStorage, replaceStorage]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 13 (Storage/Cart Divine Pride fallback) applied');
		break;
	}
}


// Patch 14: NpcStore item icon fallback to Divine Pride
const targetStoreItem = `		// Add the icon once loaded
		Client.loadFile(
			DB.INTERFACE_PATH +
				'item/' +
				(item.IsIdentified ? it.identifiedResourceName : it.unidentifiedResourceName) +
				'.bmp',
			function (data) {
				content
					.find('.item[data-index="' + item.index + '"] .icon')
					.css('backgroundImage', 'url(' + data + ')');
			}
		);`;

const replaceStoreItem = `		// Add the icon once loaded
		Client.loadFile(
			DB.INTERFACE_PATH +
				'item/' +
				(item.IsIdentified ? it.identifiedResourceName : it.unidentifiedResourceName) +
				'.bmp',
			function (data) {
				content
					.find('.item[data-index="' + item.index + '"] .icon')
					.css('backgroundImage', 'url(' + data + ')');
			},
			function () {
				content
					.find('.item[data-index="' + item.index + '"] .icon')
					.css('backgroundImage', 'url(https://static.divine-pride.net/images/items/item/' + item.ITID + '.png)');
			}
		);`;

for (const [oldStr, newStr] of [
	[targetStoreItem.replace(/\n/g, '\r\n'), replaceStoreItem.replace(/\n/g, '\r\n')],
	[targetStoreItem, replaceStoreItem]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 14 (NpcStore item icon Divine Pride fallback) applied');
		break;
	}
}

// Patch 15: NpcStore currency icon fallback to Divine Pride
const targetStoreCurrency = `		Client.loadFile(
			DB.INTERFACE_PATH +
				'item/' +
				(item.IsIdentified ? currencyit.identifiedResourceName : currencyit.unidentifiedResourceName) +
				'.bmp',
			function (data) {
				content
					.find('.item[data-index="' + item.index + '"] .currency_icon')
					.css('backgroundImage', 'url(' + data + ')');
			}
		);`;

const replaceStoreCurrency = `		Client.loadFile(
			DB.INTERFACE_PATH +
				'item/' +
				(item.IsIdentified ? currencyit.identifiedResourceName : currencyit.unidentifiedResourceName) +
				'.bmp',
			function (data) {
				content
					.find('.item[data-index="' + item.index + '"] .currency_icon')
					.css('backgroundImage', 'url(' + data + ')');
			},
			function () {
				if (item.currencyITID) {
					content
						.find('.item[data-index="' + item.index + '"] .currency_icon')
						.css('backgroundImage', 'url(https://static.divine-pride.net/images/items/item/' + item.currencyITID + '.png)');
				}
			}
		);`;

for (const [oldStr, newStr] of [
	[targetStoreCurrency.replace(/\n/g, '\r\n'), replaceStoreCurrency.replace(/\n/g, '\r\n')],
	[targetStoreCurrency, replaceStoreCurrency]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 15 (NpcStore currency icon Divine Pride fallback) applied');
		break;
	}
}

// Patch 16: NpcStore drag image safety check
const targetStoreDrag = `		img = new Image();
		url = this.firstChild.style.backgroundImage.match(/\\(([^\\)]+)/)[1].replace(/"/g, '');
		img.decoding = 'async';
		img.src = url;`;

const replaceStoreDrag = `		img = new Image();
		var _bgM = this.firstChild && this.firstChild.style.backgroundImage ? this.firstChild.style.backgroundImage.match(/\\(([^\\)]+)/) : null;
		url = _bgM ? _bgM[1].replace(/"/g, '') : '';
		img.decoding = 'async';
		if (url) img.src = url;`;

for (const [oldStr, newStr] of [
	[targetStoreDrag.replace(/\n/g, '\r\n'), replaceStoreDrag.replace(/\n/g, '\r\n')],
	[targetStoreDrag, replaceStoreDrag]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 16 (NpcStore drag image safety check) applied');
		break;
	}
}

// Clean up broken Patch 18 (renderElement 10-frame timer that broke ground items)
if (content.includes('entity.objecttype === 2 && (!spr || !act)')) {
	content = content.replace(/\t\t\tif \(entity\.objecttype === 2 && \(!spr \|\| !act\)\) \{[\s\S]*?\t\t\t\t\}\n\t\t\t\}\n/g, '');
	patches++;
	console.log('✓ Cleaned up broken Patch 18 (restored normal ground drop rendering)');
}

// Clean up broken Patch 17 (duplicate Client.loadFile calls in ItemObject.add)
if (content.includes("Client.loadFile(path + '.spr', null, function () {")) {
	content = content.replace(
		/\t\tClient\.loadFile\(path \+ '\.spr'[\s\S]*?entity\.files\.body\.act = defaultDropPath \+ '\.act';\n\t\t\}\);\n/g,
		''
	);
	patches++;
	console.log('✓ Cleaned up broken Patch 17 duplicate Client.loadFile calls');
}

// Patch 17: Safe DB.getItemPath fallback and ItemObject.add safety
if (content.includes("DB.getItemPath = function getItemPath(itemid, identify) {")) {
	content = content.replace(
		/DB\.getItemPath = function getItemPath\(itemid, identify\) \{[\s\S]*?\t\};/g,
		`DB.getItemPath = function getItemPath(itemid, identify) {
		var it = DB.getItemInfo(itemid);
		var res = it ? (identify ? it.identifiedResourceName : it.unidentifiedResourceName) : null;
		return (
			'data/sprite/\\xbe\\xc6\\xc0\\xcc\\xc5\\xdb/' +
			(res || '\\xb3\\xaa\\xc0\\xcc\\xc7\\xc1')
		);
	};`
	);
	patches++;
	console.log('✓ Patch 17a (Safe DB.getItemPath) applied');
}

// Patch 17b: Safe ItemObject.add
if (content.includes("var it = DB.getItemInfo(itemid);\n\t\tvar path = DB.getItemPath(itemid, identify);\n\t\tvar entity = new Entity();\n\t\tvar name = identify ? it.identifiedDisplayName : it.unidentifiedDisplayName;")) {
	content = content.replace(
		"var it = DB.getItemInfo(itemid);\n\t\tvar path = DB.getItemPath(itemid, identify);\n\t\tvar entity = new Entity();\n\t\tvar name = identify ? it.identifiedDisplayName : it.unidentifiedDisplayName;",
		"var it = DB.getItemInfo(itemid) || {};\n\t\tvar path = DB.getItemPath(itemid, identify);\n\t\tvar entity = new Entity();\n\t\tvar name = (identify ? it.identifiedDisplayName : it.unidentifiedDisplayName) || ('Item #' + itemid);"
	);
	patches++;
	console.log('✓ Patch 17b (Safe iteminfo fallback in ItemObject.add) applied');
}

// Patch 18a: Safe dragstart across Inventory (prevent null match error and setDragImage crash)
const targetInvDrag = `\t\t// Set image to the drag drop element
\t\tvar img = new Image();
\t\tvar url = this.querySelector('.icon')
\t\t\t.style.backgroundImage.match(/\\((.*?)\\)/)[1]
\t\t\t.replace(/('|")/g, '');
\t\timg.decoding = 'async';
\t\timg.src = url.replace(/^\\"/, '').replace(/\\"$/, '');

\t\tevent.originalEvent.dataTransfer.setDragImage(img, 12, 12);
\t\tevent.originalEvent.dataTransfer.setData(
\t\t\t'Text',
\t\t\tJSON.stringify(
\t\t\t\t(window._OBJ_DRAG_ = {
\t\t\t\t\ttype: 'item',
\t\t\t\t\tfrom: 'Inventory',
\t\t\t\t\tdata: item
\t\t\t\t})
\t\t\t)
\t\t);

\t\tonItemOut();`;

const replaceInvDrag = `\t\t// Set image to the drag drop element (safe against null match and CORS/unloaded setDragImage)
\t\tvar iconEl = this.querySelector('.icon') || this.firstChild;
\t\tvar bgM = iconEl && iconEl.style.backgroundImage ? iconEl.style.backgroundImage.match(/\\((.*?)\\)/) : null;
\t\tvar url = bgM && bgM[1] ? bgM[1].replace(/('|")/g, '').replace(/^\"/, '').replace(/\"$/, '') : '';
\t\tif (url) {
\t\t\ttry {
\t\t\t\tvar img = new Image();
\t\t\t\timg.decoding = 'async';
\t\t\t\timg.src = url;
\t\t\t\tevent.originalEvent.dataTransfer.setDragImage(img, 12, 12);
\t\t\t} catch (e) {}
\t\t}

\t\tevent.originalEvent.dataTransfer.setData(
\t\t\t'Text',
\t\t\tJSON.stringify(
\t\t\t\t(window._OBJ_DRAG_ = {
\t\t\t\t\ttype: 'item',
\t\t\t\t\tfrom: 'Inventory',
\t\t\t\t\tdata: item
\t\t\t\t})
\t\t\t)
\t\t);

\t\tonItemOut();`;

for (const [oldStr, newStr] of [
	[targetInvDrag.replace(/\n/g, '\r\n'), replaceInvDrag.replace(/\n/g, '\r\n')],
	[targetInvDrag, replaceInvDrag]
]) {
	if (content.includes(oldStr)) {
		const count = content.split(oldStr).length - 1;
		content = content.split(oldStr).join(newStr);
		patches += count;
		console.log(`✓ Patch 18a (Safe Inventory dragstart) applied to ${count} places`);
		break;
	}
}

// Safe dragend (500ms grace period so drop event always receives window._OBJ_DRAG_)
const targetInvDragEnd = `\tfunction onItemDragEnd() {\n\t\tdelete window._OBJ_DRAG_;\n\t}`;
const replaceInvDragEnd = `\tfunction onItemDragEnd() {\n\t\tsetTimeout(function () {\n\t\t\tdelete window._OBJ_DRAG_;\n\t\t}, 500);\n\t}`;

for (const [oldStr, newStr] of [
	[targetInvDragEnd.replace(/\n/g, '\r\n'), replaceInvDragEnd.replace(/\n/g, '\r\n')],
	[targetInvDragEnd, replaceInvDragEnd]
]) {
	if (content.includes(oldStr)) {
		const count = content.split(oldStr).length - 1;
		content = content.split(oldStr).join(newStr);
		patches += count;
		console.log(`✓ Patch 18a-end (Safe Inventory dragend delay) applied to ${count} places`);
		break;
	}
}

// Patch 18b: Safe InputBox.setType('item')
const targetInputItem = `			case 'item':
				this.ui.addClass('number');
				this.ui.find('.text').text(DB.getItemInfo(itemId).identifiedDisplayName);
				this.ui.find('input').attr('type', 'text');
				defaultVal = defaultVal || 0;
				break;`;

const replaceInputItem = `			case 'item':
				this.ui.addClass('number');
				var itm = DB.getItemInfo(itemId);
				this.ui.find('.text').text(itm && itm.identifiedDisplayName ? itm.identifiedDisplayName : ('Item #' + itemId));
				this.ui.find('input').attr('type', 'text');
				defaultVal = defaultVal || 0;
				break;`;

for (const [oldStr, newStr] of [
	[targetInputItem.replace(/\n/g, '\r\n'), replaceInputItem.replace(/\n/g, '\r\n')],
	[targetInputItem, replaceInputItem]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 18b (Safe InputBox item drop dialog) applied');
		break;
	}
}

// Patch 18c: Reliable MapControl drop handling (fallback to _OBJ_DRAG_, allow drop with Equipment open, attach to document)
const targetMapDrop = `\t/**
\t * Drop items to the map
\t */
\tfunction onDrop(event) {
\t\tvar item, data;

\t\ttry {
\t\t\tdata = JSON.parse(event.originalEvent.dataTransfer.getData('Text'));
\t\t} catch (e) {
\t\t\tconsole.error(e);
\t\t}

\t\t// Stop default behavior
\t\tevent.stopImmediatePropagation();
\t\tif (!data) {
\t\t\treturn false;
\t\t}

\t\t// Hacky way to trigger mouseleave (mouseleave isn't
\t\t// triggered when dragging an object).
\t\t// ondragleave event is not relyable to do it (not working as intended)
\t\tif (data.from) {
\t\t\tUIManager.getComponent(data.from).ui.trigger('mouseleave');
\t\t}

\t\t// Just support items ?
\t\tif (data.type !== 'item' || data.from !== 'Inventory') {
\t\t\treturn false;
\t\t}

\t\t// Can't drop an item on map if Equipment window is open
\t\tif (Equipment.getUI().ui.is(':visible')) {
\t\t\tChatBox.addText(DB.getMessage(189), ChatBox.TYPE.ERROR, ChatBox.FILTER.ITEM);
\t\t\treturn false;
\t\t}`;

const replaceMapDrop = `\t/**
\t * Drop items to the map (robust drag-drop with _OBJ_DRAG_ fallback)
\t */
\tfunction onDrop(event) {
\t\tvar item, data;

\t\ttry {
\t\t\tdata = JSON.parse(event.originalEvent.dataTransfer.getData('Text'));
\t\t} catch (e) {}

\t\tif (!data && window._OBJ_DRAG_) {
\t\t\tdata = window._OBJ_DRAG_;
\t\t}

\t\t// Stop default behavior
\t\tevent.stopImmediatePropagation();
\t\tif (!data) {
\t\t\treturn false;
\t\t}

\t\t// Hacky way to trigger mouseleave
\t\tif (data.from && UIManager.getComponent(data.from)) {
\t\t\tUIManager.getComponent(data.from).ui.trigger('mouseleave');
\t\t}

\t\t// Just support items ?
\t\tif (data.type !== 'item' || data.from !== 'Inventory') {
\t\t\treturn false;
\t\t}`;

for (const [oldStr, newStr] of [
	[targetMapDrop.replace(/\n/g, '\r\n'), replaceMapDrop.replace(/\n/g, '\r\n')],
	[targetMapDrop, replaceMapDrop]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 18c (Reliable MapControl drop handling & equipment unblock) applied');
		break;
	}
}

// Patch 18d: Attach drop listeners to document for full playfield drop detection
const targetMapInitDrop = `\t\t// Attach events
\t\tjQuery(Renderer.canvas)
\t\t\t.on('mousewheel DOMMouseScroll', onMouseWheel)
\t\t\t.on('dragover', onDragOver)
\t\t\t.on('drop', onDrop.bind(this));`;

const replaceMapInitDrop = `\t\t// Attach events
\t\tjQuery(Renderer.canvas)
\t\t\t.on('mousewheel DOMMouseScroll', onMouseWheel)
\t\t\t.on('dragover', onDragOver)
\t\t\t.on('drop', onDrop.bind(this));

\t\tjQuery(document)
\t\t\t.on('dragover', onDragOver)
\t\t\t.on('drop', onDrop.bind(this));`;

for (const [oldStr, newStr] of [
	[targetMapInitDrop.replace(/\n/g, '\r\n'), replaceMapInitDrop.replace(/\n/g, '\r\n')],
	[targetMapInitDrop, replaceMapInitDrop]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 18d (Document-wide ground drop listener) applied');
		break;
	}
}

// Patch 19: BGM CDN fallback, sequential playback & Tree of Savior support
const targetBgmLoad = `\t\t// load the file.
\t\tif (Preferences.BGM.play) {
\t\t\tClient.loadFile('BGM/' + filename, function (url) {
\t\t\t\tBGM.load(url);
\t\t\t});
\t\t}
\t};

\t/**
\t * Load the audio file
\t *
\t * @param {string} url (HTTP / DATA URI or BLOB)
\t */
\tBGM.load = function load(url) {
\t\tif (!Preferences.BGM.play) {
\t\t\treturn;
\t\t}

\t\t// Add support for other extensions, only supported with
\t\t// remote audio files.
\t\tif (!url.match(/^(blob|data):/)) {
\t\t\turl = url.replace(/mp3$/i, BGM.extension);
\t\t}

\t\tBGM.audio.src = url;
\t\tBGM.audio.volume = this.volume;
\t\tBGM.audio.play().catch(error => {
\t\t\tconsole.error('Failed to play "BGM/' + this.filename + '": ' + error.message);
\t\t});
\t};`;

const replaceBgmLoad = `\t\t// load the file.
\t\tif (Preferences.BGM.play) {
\t\t\tvar bgmTrackLoaded = false;
\t\t\ttry {
\t\t\t\tClient.loadFile('BGM/' + filename, function (url) {
\t\t\t\t\tbgmTrackLoaded = true;
\t\t\t\t\tBGM.load(url);
\t\t\t\t}, function () {
\t\t\t\t\tif (!bgmTrackLoaded) {
\t\t\t\t\t\tBGM.load('https://grf.robrowser.com/BGM/' + filename);
\t\t\t\t\t}
\t\t\t\t});
\t\t} catch (e) {
\t\t\t\tBGM.load('https://grf.robrowser.com/BGM/' + filename);
\t\t\t}
\t\t}
\t};

\t/**
\t * Load the audio file (with roBrowser CDN fallback & Tree of Savior sequential playback)
\t *
\t * @param {string} url (HTTP / DATA URI or BLOB)
\t */
\tBGM.currentPlaylist = BGM.currentPlaylist || [];
\tBGM.playlistIndex = BGM.playlistIndex || 0;
\tBGM.onEnded = function () {
\t\tif (BGM.currentPlaylist && BGM.currentPlaylist.length > 1) {
\t\t\tBGM.playlistIndex = (BGM.playlistIndex + 1) % BGM.currentPlaylist.length;
\t\t\tvar nextTrack = BGM.currentPlaylist[BGM.playlistIndex];
\t\t\tconsole.log('[BGM] Track finished. Advancing ToS Playlist (' + (BGM.playlistIndex + 1) + '/' + BGM.currentPlaylist.length + '): ' + nextTrack);
\t\t\tBGM.play(nextTrack);
\t\t} else {
\t\t\tconsole.log('[BGM] Single track finished. Replaying: ' + BGM.filename);
\t\t\tif (BGM.audio) {
\t\t\t\tBGM.audio.currentTime = 0;
\t\t\t\tBGM.audio.play();
\t\t\t}
\t\t}
\t};
\tBGM.next = function () {
\t\tBGM.onEnded();
\t};
\tif (typeof window !== 'undefined') {
\t\twindow.BGM = BGM;
\t}

\tBGM.load = function load(url) {
\t\tif (!Preferences.BGM.play) {
\t\t\treturn;
\t\t}

\t\tvar cleanFile = (this.filename || '01.mp3').replace(/^.*[\\\\/]/, '');
\t\tvar cdnUrl = 'https://grf.robrowser.com/BGM/' + cleanFile;

\t\t// If it is not a local blob/data from GRF, use CDN directly
\t\tif (!url || !url.match(/^(blob|data):/)) {
\t\t\turl = cdnUrl;
\t\t}

\t\tvar audio = BGM.audio;
\t\taudio.loop = false;
\t\tif (!audio._hasTosEndedHook) {
\t\t\taudio._hasTosEndedHook = true;
\t\t\taudio.addEventListener('ended', function () {
\t\t\t\tif (typeof BGM.onEnded === 'function') {
\t\t\t\t\tBGM.onEnded();
\t\t\t\t}
\t\t\t}, false);
\t\t}

\t\tvar playTarget = function(src) {
\t\t\taudio.src = src;
\t\t\taudio.volume = BGM.volume;
\t\t\tvar promise = audio.play();
\t\t\tif (promise && promise.catch) {
\t\t\t\tpromise.catch(function(err) {
\t\t\t\t\tconsole.warn('[BGM] Play error on ' + src + ':', err.message);
\t\t\t\t\tif (src !== cdnUrl) {
\t\t\t\t\t\tconsole.log('[BGM] Falling back to CDN: ' + cdnUrl);
\t\t\t\t\t\tplayTarget(cdnUrl);
\t\t\t\t\t}
\t\t\t\t});
\t\t\t}
\t\t};

\t\taudio.onerror = function() {
\t\t\tif (audio.src !== cdnUrl) {
\t\t\t\tconsole.log('[BGM] Audio element error, falling back to CDN: ' + cdnUrl);
\t\t\t\tplayTarget(cdnUrl);
\t\t\t}
\t\t};

\t\tplayTarget(url);
\t};`;

// Apply Patch 19 (match either original or previously patched version)
if (content.includes('// Load the audio file (with roBrowser CDN fallback)')) {
	content = content.replace(
		/\/\*\*[\s\S]*?Load the audio file \(with roBrowser CDN fallback\)[\s\S]*?playTarget\(url\);\s*\};/,
		replaceBgmLoad.slice(replaceBgmLoad.indexOf('/**\n\t * Load the audio file'))
	);
	patches++;
	console.log('✓ Patch 19 upgraded (Tree of Savior sequential BGM audio loop & ended hook)');
} else {
	for (const [oldStr, newStr] of [
		[targetBgmLoad.replace(/\n/g, '\r\n'), replaceBgmLoad.replace(/\n/g, '\r\n')],
		[targetBgmLoad, replaceBgmLoad]
	]) {
		if (content.includes(oldStr)) {
			content = content.replace(oldStr, newStr);
			patches++;
			console.log('✓ Patch 19 (BGM CDN fallback & Tree of Savior sequential audio) applied');
			break;
		}
	}
}

// Patch 20: Tree of Savior Style Deterministic BGM System (100% Track Coverage)
const tosBgmCode = `\t/**
\t * Tree of Savior Style Deterministic BGM System (100% Track Coverage)
\t */
\tvar EXPLICIT_PLAYLISTS = {
\t\t"prontera": ["06.mp3", "01.mp3", "42.mp3", "39.mp3"],
\t\t"geffen": ["08.mp3", "04.mp3", "39.mp3", "29.mp3"],
\t\t"morocc": ["07.mp3", "19.mp3", "46.mp3", "27.mp3"],
\t\t"payon": ["09.mp3", "22.mp3", "54.mp3", "45.mp3"],
\t\t"alberta": ["10.mp3", "41.mp3", "63.mp3", "76.mp3"],
\t\t"izlude": ["11.mp3", "04.mp3", "12.mp3", "42.mp3"],
\t\t"aldebaran": ["13.mp3", "38.mp3", "50.mp3", "01.mp3"],
\t\t"lutie": ["18.mp3", "17.mp3", "23.mp3", "70.mp3"],
\t\t"xmas": ["18.mp3", "17.mp3", "23.mp3", "70.mp3"],
\t\t"comodo": ["14.mp3", "49.mp3", "76.mp3", "63.mp3"],
\t\t"yuno": ["26.mp3", "57.mp3", "100.mp3", "08.mp3"],
\t\t"einbroch": ["60.mp3", "75.mp3", "78.mp3", "50.mp3"],
\t\t"einbech": ["78.mp3", "75.mp3", "60.mp3", "50.mp3"],
\t\t"lighthalzen": ["83.mp3", "84.mp3", "59.mp3", "118.mp3"],
\t\t"hugel": ["88.mp3", "85.mp3", "90.mp3", "33.mp3"],
\t\t"rachel": ["61.mp3", "91.mp3", "113.mp3", "77.mp3"],
\t\t"veins": ["94.mp3", "93.mp3", "116.mp3", "46.mp3"],
\t\t"amatsu": ["64.mp3", "54.mp3", "81.mp3", "09.mp3"],
\t\t"gonryun": ["65.mp3", "82.mp3", "68.mp3", "72.mp3"],
\t\t"louyang": ["68.mp3", "69.mp3", "65.mp3", "54.mp3"],
\t\t"ayothaya": ["72.mp3", "73.mp3", "68.mp3", "81.mp3"],
\t\t"moscovia": ["98.mp3", "96.mp3", "97.mp3", "88.mp3"],
\t\t"brasilis": ["106.mp3", "105.mp3", "108.mp3", "14.mp3"],
\t\t"jawaii": ["76.mp3", "63.mp3", "14.mp3", "10.mp3"],
\t\t"umbala": ["67.mp3", "14.mp3", "72.mp3"],
\t\t"dewata": ["125.mp3", "126.mp3", "127.mp3"],
\t\t"malangdo": ["128.mp3", "129.mp3", "130.mp3"],
\t\t"malaya": ["132.mp3", "133.mp3", "134.mp3"],
\t\t"eclage": ["135.mp3", "136.mp3", "137.mp3"],
\t\t"mora": ["121.mp3", "122.mp3", "124.mp3"],
\t\t"mid_camp": ["101.mp3", "111.mp3", "112.mp3"],
\t\t"splendide": ["102.mp3", "101.mp3", "114.mp3"],
\t\t"manuk": ["103.mp3", "101.mp3", "115.mp3"],
\t\t"dicastes01": ["109.mp3", "110.mp3", "123.mp3"],
\t\t"glast_01": ["43.mp3", "40.mp3", "48.mp3", "87.mp3", "141.mp3"],
\t\t"gl_cas01": ["43.mp3", "40.mp3", "48.mp3", "87.mp3", "141.mp3"],
\t\t"gl_prison": ["48.mp3", "40.mp3", "43.mp3", "141.mp3"],
\t\t"niflheim": ["71.mp3", "66.mp3", "40.mp3", "48.mp3"],
\t\t"abbey01": ["87.mp3", "48.mp3", "43.mp3", "71.mp3"],
\t\t"nameless_n": ["87.mp3", "48.mp3", "43.mp3", "71.mp3"],
\t\t"lhz_dun01": ["84.mp3", "48.mp3", "140.mp3", "43.mp3"],
\t\t"lhz_dun02": ["84.mp3", "48.mp3", "140.mp3", "43.mp3"],
\t\t"lhz_dun03": ["84.mp3", "48.mp3", "140.mp3", "43.mp3"],
\t\t"ice_dun01": ["79.mp3", "16.mp3", "74.mp3", "142.mp3"],
\t\t"ice_dun02": ["79.mp3", "16.mp3", "74.mp3", "142.mp3"],
\t\t"ice_dun03": ["79.mp3", "16.mp3", "74.mp3", "142.mp3"],
\t\t"xmas_dun01": ["16.mp3", "74.mp3", "17.mp3", "142.mp3"],
\t\t"xmas_dun02": ["74.mp3", "16.mp3", "17.mp3", "142.mp3"],
\t\t"mag_dun01": ["15.mp3", "107.mp3", "52.mp3", "03.mp3"],
\t\t"mag_dun02": ["15.mp3", "107.mp3", "52.mp3", "03.mp3"],
\t\t"thor_v01": ["107.mp3", "52.mp3", "03.mp3", "15.mp3"],
\t\t"thor_v02": ["107.mp3", "52.mp3", "03.mp3", "15.mp3"],
\t\t"thor_v03": ["107.mp3", "52.mp3", "03.mp3", "15.mp3"],
\t\t"juperos_01": ["57.mp3", "38.mp3", "51.mp3", "151.mp3"],
\t\t"jupe_core": ["57.mp3", "51.mp3", "151.mp3", "152.mp3"],
\t\t"tha_t01": ["77.mp3", "92.mp3", "89.mp3", "62.mp3"],
\t\t"tha_t06": ["92.mp3", "77.mp3", "89.mp3", "62.mp3"],
\t\t"odin_tem01": ["89.mp3", "92.mp3", "77.mp3", "131.mp3"],
\t\t"odin_tem02": ["89.mp3", "92.mp3", "77.mp3", "131.mp3"],
\t\t"c_tower1": ["38.mp3", "51.mp3", "86.mp3", "57.mp3"],
\t\t"c_tower2": ["38.mp3", "51.mp3", "86.mp3", "57.mp3"],
\t\t"c_tower3": ["51.mp3", "38.mp3", "86.mp3", "57.mp3"],
\t\t"c_tower4": ["51.mp3", "38.mp3", "86.mp3", "57.mp3"],
\t\t"kh_dun01": ["86.mp3", "59.mp3", "38.mp3", "51.mp3"],
\t\t"kh_school": ["59.mp3", "86.mp3", "38.mp3", "51.mp3"],
\t\t"ra_san01": ["91.mp3", "77.mp3", "113.mp3", "89.mp3"],
\t\t"abyss_01": ["53.mp3", "104.mp3", "47.mp3", "138.mp3"],
\t\t"abyss_02": ["53.mp3", "104.mp3", "47.mp3", "138.mp3"],
\t\t"abyss_03": ["53.mp3", "104.mp3", "47.mp3", "138.mp3"],
\t\t"nyd_dun01": ["104.mp3", "53.mp3", "77.mp3", "139.mp3"],
\t\t"verus01": ["151.mp3", "152.mp3", "153.mp3", "154.mp3"],
\t\t"prt_sewb1": ["02.mp3", "15.mp3", "28.mp3", "30.mp3"],
\t\t"pay_dun00": ["45.mp3", "30.mp3", "56.mp3", "81.mp3"],
\t\t"gef_dun00": ["30.mp3", "02.mp3", "56.mp3", "45.mp3"],
\t\t"anthell01": ["28.mp3", "02.mp3", "15.mp3", "110.mp3"],
\t\t"moc_pryd01": ["24.mp3", "20.mp3", "27.mp3", "46.mp3"],
\t\t"in_sphinx1": ["27.mp3", "24.mp3", "46.mp3", "19.mp3"],
\t\t"treasure01": ["36.mp3", "41.mp3", "10.mp3", "02.mp3"],
\t\t"orcsdun01": ["02.mp3", "28.mp3", "15.mp3", "03.mp3"],
\t\t"mjo_dun01": ["28.mp3", "78.mp3", "02.mp3", "15.mp3"],
\t\t"tur_dun01": ["36.mp3", "56.mp3", "25.mp3", "10.mp3"],
\t\t"ein_dun01": ["78.mp3", "75.mp3", "50.mp3", "60.mp3"],
\t\t"bra_dun01": ["108.mp3", "105.mp3", "97.mp3", "106.mp3"],
\t\t"mosk_dun01": ["97.mp3", "96.mp3", "98.mp3", "88.mp3"],
\t\t"endless": ["99.mp3", "47.mp3", "95.mp3", "92.mp3"],
\t\t"bossnia_01": ["95.mp3", "47.mp3", "52.mp3", "03.mp3"],
\t\t"pvp_y_1-1": ["03.mp3", "52.mp3", "47.mp3", "95.mp3"],
\t\t"guild_vs1": ["58.mp3", "47.mp3", "55.mp3", "62.mp3"],
\t\t"1@face": ["143.mp3", "144.mp3", "145.mp3"],
\t\t"1@ge_st": ["146.mp3", "147.mp3", "148.mp3"],
\t\t"1@sara": ["149.mp3", "150.mp3", "155.mp3"],
\t\t"1@air1": ["156.mp3", "157.mp3", "158.mp3"],
\t\t"1@tnm1": ["159.mp3", "160.mp3", "117.mp3"],
\t\t"1@dth1": ["119.mp3", "120.mp3", "114.mp3"],
\t\t"prt_fild08": ["12.mp3", "04.mp3", "21.mp3", "33.mp3"],
\t\t"gef_fild07": ["05.mp3", "29.mp3", "34.mp3", "35.mp3"],
\t\t"mjolnir_01": ["31.mp3", "35.mp3", "29.mp3", "04.mp3"],
\t\t"pay_fild01": ["22.mp3", "37.mp3", "21.mp3", "80.mp3"],
\t\t"prt_monk": ["44.mp3", "42.mp3", "01.mp3"]
\t};

\tvar BGM_BIOMES = {
\t\ttowns: ["06.mp3", "01.mp3", "08.mp3", "10.mp3", "39.mp3"],
\t\tfields: ["04.mp3", "05.mp3", "12.mp3", "21.mp3", "22.mp3"],
\t\tdungeons: ["02.mp3", "15.mp3", "28.mp3", "30.mp3", "56.mp3"],
\t\tdesert: ["07.mp3", "19.mp3", "20.mp3", "24.mp3", "27.mp3"],
\t\tspooky: ["40.mp3", "43.mp3", "48.mp3", "71.mp3", "87.mp3"],
\t\tsnow: ["18.mp3", "16.mp3", "17.mp3", "23.mp3", "70.mp3"],
\t\toriental: ["64.mp3", "65.mp3", "68.mp3", "72.mp3", "54.mp3"],
\t\tvolcano: ["15.mp3", "107.mp3", "52.mp3", "03.mp3"],
\t\tancient_tech: ["38.mp3", "51.mp3", "57.mp3", "86.mp3", "77.mp3"],
\t\tbattle_boss: ["47.mp3", "52.mp3", "55.mp3", "58.mp3", "95.mp3"],
\t\ttropical: ["14.mp3", "49.mp3", "63.mp3", "76.mp3", "10.mp3"]
\t};

\tvar BGM_BIOME_RULES = [
\t\t{ theme: "battle_boss", regex: /(^|_)(guild_|gld_|gld2_|pvp_|arena|bossnia|endless|poring_w|force_|te_prt|te_aldeg|_gld|cas\\d|g_room|ordeal|prt_are|battle|camp|nguild_|siege|_castle)/i },
\t\t{ theme: "volcano", regex: /(^|_)(mag_dun|thor_v|thor_camp)/i },
\t\t{ theme: "snow", regex: /(^|_)(xmas|ice_dun|toy_factory)/i },
\t\t{ theme: "desert", regex: /(^|_)(moc_fild|moc_pryd|moc_ruins|in_sphinx|morocc|moc_castle|in_moc)/i },
\t\t{ theme: "spooky", regex: /(^|_)(gl_|glast|niflheim|nif_|abbey|nameless|lhz_dun|monastery|sec_pri)/i },
\t\t{ theme: "tropical", regex: /(^|_)(comodo|cmd_|jawaii|beach_dun|alb2trea|umbala)/i },
\t\t{ theme: "oriental", regex: /(^|_)(amatsu|ama_|gonryun|gon_|louyang|lou_|ayothaya|ayo_)/i },
\t\t{ theme: "ancient_tech", regex: /(^|_)(juperos|jupe_|c_tower|alde_dun|kh_|kiel|tha_t|thana|ra_san|odin_tem|abyss|nyd_dun|yggdrasil|valkyrie|himinn|gefenia|verus)/i },
\t\t{ theme: "dungeons", regex: /(^|_)(prt_sewb|pay_dun|gef_dun|anthell|treasure|orcsdun|mjo_dun|tur_dun|bra_dun|mosk_dun|ein_dun|dic_dun|man_dun|dew_dun|sewer|cave|dun|izlu2dun|in_orcs)/i },
\t\t{ theme: "fields", regex: /(^|_)(fild|prt_maze|pay_arche|mjolnir|new_\\d|job_|hunter_|knight_|priest_|sword_|wizard_|assassin_|quiz)/i },
\t\t{ theme: "towns", regex: /(^|_)(prontera|prt_|geffen|gef_|payon|pay_|alberta|alb_|izlude|izl_|aldebaran|alde|yuno|lutie|einbroch|einbech|ein_|lighthalzen|lhz_|hugel|hu_|rachel|ra_|veins|ve_|moscovia|mosk_|brasilis|bra_|splendide|manuk|mid_camp|mora|dewata|malaya|lasagna|alb_ship|sec_in|gef_tower|airplane|monk_in)|_in$|_in\\d|in_/i }
\t];

\tfunction getMapPlaylist(mapName, defaultMp3) {
\t\tvar cleanMap = (mapName || "").replace(/\\.(gat|rsw)$/i, "").toLowerCase();

\t\t// 1. Direct match in EXPLICIT_PLAYLISTS
\t\tif (EXPLICIT_PLAYLISTS[cleanMap]) {
\t\t\treturn EXPLICIT_PLAYLISTS[cleanMap].slice();
\t\t}

\t\t// 2. Prefix match in EXPLICIT_PLAYLISTS
\t\tfor (var key in EXPLICIT_PLAYLISTS) {
\t\t\tif (cleanMap.indexOf(key) === 0 || key.indexOf(cleanMap) === 0) {
\t\t\t\treturn EXPLICIT_PLAYLISTS[key].slice();
\t\t\t}
\t\t}

\t\t// 3. Biome match
\t\tvar chosenTheme = "fields";
\t\tfor (var r = 0; r < BGM_BIOME_RULES.length; r++) {
\t\t\tif (BGM_BIOME_RULES[r].regex.test(cleanMap)) {
\t\t\t\tchosenTheme = BGM_BIOME_RULES[r].theme;
\t\t\t\tbreak;
\t\t\t}
\t\t}

\t\tvar biomeTracks = BGM_BIOMES[chosenTheme] || BGM_BIOMES.fields;
\t\tvar cleanDefault = defaultMp3 ? defaultMp3.replace(/^.*[\\\\/]/, "").toLowerCase() : null;

\t\tif (cleanDefault && cleanDefault.endsWith(".mp3")) {
\t\t\tvar list = [cleanDefault];
\t\t\tfor (var i = 0; i < biomeTracks.length; i++) {
\t\t\t\tif (biomeTracks[i].toLowerCase() !== cleanDefault && list.length < 4) {
\t\t\t\t\tlist.push(biomeTracks[i]);
\t\t\t\t}
\t\t\t}
\t\t\treturn list;
\t\t}

\t\treturn biomeTracks.slice(0, 4);
\t}

\t/**
\t * Once the map finished to load (Deterministic Tree of Savior Playlist)
\t */
\tfunction onMapComplete(success, error) {
\t\tvar worldResource = this.currentMap.replace(/\\.gat$/i, '.rsw');
\t\tvar mapInfo = DB.getMap(worldResource);

\t\t// Problem during loading ?
\t\tif (!success) {
\t\t\tUIManager.showErrorBox(error).ui.css('zIndex', 1000);
\t\t\treturn;
\t\t}

\t\t// Play BGM (Deterministic Tree of Savior Playlist)
\t\tvar isSameMap = (this._currentBgmMap === this.currentMap);
\t\tthis._currentBgmMap = this.currentMap;

\t\tif (!isSameMap || !BGM.audio || BGM.audio.paused) {
\t\t\tvar playlist = getMapPlaylist(this.currentMap, mapInfo && mapInfo.mp3);
\t\t\tBGM.currentPlaylist = playlist;
\t\t\tif (!isSameMap) {
\t\t\t\tBGM.playlistIndex = 0;
\t\t\t}
\t\t\tvar trackToPlay = BGM.currentPlaylist[BGM.playlistIndex || 0] || '01.mp3';
\t\t\tconsole.log('[BGM] Map="' + this.currentMap + '" -> ToS Playlist: [' + playlist.join(', ') + '] -> Playing track ' + ((BGM.playlistIndex || 0) + 1) + ': ' + trackToPlay);
\t\t\tBGM.play(trackToPlay);
\t\t}`;

// Apply Patch 20 (match either original or previously patched version)
if (content.includes('Thematic BGM Groups & Randomization System')) {
	content = content.replace(
		/\/\*\*[\s\S]*?Thematic BGM Groups & Randomization System[\s\S]*?BGM\.play\(selectedBgm\);\s*\}/,
		tosBgmCode
	);
	patches++;
	console.log('✓ Patch 20 upgraded to Tree of Savior Deterministic Playlist System (100% Track Coverage)');
} else {
	const targetBgmMap = `\t/**
\t * Once the map finished to load
\t */
\tfunction onMapComplete(success, error) {
\t\tvar worldResource = this.currentMap.replace(/\\.gat$/i, '.rsw');
\t\tvar mapInfo = DB.getMap(worldResource);

\t\t// Problem during loading ?
\t\tif (!success) {
\t\t\tUIManager.showErrorBox(error).ui.css('zIndex', 1000);
\t\t\treturn;
\t\t}

\t\t// Play BGM
\t\tBGM.play((mapInfo && mapInfo.mp3) || '01.mp3');`;

	for (const [oldStr, newStr] of [
		[targetBgmMap.replace(/\n/g, '\r\n'), tosBgmCode.replace(/\n/g, '\r\n')],
		[targetBgmMap, tosBgmCode]
	]) {
		if (content.includes(oldStr)) {
			content = content.replace(oldStr, newStr);
			patches++;
			console.log('✓ Patch 20 (Tree of Savior Deterministic BGM System) applied');
			break;
		}
	}
}

fs.writeFileSync(onlinePath, content, 'utf8');

// Patch ThreadEventHandler.js para desativar cache local no itemInfo.lua
const threadPath = onlinePath.replace('Online.js', 'ThreadEventHandler.js');
if (fs.existsSync(threadPath)) {
	console.log(`Patching ${threadPath}...`);
	let threadContent = fs.readFileSync(threadPath, 'utf8');
	let threadPatches = 0;

	// 1. Bypass FileSystem.getFile for itemInfo in ThreadEventHandler.js
	const targetGet = `\t\t// Search in filesystem
\t\tFileSystem.getFile(
\t\t\tfilename,

\t\t\t// Found in file system, youhou !
\t\t\tfunction onFound(file) {
\t\t\t\tvar reader = new FileReader();
\t\t\t\treader.onloadend = function onLoad(event) {
\t\t\t\t\tcallback(event.target.result);
\t\t\t\t};
\t\t\t\treader.readAsArrayBuffer(file);
\t\t\t},

\t\t\t// Not found, fetching files
\t\t\tfunction onNotFound() {
\t\t\t\tvar i, count;
\t\t\t\tvar fileList;
\t\t\t\tvar path;

\t\t\t\tpath = filename.replace(/\\//g, '\\\\');
\t\t\t\tfileList = FileManager.gameFiles;
\t\t\t\tcount = fileList.length;

\t\t\t\tfor (i = 0; i < count; ++i) {
\t\t\t\t\tif (fileList[i].getFile(path, callback)) {
\t\t\t\t\t\treturn;
\t\t\t\t\t}
\t\t\t\t}

\t\t\t\t// Not in GRFs ? Try to load it from
\t\t\t\t// remote client host
\t\t\t\tFileManager.getHTTP(filename, callback);
\t\t\t}
\t\t);`;

	const replaceGet = `\t\t// Search in filesystem
\t\tvar _isItemInfo = /itemInfo/i.test(filename);
\t\tvar _onNotFound = function () {
\t\t\tvar i, count;
\t\t\tvar fileList;
\t\t\tvar path;

\t\t\tpath = filename.replace(/\\//g, '\\\\');
\t\t\tfileList = FileManager.gameFiles;
\t\t\tcount = fileList.length;

\t\t\tfor (i = 0; i < count; ++i) {
\t\t\t\tif (fileList[i].getFile(path, callback)) {
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t}

\t\t\tFileManager.getHTTP(filename, callback);
\t\t};

\t\tif (!_isItemInfo) {
\t\t\tFileSystem.getFile(
\t\t\t\tfilename,
\t\t\t\tfunction onFound(file) {
\t\t\t\t\tvar reader = new FileReader();
\t\t\t\t\treader.onloadend = function onLoad(event) {
\t\t\t\t\t\tcallback(event.target.result);
\t\t\t\t\t};
\t\t\t\t\treader.readAsArrayBuffer(file);
\t\t\t\t},
\t\t\t\t_onNotFound
\t\t\t);
\t\t} else {
\t\t\t_onNotFound();
\t\t}`;

	for (const [oldStr, newStr] of [
		[targetGet.replace(/\n/g, '\r\n'), replaceGet.replace(/\n/g, '\r\n')],
		[targetGet, replaceGet]
	]) {
		if (threadContent.includes(oldStr)) {
			threadContent = threadContent.replace(oldStr, newStr);
			threadPatches++;
			console.log('✓ Thread Patch 1 (itemInfo bypass FileSystem.getFile) applied');
			break;
		}
	}

	// 2. Fetch with cache busting and do not save itemInfo to local FileSystem
	const targetHttp = `\t\tvar xhr = new XMLHttpRequest();
\t\txhr.open('GET', url, true);
\t\txhr.responseType = 'arraybuffer';
\t\txhr.onload = function () {
\t\t\tif (xhr.status == 200) {
\t\t\t\tcallback(xhr.response);
\t\t\t\tFileSystem.saveFile(filename, xhr.response);
\t\t\t} else {
\t\t\t\tcallback(null, "Can't get file");
\t\t\t}
\t\t};`;

	const replaceHttp = `\t\tvar xhr = new XMLHttpRequest();
\t\tvar requestUrl = /itemInfo/i.test(filename) ? url + '?_t=' + Date.now() : url;
\t\txhr.open('GET', requestUrl, true);
\t\txhr.responseType = 'arraybuffer';
\t\txhr.onload = function () {
\t\t\tif (xhr.status == 200) {
\t\t\t\tcallback(xhr.response);
\t\t\t\tif (!/itemInfo/i.test(filename)) {
\t\t\t\t\tFileSystem.saveFile(filename, xhr.response);
\t\t\t\t}
\t\t\t} else {
\t\t\t\tcallback(null, "Can't get file");
\t\t\t}
\t\t};`;

	for (const [oldStr, newStr] of [
		[targetHttp.replace(/\n/g, '\r\n'), replaceHttp.replace(/\n/g, '\r\n')],
		[targetHttp, replaceHttp]
	]) {
		if (threadContent.includes(oldStr)) {
			threadContent = threadContent.replace(oldStr, newStr);
			threadPatches++;
			console.log('✓ Thread Patch 2 (itemInfo no-cache & no FileSystem.saveFile) applied');
			break;
		}
	}

	if (threadPatches > 0) {
		fs.writeFileSync(threadPath, threadContent, 'utf8');
		console.log(`ThreadEventHandler patched: ${threadPatches} patches applied.`);
	}
}

// Patch individual Inventory components if present
['InventoryV0', 'InventoryV1', 'InventoryV2', 'InventoryV3'].forEach(v => {
	const invPath = onlinePath.replace('Online.js', `src/UI/Components/Inventory/${v}/${v}.js`);
	if (fs.existsSync(invPath)) {
		let invContent = fs.readFileSync(invPath, 'utf8');
		let invPatches = 0;
		for (const [oldStr, newStr] of [
			[targetInvDrag.replace(/\n/g, '\r\n'), replaceInvDrag.replace(/\n/g, '\r\n')],
			[targetInvDrag, replaceInvDrag]
		]) {
			if (invContent.includes(oldStr)) {
				invContent = invContent.replace(oldStr, newStr);
				invPatches++;
				break;
			}
		}
		for (const [oldStr, newStr] of [
			[targetInvDragEnd.replace(/\n/g, '\r\n'), replaceInvDragEnd.replace(/\n/g, '\r\n')],
			[targetInvDragEnd, replaceInvDragEnd]
		]) {
			if (invContent.includes(oldStr)) {
				invContent = invContent.replace(oldStr, newStr);
				invPatches++;
				break;
			}
		}
		if (invPatches > 0) {
			fs.writeFileSync(invPath, invContent, 'utf8');
			console.log(`✓ Patched ${v}.js (${invPatches} patches)`);
		}
	}
});

// Patch src/Audio/BGM.js for Tree of Savior sequential playback
const bgmPath = onlinePath.replace('Online.js', 'src/Audio/BGM.js');
if (fs.existsSync(bgmPath)) {
	let bgmContent = fs.readFileSync(bgmPath, 'utf8');
	let bgmPatches = 0;

	// Disable loop and add onEnded listener hook
	const targetBgmInit = `\t\t// Buggy looping for HTM5 Audio...
\t\tif (typeof BGM.audio.loop === 'boolean') {
\t\t\tBGM.audio.loop = true;
\t\t\treturn;
\t\t}

\t\t// Work around
\t\tBGM.audio.addEventListener(
\t\t\t'ended',
\t\t\tfunction () {
\t\t\t\tBGM.audio.currentTime = 0;
\t\t\t\tBGM.audio.play();
\t\t\t},
\t\t\tfalse
\t\t);`;

	const replaceBgmInit = `\t\t// Tree of Savior Sequential Audio Playback
\t\tBGM.audio.loop = false;
\t\tif (!BGM.audio._hasTosEndedHook) {
\t\t\tBGM.audio._hasTosEndedHook = true;
\t\t\tBGM.audio.addEventListener('ended', function () {
\t\t\t\tif (typeof BGM.onEnded === 'function') {
\t\t\t\t\tBGM.onEnded();
\t\t\t\t} else if (BGM.audio) {
\t\t\t\t\tBGM.audio.currentTime = 0;
\t\t\t\t\tBGM.audio.play();
\t\t\t\t}
\t\t\t}, false);
\t\t}`;

	for (const [oldStr, newStr] of [
		[targetBgmInit.replace(/\n/g, '\r\n'), replaceBgmInit.replace(/\n/g, '\r\n')],
		[targetBgmInit, replaceBgmInit]
	]) {
		if (bgmContent.includes(oldStr)) {
			bgmContent = bgmContent.replace(oldStr, newStr);
			bgmPatches++;
			break;
		}
	}

	// Add BGM.onEnded, BGM.next, and CDN fallback to BGM.load
	const targetBgmLoadSrc = `\tBGM.load = function load(url) {
\t\tif (!Preferences.BGM.play) {
\t\t\treturn;
\t\t}

\t\t// Add support for other extensions, only supported with
\t\t// remote audio files.
\t\tif (!url.match(/^(blob|data):/)) {
\t\t\turl = url.replace(/mp3$/i, BGM.extension);
\t\t}

\t\tBGM.audio.src = url;
\t\tBGM.audio.volume = this.volume;
\t\tBGM.audio.play().catch(error => {
\t\t\tconsole.error('Failed to play "BGM/' + this.filename + '": ' + error.message);
\t\t});
\t};`;

	const replaceBgmLoadSrc = `\tBGM.currentPlaylist = BGM.currentPlaylist || [];
\tBGM.playlistIndex = BGM.playlistIndex || 0;
\tBGM.onEnded = function () {
\t\tif (BGM.currentPlaylist && BGM.currentPlaylist.length > 1) {
\t\t\tBGM.playlistIndex = (BGM.playlistIndex + 1) % BGM.currentPlaylist.length;
\t\t\tvar nextTrack = BGM.currentPlaylist[BGM.playlistIndex];
\t\t\tconsole.log('[BGM] Track finished. Advancing ToS Playlist (' + (BGM.playlistIndex + 1) + '/' + BGM.currentPlaylist.length + '): ' + nextTrack);
\t\t\tBGM.play(nextTrack);
\t\t} else {
\t\t\tif (BGM.audio) {
\t\t\t\tBGM.audio.currentTime = 0;
\t\t\t\tBGM.audio.play();
\t\t\t}
\t\t}
\t};
\tBGM.next = function () {
\t\tBGM.onEnded();
\t};
\tif (typeof window !== 'undefined') {
\t\twindow.BGM = BGM;
\t}

\tBGM.load = function load(url) {
\t\tif (!Preferences.BGM.play) {
\t\t\treturn;
\t\t}

\t\tvar cleanFile = (this.filename || '01.mp3').replace(/^.*[\\\\/]/, '');
\t\tvar cdnUrl = 'https://grf.robrowser.com/BGM/' + cleanFile;
\t\tif (!url || !url.match(/^(blob|data):/)) {
\t\t\turl = cdnUrl;
\t\t}

\t\tvar audio = BGM.audio;
\t\taudio.loop = false;
\t\tvar playTarget = function (src) {
\t\t\taudio.src = src;
\t\t\taudio.volume = BGM.volume;
\t\t\tvar promise = audio.play();
\t\t\tif (promise && promise.catch) {
\t\t\t\tpromise.catch(function (err) {
\t\t\t\t\tconsole.warn('[BGM] Play error on ' + src + ':', err.message);
\t\t\t\t\tif (src !== cdnUrl) {
\t\t\t\t\t\tplayTarget(cdnUrl);
\t\t\t\t\t}
\t\t\t\t});
\t\t\t}
\t\t};

\t\taudio.onerror = function () {
\t\t\tif (audio.src !== cdnUrl) {
\t\t\t\tplayTarget(cdnUrl);
\t\t\t}
\t\t};

\t\tplayTarget(url);
\t};`;

	for (const [oldStr, newStr] of [
		[targetBgmLoadSrc.replace(/\n/g, '\r\n'), replaceBgmLoadSrc.replace(/\n/g, '\r\n')],
		[targetBgmLoadSrc, replaceBgmLoadSrc]
	]) {
		if (bgmContent.includes(oldStr)) {
			bgmContent = bgmContent.replace(oldStr, newStr);
			bgmPatches++;
			break;
		}
	}

	if (bgmPatches > 0) {
		fs.writeFileSync(bgmPath, bgmContent, 'utf8');
		console.log(`✓ src/Audio/BGM.js patched for Tree of Savior (${bgmPatches} patches applied)`);
	}
}

console.log(`Done. Total patches applied: ${patches}`);

