'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');
const { classify, loadPolicy } = require('../check_badword.cjs');
const root = path.resolve(__dirname, '..');
const commonDirectory = path.dirname(require.resolve('@koralabs/kora-labs-common/package.json'));
const policy = loadPolicy(commonDirectory);
fs.mkdirSync(path.join(root, 'tmp'), { recursive: true });
const evidence = fs.mkdtempSync(path.join(root, 'tmp', 'policy-test-'));

// Invariant: classification uses canonical composition/obfuscation policy.
// Failure: the original partial algorithm falsely allows all four examples.
// Negative control: the retained original offline probe fails these expectations.
test('canonical primary rejects four original false-safe candidates', async () => {
    const reasons = {
        's.h.i.t': "Protected word match (with stripped characters) on 'shit'",
        punchbabies: 'Hatespeech match found for baby,punch',
        pu55y: "Number replacement match on 'pussy'",
        tinypreteenpp: 'Suggestive language match found for preteen,tiny,pp'
    };
    for (const [handle, reason] of Object.entries(reasons)) {
        assert.deepEqual(await classify(handle, policy), { handle, status: 'FLAGGED', reason });
    }
});

// Invariant: positive context remains allowed; malformed candidates are distinct.
// Failure: a blanket target blacklist blocks safe positive phrases or accepts @.
// Negative control: forcing every result FLAGGED breaks safe output assertions;
// removing the format guard makes malformed candidates lack INVALID status.
test('safe, normalized, numeric, length and invalid candidates', async () => {
    for (const handle of ['ilovebabies', 'i.love.life', ' I.LOVE.LIFE ', '123', 'a'.repeat(15)]) {
        assert.deepEqual(await classify(handle, policy), { handle, status: 'OK', reason: 'Policy allows candidate' });
    }
    for (const handle of ['', 'bad@name', 'a'.repeat(16), 'café', 'K']) {
        assert.deepEqual(await classify(handle, policy), { handle, status: 'INVALID', reason: '1-15 chars, only a-z0-9_.-' });
    }
});

// Invariant: both entry points report real classifications to the user offline.
// Failure: Python loses arguments/status, CLI drops rows, or claims mint availability.
// Negative control: restore original Python script; it cannot satisfy this exact
// --common-package invocation or canonical FLAGGED rows (retained old probe).
for (const runtime of ['node', 'python3']) {
    test(`${runtime} CLI journey: UTF-8 file to visible policy table`, () => {
        const input = path.join(evidence, `${runtime}-handles.txt`);
        fs.writeFileSync(input, 's.h.i.t\r\npunchbabies\npu55y\ntinypreteenpp\nilovebabies\nI.LOVE.LIFE\n123\nbad@name\n\n');
        const result = spawnSync(runtime, [path.join(root, runtime === 'node' ? 'check_badword.cjs' : 'check_badword.py'), input, '--common-package', commonDirectory], { encoding: 'utf8' });
        assert.equal(result.status, 0, result.stderr);
        const rows = result.stdout.trim().split('\n');
        assert.equal(rows.length, 10);
        assert.equal(rows[0], 'Offline policy: @koralabs/kora-labs-common@6.9.3; OK does not mean unminted or reservable.');
        assert.equal(rows[1], 'HANDLE\tSTATUS\tREASON');
        assert.deepEqual(rows.slice(2).map(row => row.split('\t').slice(0, 2)), [
            ['s.h.i.t', 'FLAGGED'], ['punchbabies', 'FLAGGED'], ['pu55y', 'FLAGGED'], ['tinypreteenpp', 'FLAGGED'],
            ['ilovebabies', 'OK'], ['I.LOVE.LIFE', 'OK'], ['123', 'OK'], ['bad@name', 'INVALID']
        ]);
    });
}

// Invariant: only original ASCII candidates may be normalized; every output
// field is a JSON-string interior so invalid inputs cannot corrupt the TSV.
// Failure: Kelvin sign becomes valid 'k', or tabs/control/backslashes alter rows.
// Negative control: the actual252 CLI fails these same subprocess assertions;
// restoring lowercase-before-validation or raw interpolation breaks them again.
for (const runtime of ['node', 'python3']) {
    test(`${runtime} CLI preserves ASCII boundary and lossless three-field rows`, () => {
        const candidates = ['K', 'I.LOVE.LIFE', 'bad\tname', 'bad\\name', 'bad"name', 'bad\u0000name', 'bad\u001bname', 'bad\rname'];
        const input = path.join(evidence, `${runtime}-encoding.txt`);
        fs.writeFileSync(input, candidates.join('\n') + '\n');
        const result = spawnSync(runtime, [path.join(root, runtime === 'node' ? 'check_badword.cjs' : 'check_badword.py'), input, '--common-package', commonDirectory], { encoding: 'utf8' });
        assert.equal(result.status, 0, result.stderr);
        const rows = result.stdout.trimEnd().split('\n').slice(2);
        assert.equal(rows.length, candidates.length);
        const decoded = rows.map(row => {
            const fields = row.split('\t');
            assert.equal(fields.length, 3, `corrupt row: ${JSON.stringify(row)}`);
            return fields.map(field => JSON.parse(`"${field}"`));
        });
        assert.deepEqual(decoded.map(row => row[0]), candidates);
        assert.deepEqual(decoded.map(row => row[1]), ['INVALID', 'OK', 'INVALID', 'INVALID', 'INVALID', 'INVALID', 'INVALID', 'INVALID']);
        assert.equal(decoded[1][2], 'Policy allows candidate');
        for (const row of decoded.filter(row => row[1] === 'INVALID')) {
            assert.equal(row[2], '1-15 chars, only a-z0-9_.-');
        }
    });
}

// Invariant: dependency/input errors fail visibly instead of returning safe rows.
// Failure: silent fallback, ignored version mismatch, or broken Python exit code.
// Negative control: removing version verification makes assert.throws fail;
// swallowing child errors makes the nonzero status assertions fail.
test('missing file, unknown option, wrong version and dependency errors', () => {
    const wrong = path.join(evidence, 'wrong-package');
    fs.mkdirSync(wrong);
    fs.writeFileSync(path.join(wrong, 'package.json'), JSON.stringify({ name: '@koralabs/kora-labs-common', version: '6.9.2' }));
    assert.throws(() => loadPolicy(wrong), /must be @koralabs\/kora-labs-common@6.9.3/);
    const input = path.join(evidence, 'empty.txt');
    fs.writeFileSync(input, '\n');
    for (const [args, message] of [
        [[path.join(evidence, 'missing.txt')], /ENOENT/],
        [[input, '--unknown'], /Unknown option/],
        [[input, '--common-package', wrong], /must be/],
        [[input, '--common-package', path.join(evidence, 'absent')], /ENOENT/]
    ]) {
        const result = spawnSync('python3', [path.join(root, 'check_badword.py'), ...args], { encoding: 'utf8' });
        assert.equal(result.status, 1);
        assert.match(result.stderr, message);
        assert.equal(result.stdout, '');
    }
});

// Invariant: Python reports a missing Node runtime and fails instead of crashing.
// Failure: startup failure disappears or is incorrectly returned as success.
// Negative control: remove the launcher OSError handler and the diagnostic fails.
test('Python launcher reports missing Node runtime', () => {
    const python = spawnSync('python3', ['-c', 'import sys; print(sys.executable)'], { encoding: 'utf8' });
    assert.equal(python.status, 0, python.stderr);
    const result = spawnSync(python.stdout.trim(), [path.join(root, 'check_badword.py'), '--help'], {
        encoding: 'utf8', env: { ...process.env, PATH: evidence }
    });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Cannot start Node.js policy checker:.*node/);
    assert.equal(result.stdout, '');
});

// Invariant: an empty candidate list produces metadata/header only, not a row.
// Failure: treating blank lines as invalid candidates or inventing availability.
// Negative control: remove blank-line filtering and the line-count assertion fails.
test('empty file succeeds with no candidate rows', () => {
    const input = path.join(evidence, 'blank.txt');
    fs.writeFileSync(input, '\n\r\n');
    const result = spawnSync('node', [path.join(root, 'check_badword.cjs'), input, '--common-package', commonDirectory], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout.trim().split('\n').length, 2);
});
