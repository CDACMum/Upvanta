// mongosh-like shell used at build time to execute MongoDB examples.
// Queries, updates and aggregations are evaluated by mingo (a JavaScript implementation
// of the MongoDB Query Language); collections live in memory for one example.
// Usage: node mongo_shell.js < {"setup": "...", "code": "..."}   (JSON on stdin)
const path = require('path');
const NM = process.env.MINGO_DIR || path.join(__dirname, 'node_modules');
const req = require('module').createRequire(path.join(NM, '..', 'noop.js'));
const mingo = req('mingo');
req('mingo/init/system');
const { update: applyUpdate } = req('mingo/updater');
const acorn = req('acorn');
const util = require('util');
const vm = require('vm');

// ------------------------------------------------------------------ ids & helpers
let oidCounter = 0;
class ObjectIdT {
  constructor(hex) {
    if (hex) { this.hex = hex; return; }
    oidCounter++;
    const ts = Math.floor(Date.UTC(2026, 9, 13, 9, 0, 0) / 1000) + oidCounter;   // creation second
    this.hex = ts.toString(16).padStart(8, '0') + 'a3f19c2e7b' + (0x4e21a0 + oidCounter).toString(16).padStart(6, '0');
  }
  getTimestamp() { return new Date(parseInt(this.hex.slice(0, 8), 16) * 1000); }
  toString() { return this.hex; }
  [util.inspect.custom]() { return `ObjectId('${this.hex}')`; }
}
const ObjectId = (h) => new ObjectIdT(h);
class Decimal128T {
  constructor(s) { this.s = String(s); }
  toString() { return this.s; }
  valueOf() { return Number(this.s); }
  [util.inspect.custom]() { return `Decimal128('${this.s}')`; }
}
const ISODate = (s) => new Date(s);
const clone = (v) => structuredCloneSafe(v);
function structuredCloneSafe(v) {
  if (v instanceof ObjectIdT || v instanceof Decimal128T) return v;
  if (v instanceof Date) return new Date(v.getTime());
  if (Array.isArray(v)) return v.map(structuredCloneSafe);
  if (v && typeof v === 'object') { const o = {}; for (const k of Object.keys(v)) o[k] = structuredCloneSafe(v[k]); return o; }
  return v;
}
const keyOf = (v) => (v instanceof ObjectIdT ? 'oid:' + v.hex : JSON.stringify(v));

function positional(doc, path, condition) {
  // resolve the positional "$" operator: index of the first array element matched by the query
  const i = path.indexOf('.$');
  if (i < 0 || path[i + 2] === '[') return path;
  const prefix = path.slice(0, i);
  const arr = prefix.split('.').reduce((a, k) => (a == null ? a : a[k]), doc);
  if (!Array.isArray(arr)) return path;
  const sub = {}; let scalar;
  for (const [k, v] of Object.entries(condition || {})) {
    if (k.startsWith(prefix + '.')) sub[k.slice(prefix.length + 1)] = v;
    else if (k === prefix) { if (v && v.$elemMatch) Object.assign(sub, v.$elemMatch); else scalar = v; }
  }
  let idx = -1;
  if (scalar !== undefined) idx = arr.findIndex((e) => new mingo.Query({ v: scalar }, OPTS).test({ v: e }));
  else idx = arr.findIndex((e) => new mingo.Query(sub, OPTS).test(e));
  if (idx < 0) throw new MongoServerError('The positional operator did not find the match needed from the query.', 2);
  return prefix + '.' + idx + path.slice(i + 2);
}
function applyOps(doc, upd, arrayFilters, condition) {
  for (const [op, val] of Object.entries(upd)) {
    if (!op.startsWith('$')) { const e = new Error('Update document requires atomic operators'); e.name = 'MongoInvalidArgumentError'; throw e; }
    const v2 = {};
    for (const [p, x] of Object.entries(val)) v2[positional(doc, p, condition)] = x;
    applyUpdate(doc, { [op]: v2 }, arrayFilters, undefined, { cloneMode: 'none' });
  }
}

class MongoServerError extends Error {
  constructor(msg, code) { super(msg); this.name = 'MongoServerError'; this.code = code; }
}

// ------------------------------------------------------------------ database
const dbs = {};
let currentDb = 'test';
function getDb(name) {
  if (!dbs[name]) dbs[name] = {};
  return dbs[name];
}
const resolver = (name) => (getDb(currentDb)[name] ? getDb(currentDb)[name].docs : []);
function bsonType(v) {
  if (v === null) return 'null';
  if (Array.isArray(v)) return 'array';
  if (v instanceof Date) return 'date';
  if (v instanceof ObjectIdT) return 'objectId';
  if (v instanceof Decimal128T) return 'decimal';
  if (typeof v === 'number') return Number.isInteger(v) ? 'int' : 'double';
  if (typeof v === 'string') return 'string';
  if (typeof v === 'boolean') return 'bool';
  return 'object';
}
function schemaOk(schema, v) {
  if (schema.bsonType) {
    const t = bsonType(v); const want = [].concat(schema.bsonType);
    const ok = want.some((w) => w === t || (w === 'number' && (t === 'int' || t === 'double')) || (w === 'long' && t === 'int') || (w === 'double' && t === 'int') || (w === 'decimal' && (t === 'int' || t === 'double')));
    if (!ok) return false;
  }
  if (schema.enum && !schema.enum.some((e) => JSON.stringify(e) === JSON.stringify(v))) return false;
  if (typeof v === 'number') { if (schema.minimum !== undefined && v < schema.minimum) return false; if (schema.maximum !== undefined && v > schema.maximum) return false; }
  if (typeof v === 'string') { if (schema.pattern && !new RegExp(schema.pattern).test(v)) return false; if (schema.minLength !== undefined && v.length < schema.minLength) return false; }
  if (Array.isArray(v)) { if (schema.minItems !== undefined && v.length < schema.minItems) return false; if (schema.items && !v.every((x) => schemaOk(schema.items, x))) return false; }
  if (v && typeof v === 'object' && !Array.isArray(v) && !(v instanceof Date)) {
    for (const r of schema.required || []) if (!(r in v)) return false;
    for (const [k, sub] of Object.entries(schema.properties || {})) if (k in v && !schemaOk(sub, v[k])) return false;
    if (schema.additionalProperties === false) for (const k of Object.keys(v)) if (!(k in (schema.properties || {}))) return false;
  }
  return true;
}
const OPTS = { collectionResolver: resolver, useStrictMode: true, jsonSchemaValidator: (schema) => (obj) => schemaOk(schema, obj) };

class Cursor {
  constructor(docs) { this._docs = docs; this._sort = null; this._skip = 0; this._limit = 0; }
  sort(s) { this._sort = s; return this; }
  skip(n) { this._skip = n; return this; }
  limit(n) { this._limit = n; return this; }
  pretty() { return this; }
  toArray() {
    let d = this._docs;
    if (this._sort) d = mingo.aggregate(d, [{ $sort: this._sort }], OPTS);
    if (this._skip) d = d.slice(this._skip);
    if (this._limit) d = d.slice(0, this._limit);
    return d;
  }
  count() { return this.toArray().length; }
  forEach(fn) { this.toArray().forEach(fn); }
  map(fn) { return this.toArray().map(fn); }
  hasNext() { return this.toArray().length > 0; }
  explain() { throw new Error('explain() needs a real MongoDB server'); }
}

class Collection {
  constructor(dbName, name) {
    this.dbName = dbName; this.name = name; this.docs = []; this.indexes = [{ v: 2, key: { _id: 1 }, name: '_id_' }];
  }
  get ns() { return `${this.dbName}.${this.name}`; }
  _checkUnique(doc, ignore) {
    for (const ix of this.indexes) {
      if (!(ix.unique || ix.name === '_id_')) continue;
      const fields = Object.keys(ix.key);
      const val = (d) => fields.map((f) => keyOf(f.split('.').reduce((a, k) => (a == null ? a : a[k]), d)));
      const v = val(doc).join('|');
      for (const other of this.docs) {
        if (other === ignore) continue;
        if (val(other).join('|') === v) {
          const dup = {}; fields.forEach((f) => { dup[f] = f.split('.').reduce((a, k) => (a == null ? a : a[k]), doc); });
          throw new MongoServerError(`E11000 duplicate key error collection: ${this.ns} index: ${ix.name} dup key: ${util.inspect(dup)}`, 11000);
        }
      }
    }
  }
  _validate(doc) {
    if (this.validator && !new mingo.Query(this.validator, OPTS).test(doc))
      throw new MongoServerError('Document failed validation', 121);
  }
  _prep(doc) { const d = clone(doc); if (d._id === undefined) { const o = {}; o._id = ObjectId(); Object.assign(o, d); return o; } return d; }
  insertOne(doc) { const d = this._prep(doc); this._validate(d); this._checkUnique(d); this.docs.push(d); return { acknowledged: true, insertedId: d._id }; }
  insertMany(docs, opts = {}) {
    const ids = {};
    docs.forEach((doc, i) => {
      const d = this._prep(doc);
      try { this._validate(d); this._checkUnique(d); }
      catch (e) { if (e.name === 'MongoServerError') e.name = 'MongoBulkWriteError'; throw e; }
      this.docs.push(d); ids[i] = d._id;
    });
    return { acknowledged: true, insertedIds: ids };
  }
  find(filter = {}, projection) {
    const q = new mingo.Query(filter, OPTS);
    let res = q.find(this.docs).all();
    if (projection && Object.keys(projection).length) res = mingo.aggregate(res, [{ $project: projection }], OPTS);
    return new Cursor(res.map(clone));
  }
  findOne(filter = {}, projection) { const r = this.find(filter, projection).limit(1).toArray(); return r.length ? r[0] : null; }
  countDocuments(filter = {}) { return new mingo.Query(filter, OPTS).find(this.docs).all().length; }
  estimatedDocumentCount() { return this.docs.length; }
  distinct(field, filter = {}) {
    const out = []; const seen = new Set();
    for (const d of new mingo.Query(filter, OPTS).find(this.docs).all()) {
      let v = field.split('.').reduce((a, k) => (a == null ? a : a[k]), d);
      for (const x of Array.isArray(v) ? v : [v]) { if (x === undefined) continue; const k = keyOf(x); if (!seen.has(k)) { seen.add(k); out.push(x); } }
    }
    return out.sort((a, b) => (a > b ? 1 : a < b ? -1 : 0));
  }
  _update(filter, upd, opts, many) {
    const q = new mingo.Query(filter, OPTS);
    const matched = this.docs.filter((d) => q.test(d));
    const targets = many ? matched : matched.slice(0, 1);
    let modified = 0;
    for (const d of targets) {
      const before = JSON.stringify(d);
      const copy = clone(d);
      if (Array.isArray(upd)) { const r = mingo.aggregate([copy], upd, OPTS)[0]; Object.keys(copy).forEach((k) => delete copy[k]); Object.assign(copy, r); }
      else applyOps(copy, upd, (opts && opts.arrayFilters) || [], filter);
      if (keyOf(copy._id) !== keyOf(d._id))
        throw new MongoServerError("Performing an update on the path '_id' would modify the immutable field '_id'", 66);
      this._validate(copy); this._checkUnique(copy, d);
      Object.keys(d).forEach((k) => delete d[k]); Object.assign(d, copy);
      if (JSON.stringify(d) !== before) modified++;
    }
    let upsertedId = null;
    if (!matched.length && opts && opts.upsert) {
      const seed = {};
      for (const [k, v] of Object.entries(filter)) if (!k.startsWith('$') && (typeof v !== 'object' || v === null || v instanceof Date)) seed[k] = v;
      const nd = this._prep(seed);
      if (!Array.isArray(upd)) {
        const u = clone(upd); if (u.$setOnInsert) { u.$set = Object.assign({}, u.$set || {}, u.$setOnInsert); delete u.$setOnInsert; }
        applyOps(nd, u, [], {});
      }
      this._checkUnique(nd); this.docs.push(nd); upsertedId = nd._id;
    }
    return { acknowledged: true, insertedId: upsertedId, matchedCount: targets.length, modifiedCount: modified, upsertedCount: upsertedId === null ? 0 : 1 };
  }
  updateOne(f, u, o) { return this._update(f, u, o, false); }
  updateMany(f, u, o) { return this._update(f, u, o, true); }
  replaceOne(filter, doc, opts) {
    const q = new mingo.Query(filter, OPTS); const d = this.docs.find((x) => q.test(x));
    if (!d) {
      if (opts && opts.upsert) { const nd = this._prep(doc); this.docs.push(nd); return { acknowledged: true, insertedId: nd._id, matchedCount: 0, modifiedCount: 0, upsertedCount: 1 }; }
      return { acknowledged: true, insertedId: null, matchedCount: 0, modifiedCount: 0, upsertedCount: 0 };
    }
    const id = d._id; Object.keys(d).forEach((k) => delete d[k]); Object.assign(d, { _id: id }, clone(doc));
    return { acknowledged: true, insertedId: null, matchedCount: 1, modifiedCount: 1, upsertedCount: 0 };
  }
  findOneAndUpdate(filter, upd, opts = {}) {
    const q = new mingo.Query(filter, OPTS);
    let d = this.docs.find((x) => q.test(x));
    if (opts.sort) { const s = mingo.aggregate(this.docs.filter((x) => q.test(x)), [{ $sort: opts.sort }], OPTS)[0]; d = this.docs.find((x) => JSON.stringify(x) === JSON.stringify(s)); }
    if (!d && !opts.upsert) return null;
    const before = d ? clone(d) : null;
    if (d) { applyOps(d, upd, opts.arrayFilters || [], filter); } else { this._update(filter, upd, opts, false); d = this.docs[this.docs.length - 1]; }
    const after = clone(d);
    const out = opts.returnDocument === 'after' ? after : before;
    return opts.projection ? mingo.aggregate([out], [{ $project: opts.projection }], OPTS)[0] : out;
  }
  deleteOne(filter) { const q = new mingo.Query(filter, OPTS); const i = this.docs.findIndex((d) => q.test(d)); if (i >= 0) this.docs.splice(i, 1); return { acknowledged: true, deletedCount: i >= 0 ? 1 : 0 }; }
  deleteMany(filter) { const q = new mingo.Query(filter, OPTS); const n = this.docs.length; this.docs = this.docs.filter((d) => !q.test(d)); return { acknowledged: true, deletedCount: n - this.docs.length }; }
  aggregate(pipeline) {
    const out = pipeline.length && (pipeline[pipeline.length - 1].$out || pipeline[pipeline.length - 1].$merge);
    let p = out ? pipeline.slice(0, -1) : pipeline;
    const res = mingo.aggregate(this.docs.map(clone), p, OPTS);
    if (out) {
      const target = typeof out === 'string' ? out : (out.into || out);
      const c = dbProxy[target]; c.docs = res.map(clone); return undefined;
    }
    return new Cursor(res);
  }
  createIndex(key, opts = {}) {
    const name = opts.name || Object.entries(key).map(([k, v]) => `${k}_${v}`).join('_');
    if (opts.unique) { const tmp = this.indexes; this.indexes = [{ key, name, unique: true }]; try { const seen = this.docs.slice(); this.docs = []; for (const d of seen) { this._checkUnique(d); this.docs.push(d); } } finally { this.indexes = tmp; } }
    if (!this.indexes.find((i) => i.name === name)) {
      const ix = { v: 2, key, name }; if (opts.unique) ix.unique = true;
      if (opts.expireAfterSeconds !== undefined) ix.expireAfterSeconds = opts.expireAfterSeconds;
      if (opts.partialFilterExpression) ix.partialFilterExpression = opts.partialFilterExpression;
      this.indexes.push(ix);
    }
    return name;
  }
  createIndexes(list) { return list.map((k) => this.createIndex(k)); }
  getIndexes() { return this.indexes.map(clone); }
  dropIndex(name) { this.indexes = this.indexes.filter((i) => i.name !== name); return { nIndexesWas: this.indexes.length + 1, ok: 1 }; }
  drop() { delete getDb(this.dbName)[this.name]; return true; }
  bulkWrite(ops) {
    let ins = 0, mat = 0, mod = 0, del = 0, ups = 0;
    for (const op of ops) {
      if (op.insertOne) { this.insertOne(op.insertOne.document); ins++; }
      else if (op.updateOne) { const r = this.updateOne(op.updateOne.filter, op.updateOne.update, op.updateOne); mat += r.matchedCount; mod += r.modifiedCount; ups += r.upsertedCount; }
      else if (op.updateMany) { const r = this.updateMany(op.updateMany.filter, op.updateMany.update, op.updateMany); mat += r.matchedCount; mod += r.modifiedCount; ups += r.upsertedCount; }
      else if (op.deleteOne) { del += this.deleteOne(op.deleteOne.filter).deletedCount; }
      else if (op.deleteMany) { del += this.deleteMany(op.deleteMany.filter).deletedCount; }
    }
    return { acknowledged: true, insertedCount: ins, matchedCount: mat, modifiedCount: mod, deletedCount: del, upsertedCount: ups };
  }
  explain() { throw new Error('explain() needs a real MongoDB server'); }
}

const dbProxy = new Proxy({}, {
  get(_, prop) {
    if (prop === 'getName') return () => currentDb;
    if (prop === 'getCollectionNames') return () => Object.keys(getDb(currentDb)).sort();
    if (prop === 'getSiblingDB') return (n) => { currentDb = n; return dbProxy; };
    if (prop === 'createCollection') return (n, o = {}) => { if (!getDb(currentDb)[n]) getDb(currentDb)[n] = new Collection(currentDb, n); if (o.validator) getDb(currentDb)[n].validator = o.validator; return { ok: 1 }; };
    if (prop === 'runCommand') return (c) => { if (c.collMod) { dbProxy[c.collMod].validator = c.validator; return { ok: 1 }; } return { ok: 1 }; };
    if (prop === 'dropDatabase') return () => { delete dbs[currentDb]; return { ok: 1, dropped: currentDb }; };
    if (prop === 'getCollection') return (n) => dbProxy[n];
    if (typeof prop === 'symbol' || prop === 'inspect' || prop === 'then') return undefined;
    if (prop === 'toString') return () => currentDb;
    const d = getDb(currentDb);
    if (!d[prop]) d[prop] = new Collection(currentDb, prop);
    return d[prop];
  },
});

// ------------------------------------------------------------------ printing
const OUT = [];
const idFirst = (v) => {
  if (Array.isArray(v)) return v.map(idFirst);
  if (v && typeof v === 'object' && !(v instanceof Date) && !(v instanceof ObjectIdT) && !(v instanceof Decimal128T)) {
    const o = {}; if ('_id' in v) o._id = idFirst(v._id);
    for (const k of Object.keys(v)) if (k !== '_id') o[k] = idFirst(v[k]);
    return o;
  }
  return v;
};
const fmt = (v) => {
  if (v instanceof Cursor) v = v.toArray();
  v = idFirst(v);
  if (typeof v === 'string') return v;
  return util.inspect(v, { depth: null, breakLength: 90, compact: 3, maxArrayLength: 200 })
    .replace(/(\d{4}-\d{2}-\d{2}T[\d:.]+Z)/g, (m) => m)
    .replace(/(?<![\w'])(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)(?![\w'])/g, "ISODate('$1')");
};
const print = (...a) => OUT.push(a.map((x) => (typeof x === 'string' ? x : fmt(x))).join(' '));

// ------------------------------------------------------------------ run
function preprocess(src) {
  return src
    .replace(/^\s*use\s+(\w+)\s*;?\s*$/gm, (m, n) => `__use(${JSON.stringify(n)});`)
    .replace(/^\s*show\s+(collections|dbs|databases)\s*;?\s*$/gm, (m, w) => `__show(${JSON.stringify(w)});`);
}
function runScript(src, echo) {
  src = preprocess(src);
  const ast = acorn.parse(src, { ecmaVersion: 2022, allowReturnOutsideFunction: true });
  for (const st of ast.body) {
    const code = src.slice(st.start, st.end);
    try {
      if (st.type === 'ExpressionStatement') {
        const v = vm.runInContext(code, ctx);
        if (echo && v !== undefined && !(st.expression.type === 'CallExpression' && st.expression.callee.name && ['print', 'printjson', '__use', '__show'].includes(st.expression.callee.name)))
          OUT.push(fmt(v));
      } else {
        vm.runInContext(code.replace(/^(const|let)\s/, 'var '), ctx);
      }
    } catch (e) {
      if (!echo) throw e;
      OUT.push(`${e.name}: ${e.message}`);
    }
  }
}
const ctx = vm.createContext({
  db: dbProxy, ObjectId, ISODate, Date, Math, JSON, NumberInt: (x) => x, NumberLong: (x) => x, NumberDecimal: (x) => new Decimal128T(x), Decimal128: (x) => new Decimal128T(x),
  print, printjson: (x) => print(x), console: { log: print },
  __use: (n) => { currentDb = n; if (!__quiet) OUT.push(`switched to db ${n}`); },
  __show: (w) => { OUT.push(w === 'collections' ? Object.keys(getDb(currentDb)).sort().join('\n') : Object.keys(dbs).sort().join('\n')); },
});
let __quiet = false;
let input = '';
process.stdin.on('data', (c) => (input += c));
process.stdin.on('end', () => {
  const req = JSON.parse(input);
  try {
    currentDb = 'cdac';
    __quiet = true; if (req.setup) runScript(req.setup, false); __quiet = false;
    runScript(req.code, true);
    process.stdout.write(JSON.stringify({ output: OUT.join('\n') }));
  } catch (e) {
    process.stdout.write(JSON.stringify({ error: String(e && e.stack || e) }));
  }
});
