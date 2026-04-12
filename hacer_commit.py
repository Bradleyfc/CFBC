import subprocess
import os

env = os.environ.copy()
env['GIT_PAGER'] = 'cat'
env['PAGER'] = 'cat'
env['GIT_TERMINAL_PROMPT'] = '0'

# git add -A
r1 = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True, env=env)
print('ADD stdout:', r1.stdout)
print('ADD stderr:', r1.stderr)

# git commit
r2 = subprocess.run(
    ['git', 'commit', '-m', 'Merge subir-descargar-documentos into main'],
    capture_output=True, text=True, env=env
)
print('COMMIT stdout:', r2.stdout)
print('COMMIT stderr:', r2.stderr)
