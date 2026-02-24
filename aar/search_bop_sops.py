import os
import fnmatch
import shutil
from pathlib import Path

search_root = r"C:/Users/Mizzi/APEX_NEXUS_SYSTEM"
patterns = ["*BOP*", "*SOP*"]
matches = []

for root, dirs, files in os.walk(search_root):
    for pattern in patterns:
        for filename in fnmatch.filter(files, pattern):
            full_path = os.path.join(root, filename)
            if full_path not in matches:
                matches.append(full_path)

output_dir = Path(r"C:/Users/Mizzi/APEX_NEXUS_SYSTEM/04_PROJECTS/DIDGERI_BOOM/aar/BOP_SOPs")
output_dir.mkdir(parents=True, exist_ok=True)

index_path = output_dir / "README.md"
with open(index_path, "w", encoding="utf-8") as idx:
    idx.write("# BOP SOPs Index\n\n")
    if not matches:
        idx.write("No BOP or SOP files found in the search path.\n")
    for file_path in matches:
        dest = output_dir / Path(file_path).name
        try:
            shutil.copy2(file_path, dest)
            idx.write(f"- [{Path(file_path).name}]({dest})\n")
        except Exception as e:
            idx.write(f"- Failed to copy {file_path}: {e}\n")

print(f"Found {len(matches)} files. Index written to {index_path}")
