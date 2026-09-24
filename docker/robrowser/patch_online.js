#!/usr/bin/env node
const fs = require('fs');

const onlinePath = process.argv[2] || '/opt/roBrowserLegacy/Online.js';
console.log(`Patching ${onlinePath}...`);

let content = fs.readFileSync(onlinePath, 'utf8');
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
		let count = 0;
		while (content.includes(oldStr)) {
			content = content.replace(oldStr, newStr);
			count++;
		}
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

// Patch 17: ItemObject ground drop sprite fallback
const targetItemObject = `		entity.files.body.spr = path + '.spr';
		entity.files.body.act = path + '.act';

		entity.files.shadow.size = 0.25;`;

const replaceItemObject = `		var defaultDropPath = 'data/sprite/\xbe\xc6\xc0\xcc\xc5\xdb/\xb3\xaa\xc0\xcc\xc7\xc1';
		entity.files.body.spr = path + '.spr';
		entity.files.body.act = path + '.act';

		Client.loadFile(path + '.spr', null, function () {
			entity.files.body.spr = defaultDropPath + '.spr';
			entity.files.body.act = defaultDropPath + '.act';
		});
		Client.loadFile(path + '.act', null, function () {
			entity.files.body.spr = defaultDropPath + '.spr';
			entity.files.body.act = defaultDropPath + '.act';
		});

		entity.files.shadow.size = 0.25;`;

for (const [oldStr, newStr] of [
	[targetItemObject.replace(/\n/g, '\r\n'), replaceItemObject.replace(/\n/g, '\r\n')],
	[targetItemObject, replaceItemObject]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 17 (ItemObject ground drop sprite fallback) applied');
		break;
	}
}

// Patch 18: renderElement item drop frame-level fallback
const targetRenderElement = `			// Get back sprite and act
			var spr = Client.loadFile(files.spr);
			var act = Client.loadFile(files.act);

			// Not loaded yet
			if (!spr || !act) {
				return;
			}`;

const replaceRenderElement = `			// Get back sprite and act
			var spr = Client.loadFile(files.spr);
			var act = Client.loadFile(files.act);

			if (entity.objecttype === 2 && (!spr || !act)) {
				var defaultDropPath = 'data/sprite/\xbe\xc6\xc0\xcc\xc5\xdb/\xb3\xaa\xc0\xcc\xc7\xc1';
				if (files.spr !== defaultDropPath + '.spr') {
					files._fallbackCount = (files._fallbackCount || 0) + 1;
					if (files._fallbackCount > 10) {
						files.spr = defaultDropPath + '.spr';
						files.act = defaultDropPath + '.act';
						spr = Client.loadFile(files.spr);
						act = Client.loadFile(files.act);
					}
				}
			}

			// Not loaded yet
			if (!spr || !act) {
				return;
			}`;

for (const [oldStr, newStr] of [
	[targetRenderElement.replace(/\n/g, '\r\n'), replaceRenderElement.replace(/\n/g, '\r\n')],
	[targetRenderElement, replaceRenderElement]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 18 (renderElement ground drop frame-level fallback) applied');
		break;
	}
}

// Patch 19: BGM CDN fallback & audio play error recovery
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
\t\t\t} catch (e) {
\t\t\t\tBGM.load('https://grf.robrowser.com/BGM/' + filename);
\t\t\t}
\t\t}
\t};

\t/**
\t * Load the audio file (with roBrowser CDN fallback)
\t *
\t * @param {string} url (HTTP / DATA URI or BLOB)
\t */
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

for (const [oldStr, newStr] of [
	[targetBgmLoad.replace(/\n/g, '\r\n'), replaceBgmLoad.replace(/\n/g, '\r\n')],
	[targetBgmLoad, replaceBgmLoad]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 19 (BGM CDN fallback & audio play error recovery) applied');
		break;
	}
}

// Patch 20: Thematic Map BGM Groups & Randomization System
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

const replaceBgmMap = `\t/**
\t * Thematic BGM Groups & Randomization System
\t */
\tvar BGM_THEMES = {
\t\ttowns: ['01.mp3', '06.mp3', '08.mp3', '09.mp3', '10.mp3', '11.mp3', '13.mp3', '26.mp3', '39.mp3', '42.mp3', '60.mp3', '61.mp3', '83.mp3', '88.mp3', '94.mp3', '98.mp3', '106.mp3'],
\t\tfields: ['04.mp3', '05.mp3', '12.mp3', '21.mp3', '22.mp3', '29.mp3', '31.mp3', '33.mp3', '34.mp3', '35.mp3', '37.mp3', '41.mp3', '80.mp3', '85.mp3', '90.mp3', '96.mp3', '105.mp3'],
\t\tdungeons: ['02.mp3', '15.mp3', '28.mp3', '30.mp3', '36.mp3', '45.mp3', '56.mp3', '78.mp3', '97.mp3', '108.mp3', '110.mp3'],
\t\tdesert: ['07.mp3', '19.mp3', '20.mp3', '24.mp3', '27.mp3', '46.mp3', '93.mp3'],
\t\tspooky: ['40.mp3', '43.mp3', '48.mp3', '66.mp3', '71.mp3', '84.mp3', '87.mp3'],
\t\tsnow: ['16.mp3', '17.mp3', '18.mp3', '23.mp3', '70.mp3', '74.mp3', '79.mp3'],
\t\toriental: ['09.mp3', '54.mp3', '64.mp3', '65.mp3', '68.mp3', '69.mp3', '72.mp3', '73.mp3', '81.mp3', '82.mp3'],
\t\tvolcano: ['03.mp3', '15.mp3', '52.mp3', '107.mp3'],
\t\tancient_tech: ['38.mp3', '51.mp3', '53.mp3', '57.mp3', '59.mp3', '77.mp3', '86.mp3', '89.mp3', '91.mp3', '92.mp3', '104.mp3'],
\t\tbattle_boss: ['03.mp3', '47.mp3', '52.mp3', '55.mp3', '58.mp3', '62.mp3', '95.mp3', '99.mp3'],
\t\ttropical: ['10.mp3', '14.mp3', '49.mp3', '63.mp3', '76.mp3', '106.mp3']
\t};

\tvar BGM_THEME_RULES = [
\t\t{ theme: 'battle_boss', regex: /(^|_)(guild_|gld_|gld2_|pvp_|arena|bossnia|endless|poring_w|force_|te_prt|te_aldeg|_gld|cas\\\\d|g_room|ordeal|prt_are|battle|camp|nguild_|siege|_castle)/i },
\t\t{ theme: 'volcano', regex: /(^|_)(mag_dun|thor_v|thor_camp)/i },
\t\t{ theme: 'snow', regex: /(^|_)(xmas|ice_dun|toy_factory)/i },
\t\t{ theme: 'desert', regex: /(^|_)(moc_fild|moc_pryd|moc_ruins|in_sphinx|morocc|moc_castle|in_moc)/i },
\t\t{ theme: 'spooky', regex: /(^|_)(gl_|glast|niflheim|nif_|abbey|nameless|lhz_dun0[3-4]|monastery|sec_pri)/i },
\t\t{ theme: 'tropical', regex: /(^|_)(comodo|cmd_|jawaii|beach_dun|alb2trea|umbala)/i },
\t\t{ theme: 'oriental', regex: /(^|_)(amatsu|ama_|gonryun|gon_|louyang|lou_|ayothaya|ayo_)/i },
\t\t{ theme: 'ancient_tech', regex: /(^|_)(juperos|jupe_|c_tower|alde_dun|kh_|kiel|tha_t|thana|ra_san|odin_tem|abyss|nyd_dun|yggdrasil|valkyrie|himinn|gefenia)/i },
\t\t{ theme: 'dungeons', regex: /(^|_)(prt_sewb|pay_dun|gef_dun|anthell|treasure|orcsdun|mjo_dun|tur_dun|bra_dun|mosk_dun|ein_dun|dic_dun|man_dun|dew_dun|sewer|cave|dun|izlu2dun|in_orcs)/i },
\t\t{ theme: 'fields', regex: /(^|_)(fild|prt_maze|pay_arche|mjolnir|new_\\\\d|job_|hunter_|knight_|priest_|sword_|wizard_|assassin_|quiz)/i },
\t\t{ theme: 'towns', regex: /(^|_)(prontera|prt_|geffen|gef_|payon|pay_|alberta|alb_|izlude|izl_|aldebaran|alde|yuno|lutie|einbroch|einbech|ein_|lighthalzen|lhz_|hugel|hu_|rachel|ra_|veins|ve_|moscovia|mosk_|brasilis|bra_|splendide|manuk|mid_camp|mora|dewata|malaya|lasagna|alb_ship|sec_in|gef_tower|airplane|monk_in)|_in$|_in\\\\d|in_/i }
\t];

\tvar BGM_TRACK_TO_THEME = null;
\tfunction getThematicMapBgm(mapName, defaultMp3) {
\t\tif (!BGM_TRACK_TO_THEME) {
\t\t\tBGM_TRACK_TO_THEME = {};
\t\t\tfor (var k in BGM_THEMES) {
\t\t\t\tif (BGM_THEMES.hasOwnProperty(k)) {
\t\t\t\t\tvar arr = BGM_THEMES[k];
\t\t\t\t\tfor (var i = 0; i < arr.length; i++) {
\t\t\t\t\t\tif (!BGM_TRACK_TO_THEME[arr[i]]) {
\t\t\t\t\t\t\tBGM_TRACK_TO_THEME[arr[i]] = k;
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}

\t\tvar cleanMap = (mapName || '').replace(/\\.(gat|rsw)$/i, '').toLowerCase();
\t\tvar chosenTheme = null;

\t\tfor (var r = 0; r < BGM_THEME_RULES.length; r++) {
\t\t\tif (BGM_THEME_RULES[r].regex.test(cleanMap)) {
\t\t\t\tchosenTheme = BGM_THEME_RULES[r].theme;
\t\t\t\tbreak;
\t\t\t}
\t\t}

\t\tif (!chosenTheme && defaultMp3) {
\t\t\tvar cleanMp3 = defaultMp3.replace(/^.*[\\\\/]/, '').toLowerCase();
\t\t\tif (cleanMp3 && BGM_TRACK_TO_THEME[cleanMp3]) {
\t\t\t\tchosenTheme = BGM_TRACK_TO_THEME[cleanMp3];
\t\t\t}
\t\t}

\t\tif (!chosenTheme) {
\t\t\tchosenTheme = 'fields';
\t\t}

\t\tvar pool = BGM_THEMES[chosenTheme] || BGM_THEMES.towns;
\t\tvar currentPlaying = (BGM.filename || '').replace(/^.*[\\\\/]/, '').toLowerCase();
\t\tvar candidates = pool.filter(function (t) { return t.toLowerCase() !== currentPlaying; });
\t\tif (!candidates.length) {
\t\t\tcandidates = pool;
\t\t}

\t\tvar selected = candidates[Math.floor(Math.random() * candidates.length)];
\t\tconsole.log('[BGM] Thematic Randomizer: Map="' + mapName + '" -> Theme="' + chosenTheme + '" -> Track="' + selected + '" (Default: ' + (defaultMp3 || 'none') + ')');
\t\treturn selected;
\t}

\t/**
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

\t\t// Play BGM (Thematic Randomization)
\t\tvar isSameMap = (this._currentBgmMap === this.currentMap);
\t\tthis._currentBgmMap = this.currentMap;

\t\tif (!isSameMap || !BGM.audio || BGM.audio.paused) {
\t\t\tvar selectedBgm = getThematicMapBgm(this.currentMap, mapInfo && mapInfo.mp3);
\t\t\tBGM.play(selectedBgm);
\t\t}`;

for (const [oldStr, newStr] of [
	[targetBgmMap.replace(/\n/g, '\r\n'), replaceBgmMap.replace(/\n/g, '\r\n')],
	[targetBgmMap, replaceBgmMap]
]) {
	if (content.includes(oldStr)) {
		content = content.replace(oldStr, newStr);
		patches++;
		console.log('✓ Patch 20 (Thematic Map BGM Groups & Randomization System) applied');
		break;
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

console.log(`Done. Total patches applied: ${patches}`);

