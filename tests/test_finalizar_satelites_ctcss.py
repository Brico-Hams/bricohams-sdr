import ast
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
script = (root / "tools" / "finalizar-satelites-ctcss.sh").read_text(encoding="utf-8")
blocks = script.split("<<'PY'\n")[1:]
assert len(blocks) == 2
assert 'if command -v node ' in script
assert 'elif command -v nodejs ' in script
assert 'falta validar JavaScript en el navegador' in script
patterns = []
for block in blocks:
    tree = ast.parse(block.split("\nPY\n", 1)[0])
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "option" for t in statement.targets):
                patterns.append(ast.literal_eval(statement.value))
assert len(patterns) == 2 and patterns[0] == patterns[1]
for value in ["true", "false", "'yes' === 'yes'", "'no' === 'yes'"]:
    source = (
        "    tone_detector: " + value + ", // external\n"
        "const external = { tone_detector: window.ea5hkx_config.tone_detector };\n"
        "const native = { ctcss: true };\n"
    )
    result, count = re.subn(patterns[0], r"\g<1>false", source)
    assert count == 1
    assert result == source.replace("tone_detector: " + value + ",", "tone_detector: false,", 1)
    assert re.sub(patterns[0], r"\g<1>false", result) == result
for value in ["window.other", "'yes'", "true || other"]:
    assert not re.search(patterns[0], "    tone_detector: " + value + ",")
print("OK: opcion CTCSS generada, booleanos e idempotencia; control integrado intacto")
