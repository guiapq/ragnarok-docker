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

fs.writeFileSync(onlinePath, content, 'utf8');
console.log(`Done. Total patches applied: ${patches}`);
