import re
from collections import namedtuple
from asn1codec.utils import reformat_asn_line


CodeBlock = namedtuple("CodeBlock", ["name", "type", "definition"])   ## type: choice, set, sequence, sequence_of, set_of, other

class AsnCodeMgmt(object):
    def __init__(self, data):
        self.lines = data.split('\n')
        self.code_blocks = {}
        self._store_code_blocks()

    def _parse_code_block(self, line):
        patterns = [(r"(\S+)\s*::=\s*SEQUENCE.+OF.*", "sequence_of"),
                    (r"(\S+)\s*::=\s*SET.+OF.*", "set_of"),
                    (r"(\S+)\s*::=\s*CHOICE.*", "choice"),
                    (r"(\S+)\s*::=\s*SEQUENCE.*", "sequence"),
                    (r"(\S+)\s*::=\s*SET.*", "set")]
        for pattern in patterns:
            matched = re.match(pattern[0], line)
            if matched:
                return matched.group(1).strip(), pattern[1], " ".join(re.findall(r"\S+", line))
        return re.findall(r"[\w\-]+", line)[0].strip(), "other", " ".join(re.findall(r"\S+", line))
    
    def _precheck_line(self, line):
        patterns = [(r"(.*)--.*?--(.*)", "comment_type1"),
                    (r"(.*)--.*", "comment_type2"),
                    (r"--.*", "comment_type3")]
        for pattern in patterns:
            matched = re.match(pattern[0], line.strip())
            if matched:
                if pattern[1] == "comment_type1":
                    return matched.group(1) + matched.group(2)
                if pattern[1] == "comment_type2":
                    return matched.group(1)
                if pattern[1] == "comment_type3":
                    return ""
        return line.strip()
    
    def _store_code_blocks(self):
        code_block = ''
        for _line in self.lines:
            line = self._precheck_line(_line)
            if line == '': continue
            if ("::=" in line) or (line.split(" ")[0] in ["BEGIN", "END", "IMPORTS", "FROM"]):
                if "::=" in code_block:
                    _name, _type, _def = self._parse_code_block(code_block)
                    self.code_blocks[_name] = CodeBlock(_name, _type, _def)
                code_block = line
            else: code_block += (" " + line)
        if "::=" in code_block:
            _name, _type, _def = self._parse_code_block(code_block)
            self.code_blocks[_name] = CodeBlock(_name, _type, _def)

    def get_message_definition(self, msg_name):
        from queue import Queue
        checked_msgs = []        # to avoid get one message definition multi times
        msgs = Queue()
        msgs.put(msg_name)
        res = ''
        while not msgs.empty():
            msg = msgs.get()
            if msg in checked_msgs: continue
            definition = self.code_blocks[msg].definition
            res = res + "\n\n" + reformat_asn_line(definition) if res != '' else reformat_asn_line(definition)
            types = self._get_member_types(msg)
            checked_msgs.append(msg)
            for item in types:
                msgs.put(item)
        return res
    
    def _get_member_types(self, msg_name):
        definition = self.code_blocks[msg_name].definition
        asn_key_words = ["SEQUENCE", "OF", "CHOICE", "BOOLEAN", "BIT", "STRING", "OCTET", "CONTAINING", "NULL", "SIZE",
                         "SET", "INTEGER", "DEFINITIONS", "AUTOMATIC", "TAGS", "BEGIN", "END", "IMPORTS", "FROM"]
        types = []
        for typ in re.findall(r"[\w\-]+", definition)[1:]:
            if (typ not in asn_key_words) and (typ in self.code_blocks):
                types.append(typ)
        return types
