import re

def change_variable_to_asn_style(variable):
    return re.sub("_", "-", variable)


def change_variable_to_python_style(variable):
    return re.sub("-", "_", variable)


def get_supported_messages_in_modules(file):
    supported_msgs_in_modules = {}
    lines = []
    with open(file, "r") as fd:
        for line in fd.readlines():
            if len(line.strip()) == 0: continue
            lines.append(line)
    for module in re.findall(r"[\w\_]+", lines[-1])[1:]:
        supported_msgs_in_modules[change_variable_to_asn_style(module)] = []
    
    patterns = ((r"class\s([\w\_]+)\:", "class"),
                (r"([\w\_]+)\s*=\s*SEQ\(name=\'\S+\',\smode=MODE_TYPE\)", "sequence"))
    current_module = ''
    for line in lines:
        for pattern in patterns:
            matched = re.match(pattern[0], line.strip())
            if matched:
                if pattern[1] == 'class':
                    current_module = change_variable_to_asn_style(matched.group(1))
                elif pattern[1] == 'sequence':
                    supported_msgs_in_modules[current_module].append(change_variable_to_asn_style(matched.group(1)))
                else: pass
                break
    return supported_msgs_in_modules


def reformat_asn_line(line):
    words = re.findall(r"\([^\(\)]*\(.*?\)[^\(\)]*\)|\(.*?\)|[\w\-]+|[\:\=]+|\{|\}|,", line)
    new_lines = []
    indent = 0
    new_line = ' ' * indent
    for i in range(len(words)):
        if words[i] == "{":
            new_line += words[i]
            indent += 4
            new_lines.append(new_line)
            new_line = ' ' * indent
        elif words[i] == "}":
            indent -= 4
            if i > 0 and words[i-1] == "{":
                new_line = new_lines[-1]
                new_line += (words[i] + " ")
                del new_lines[-1]
            else:
                new_lines.append(new_line)
                new_line = (' ' * indent) + words[i] + " "
        else:
            if i > 0 and words[i-1] == ",":
                new_lines.append(new_line)
                new_line = (' ' * indent) + words[i] + " "
            else:
                new_line += (words[i] + " ")
    if new_line.strip() != '': new_lines.append(new_line)
    return "\n".join(new_lines)
