import re
import ast
import binascii
from asn1codec.json_formater import format_json
from asn1codec.utils import change_variable_to_python_style, get_supported_messages_in_modules, reformat_asn_line
from asn1codec.asn_code_mgmt import AsnCodeMgmt
from asn1codec.asn_codec_error import AsnCodeError


class Asn1Codec(object):
    def __init__(self, py_file, module):
        """
          py_file: the python file name which should be the output py file of pycrate
          module: the module of py_file, it's a string like "xx.xxxx.xx", which can be recorgnized by __import__
        """
        self.py_file = py_file
        self.msgs_in_modules = {}
        self.asn_mgmt = None
        self.module = module

    def compile(self, data):
        """
          data: the whole asn1 data
        """
        try:
            self.asn_mgmt = AsnCodeMgmt(data)
            ckw = {'autotags': True, 'extimpl': True, 'verifwarn': True}
            from pycrate_asn1c.proc import compile_text, generate_modules, PycrateGenerator
            compile_text(data, **ckw)
            generate_modules(PycrateGenerator, self.py_file)
        except AsnCodeError as e:
            return False, str(e), []
        except Exception as e:
            return False, str(e), []
        self.msgs_in_modules = get_supported_messages_in_modules(self.py_file)
        msgs = []
        for module in self.msgs_in_modules:
            msgs.extend(self.msgs_in_modules[module])
        msgs.sort()
        return True, "Compile Success!", msgs
    
    def encode(self, protocol, format, msg_name, msg_content):
        """
          protocol: to spicify the encode mothod, per/uper/ber/cer/der
          format: to spicify the format of input message content, asn1/json
          msg_name: the name of message to encode
          msg_content: the content of message to encode
        """
        pdu_str = self._get_pdu_str(msg_name)
        if pdu_str is None: return False, "Unknow message!"
        modules = [change_variable_to_python_style(module) for module in self.msgs_in_modules]
        target = __import__(self.module, globals(), locals(), modules)
        pdu = eval("target." + pdu_str)
        try:
            if format == "asn1": pdu.from_asn1(msg_content)
            else:
                msg = ast.literal_eval(msg_content)
                pdu.set_val(msg)
            payload = None
            if protocol == "per":
                payload = pdu.to_aper()
            elif protocol == "uper":
                payload = pdu.to_uper()
            elif protocol == "ber":
                payload = pdu.to_ber()
            elif protocol == "cer":
                payload = pdu.to_cer()
            elif protocol == "der":
                payload = pdu.to_der()
            else:
                return False, "Unkown protocol"
        except Exception as e:
            return False, str(e)
        return True, binascii.hexlify(payload).decode("utf-8")
    
    def decode(self, protocol, format, msg_name, payload):
        """
          protocol: to spicify the decode mothod, per/uper/ber/cer/der
          format: to spicify the format of input message content, asn1/json
          msg_name: the name of message to decode
          msg_content: the content of message to decode
        """
        ## the length of payload must be even, and payload should be hex stream
        pdu_str = self._get_pdu_str(msg_name)
        if pdu_str is None: return False, "Unknow message!"
        modules = [change_variable_to_python_style(module) for module in self.msgs_in_modules]
        target = __import__(self.module, globals(), locals(), modules)
        pdu = eval("target." + pdu_str)
        try:
            if protocol == "per":
                pdu.from_aper(binascii.a2b_hex(payload))
            elif protocol == "uper":
                pdu.from_uper(binascii.a2b_hex(payload))
            elif protocol == "ber":
                pdu.from_ber(binascii.a2b_hex(payload))
            elif protocol == "cer":
                pdu.from_cer(binascii.a2b_hex(payload))
            elif protocol == "der":
                pdu.from_der(binascii.a2b_hex(payload))
            else:
                return False, "Unkown protocol"
        except Exception as e:
            return False, str(e)
        res = pdu.to_asn1() if format == "asn1" else format_json(str(pdu()))
        return True, res
    
    def get_supported_msgs(self):
        supported_msgs = []
        for module in self.msgs_in_modules:
            supported_msgs.extend(self.msgs_in_modules[module])
        supported_msgs.sort()
        return supported_msgs
    
    def get_message_definition(self, msg_name):
        return self.asn_mgmt.get_message_definition(msg_name)
    
    def _get_pdu_str(self, msg_name):
        """
          msg_name: the asn1 format name of msg
        """
        for module in self.msgs_in_modules:
            for msg in self.msgs_in_modules[module]:
                if msg == msg_name:
                    return change_variable_to_python_style(module) + "." + change_variable_to_python_style(msg)
        return None
