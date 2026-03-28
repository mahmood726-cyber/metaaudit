import re, os

content = open(r'C:\MetaAudit\dashboard\webr-verify.html', encoding='utf-8').read()

# Remove <script>...</script> blocks for div counting
no_script = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
open_divs = len(re.findall(r'<div[\s>]', no_script))
close_divs = len(re.findall(r'</div>', no_script))
print(f'Div balance (excl. JS): open={open_divs}, close={close_divs}, balanced={open_divs==close_divs}')

# Check for literal </script> inside <script> blocks
script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, flags=re.DOTALL)
for i, block in enumerate(script_blocks):
    # Look for </script> that is NOT part of a string escape pattern
    hits = re.findall(r'</script>', block)
    print(f'Script block {i}: literal </script> occurrences = {len(hits)}')

# File stats
size = os.path.getsize(r'C:\MetaAudit\dashboard\webr-verify.html')
print(f'File size: {size:,} bytes ({size/1024:.1f} KB)')
print(f'Line count: {content.count(chr(10))+1}')

# Check type="module" on script tag
module_scripts = re.findall(r'<script[^>]*type="module"[^>]*>', content)
print(f'ES module script tags: {len(module_scripts)}')

# Check WebR CDN import
has_webr = 'webr.r-wasm.org/latest/webr.mjs' in content
print(f'WebR CDN import present: {has_webr}')

# Check metafor install
has_install = 'installPackages' in content and 'metafor' in content
print(f'metafor installPackages call present: {has_install}')
