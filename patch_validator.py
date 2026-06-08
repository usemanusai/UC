with open('validator_pro_v2.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith('<<<<<<< HEAD'):
        skip = True
        continue
    elif line.startswith('======='):
        if skip:
            skip = False
            continue
    elif line.startswith('>>>>>>> origin/testing-improvement-discovery-bridge-12377658825604851510'):
        continue

    if not skip:
        new_lines.append(line)

with open('validator_pro_v2.py', 'w') as f:
    f.writelines(new_lines)
