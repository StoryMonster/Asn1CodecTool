from tkinter import filedialog, messagebox
from tkinter import *
from asn1codec.asn1_codec import Asn1Codec
import os


def reformat_payload(payload):
    return "".join(payload.split())


def read_from_file(filename):
    data = ''
    with open(filename, "r") as fd:
        data = fd.read()
    return data


def get_definition_part_position(text, word):
    import re
    lines = text.split("\n")
    x0, y0, x1, y1 = 0, 0, 0, 0
    isDefinitionFound = False
    for i in range(0, len(lines)):
        if isDefinitionFound:
            x1 += 1
            y1 = len(lines[i])
            if lines[i].strip() == "": break
        else:
            if lines[i].find(word) == 0 and re.findall("\S+", lines[i])[0] == word:
                isDefinitionFound = True
                x0, y0 = i+1, 0
                x1, y1 = x0, len(lines[i])
    return x0, y0, x1, y1


def get_cursor_position(widget):
    infors = widget.index(INSERT).split(".")
    row, col = int(infors[0]), int(infors[1])
    return row, col


def get_selected_word_in_text_box(widget):
    word = ''
    try: word = widget.selection_get()
    except: pass
    if word.strip() == '': return ''
    return word


class MainWindow(object):
    def __init__(self, window, context):
        self.context = context
        self.window = window
        self.asn_file_name = StringVar()
        self.protocol = StringVar()
        self.protocol.set("per")
        self.code_format = StringVar()
        self.code_format.set("asn1")
        self.input_box, self.output_box, self.msg_info_box = None, None, None
        self.msg_info_menu = None
        self.msg_list_box, self.selected_msg = None, None
        self.codec_engine = None
        self.py_file = os.path.join(os.getcwd(), "output/output.py")
        self.init_client_surface()
        self.deploy_components()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing_window)

    def init_client_surface(self):
        self.window.title('ASN1CODEC')
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        client_width = int(screen_width * 0.7)
        client_heith = int(screen_height*0.8)
        client_x_position = int((screen_width - client_width)/2)
        client_y_position = int((screen_height - client_heith)/2)
        self.window.geometry('{}x{}'.format(client_width, client_heith))
        self.window.geometry('+{}+{}'.format(client_x_position, client_y_position))

    def deploy_components(self):
        head_frame = Frame(self.window)
        head_frame.pack(side=TOP, fill=BOTH, expand=1)
        self._deploy_components_on_head_frame(head_frame)
        body_frame = Frame(self.window)
        body_frame.pack(side=BOTTOM, fill=BOTH, expand=1)
        self._deploy_components_on_body_frame(body_frame)
    
    def on_closing_window(self):
        import json
        with open("config.ini", "w") as fd:
            fd.write(json.dumps(self.context))
        self.window.destroy()

    def on_open_file_clicked(self):
        dir_to_open = self.context["asn1_dir"] if os.path.exists(self.context["asn1_dir"]) else "."
        self.asn_file_name.set(filedialog.askopenfilename(initialdir = dir_to_open, title = "Select file", filetypes=(('asn files', 'asn'),)))
        self.context["asn1_dir"] = os.path.dirname(self.asn_file_name.get())

    def on_compile_clicked(self):
        filename = self.asn_file_name.get()
        if filename == '':
            messagebox.showwarning("warn", "No asn1 file found")
            return
        data = read_from_file(filename)
        self.codec_engine = Asn1Codec(self.py_file, "output.output")
        status, res, msgs = self.codec_engine.compile(data)
        self.output_box.delete(1.0, "end")
        self.output_box.insert("end", res)
        self.msg_list_box.selection_clear(0, END)
        self.selected_msg = None
        if status == True:
            for msg in msgs:
                self.msg_list_box.insert("end", msg)

    def on_encode_clicked(self):
        if self.selected_msg is None:
            messagebox.showwarning("warn", "Choose a message first")
            return
        input_content = self.input_box.get(1.0, "end").strip()
        _, payload = self.codec_engine.encode(self.protocol.get(), self.code_format.get(), self.selected_msg, input_content)
        self.output_box.delete(1.0, "end")
        self.output_box.insert("end", payload)

    def on_decode_clicked(self):
        if self.selected_msg is None:
            messagebox.showwarning("warn", "Choose a message first")
        input_content = reformat_payload(self.input_box.get(1.0, "end"))
        _, decoded = self.codec_engine.decode(self.protocol.get(), self.code_format.get(), self.selected_msg, input_content)
        self.output_box.delete(1.0, "end")
        self.output_box.insert("end", decoded)

    def on_selected_msg_changed(self, event):
        selected_msgs = self.msg_list_box.curselection()
        self.selected_msg = self.msg_list_box.get(selected_msgs[0]) if isinstance(selected_msgs[0], int) else selected_msgs[0]
        definition = self.codec_engine.get_message_definition(self.selected_msg)
        self.msg_info_box.delete(1.0, "end")
        self.msg_info_box.insert("end", definition)
    
    def on_word_selected_in_msg_info_box(self, event):
        self.msg_info_box.tag_remove("SELECT_TEXT", "1.0", END)
        word = get_selected_word_in_text_box(self.msg_info_box)
        if word == "": return
        text = self.msg_info_box.get(1.0, "end").strip()
        x0, y0, x1, y1 = get_definition_part_position(text, word)
        self.msg_info_box.tag_add("SELECT_TEXT", "{}.{}".format(x0, y0) , "{}.{}".format(x1, y1))
    
    def on_new_row_created(self, event):
        row, col = get_cursor_position(self.input_box)
        lines = self.input_box.get(1.0, "end").split('\n')
        first_part, second_part = lines[row-1][:col], lines[row-1][col:]
        string_to_insert = '\n'
        import re
        matched = re.match(r"(\s+)\S*", lines[row-1])
        if matched:
            string_to_insert += matched.group(1)
        self.input_box.insert("%d.%d" % (row, col), string_to_insert)
        self.input_box.see(INSERT)
        return 'break'
    
    def popup_msg_info_box_menu(self, event):
        self.msg_info_menu.post(event.x_root,event.y_root)
    
    def go_to_msg_definition(self):
        word = get_selected_word_in_text_box(self.msg_info_box)
        text = self.msg_info_box.get(1.0, "end")
        x0, y0, x1, y1 = get_definition_part_position(text, word)
        if x0==0 and y0==0: return
        self.msg_info_box.see("%d.%d" % (x0, y0))

    def _deploy_components_on_head_frame(self, frame):
        Button(frame, text='open', command=self.on_open_file_clicked, bd=5).pack(side=LEFT)
        Button(frame, text='compile', command=self.on_compile_clicked, bd=5).pack(side=LEFT)
        Label(frame, textvariable=self.asn_file_name, font=('Arial', 12)).pack(side=LEFT)
        Label(frame, text="StoryMonster  ", font=('', 16)).pack(side=RIGHT)

    def _deploy_components_on_message_list_frame(self, frame):
        listbox_x_scrollar_bar = Scrollbar(frame, orient=HORIZONTAL)
        listbox_x_scrollar_bar.pack(side=BOTTOM, fill=X)
        listbox_y_scrollar_bar = Scrollbar(frame, orient=VERTICAL)
        listbox_y_scrollar_bar.pack(side=RIGHT, fill=Y)
        self.msg_list_box = Listbox(frame, selectmode=SINGLE, exportselection=False, bd=5,
                                    xscrollcommand=listbox_x_scrollar_bar.set, yscrollcommand=listbox_y_scrollar_bar.set)
        self.msg_list_box.pack(side=LEFT, fill=BOTH, expand=1)
        listbox_x_scrollar_bar.config(command=self.msg_list_box.xview)
        listbox_y_scrollar_bar.config(command=self.msg_list_box.yview)
        self.msg_list_box.bind("<<ListboxSelect>>", self.on_selected_msg_changed)
    
    def _deploy_components_on_input_frame(self, frame):
        input_x_scrollar_bar = Scrollbar(frame, orient=HORIZONTAL)
        input_x_scrollar_bar.pack(side=BOTTOM, fill=X)
        input_y_scrollar_bar = Scrollbar(frame, orient=VERTICAL)
        input_y_scrollar_bar.pack(side=RIGHT, fill=Y)
        self.input_box = Text(frame, bd=5, wrap="none", xscrollcommand=input_x_scrollar_bar.set, yscrollcommand=input_y_scrollar_bar.set)
        self.input_box.pack(anchor="center", fill=BOTH, expand=1)
        self.input_box.bind("<Return>", self.on_new_row_created)
        input_x_scrollar_bar.config(command=self.input_box.xview)
        input_y_scrollar_bar.config(command=self.input_box.yview)
    
    def _deploy_components_on_function_frame(self, frame):
        Button(frame, text='encode', command=self.on_encode_clicked).pack(side=LEFT)
        Radiobutton(frame, variable=self.protocol, value="per", text="per").pack(side=LEFT)
        Radiobutton(frame, variable=self.protocol, value="uper", text="uper").pack(side=LEFT)
        Radiobutton(frame, variable=self.protocol, value="ber", text="ber").pack(side=LEFT)
        Radiobutton(frame, variable=self.protocol, value="cer", text="cer").pack(side=LEFT)
        Radiobutton(frame, variable=self.protocol, value="der", text="der").pack(side=LEFT)
        Button(frame, text='decode', command=self.on_decode_clicked).pack(side=LEFT)
        Radiobutton(frame, variable=self.code_format, value="asn1", text="asn1").pack(side=RIGHT)
        Radiobutton(frame, variable=self.code_format, value="json", text="json").pack(side=RIGHT)

    def _deploy_components_on_output_frame(self, frame):
        output_x_scrollar_bar = Scrollbar(frame, orient=HORIZONTAL)
        output_x_scrollar_bar.pack(side=BOTTOM, fill=X)
        output_y_scrollar_bar = Scrollbar(frame, orient=VERTICAL)
        output_y_scrollar_bar.pack(side=RIGHT, fill=Y)
        self.output_box = Text(frame, bd=5, wrap="none", xscrollcommand=output_x_scrollar_bar.set, yscrollcommand=output_y_scrollar_bar.set)
        self.output_box.pack(anchor="center", fill=BOTH, expand=1)
        output_x_scrollar_bar.config(command=self.output_box.xview)
        output_y_scrollar_bar.config(command=self.output_box.yview)

    def _deploy_components_on_codec_frame(self, frame):
        input_frame = Frame(frame)
        input_frame.pack(side=TOP, fill=BOTH, expand=1)
        self._deploy_components_on_input_frame(input_frame)
        function_frame = Frame(frame)
        function_frame.pack(anchor="center", fill=BOTH, expand=1)
        self._deploy_components_on_function_frame(function_frame)
        output_frame = Frame(frame)
        output_frame.pack(side=BOTTOM, fill=BOTH, expand=1)
        self._deploy_components_on_output_frame(output_frame)

    def _deploy_menu_on_msg_info_box(self, widget):
        self.msg_info_menu = Menu(widget, tearoff=0)
        self.msg_info_menu.add_command(label="go to definition", command=self.go_to_msg_definition)

    def _deploy_components_on_msg_info_frame(self, frame):
        msg_info_x_scrollar_bar = Scrollbar(frame, orient=HORIZONTAL)
        msg_info_x_scrollar_bar.pack(side=BOTTOM, fill=X)
        msg_info_y_scrollar_bar = Scrollbar(frame, orient=VERTICAL)
        msg_info_y_scrollar_bar.pack(side=RIGHT, fill=Y)
        self.msg_info_box = Text(frame, bd=5, wrap="none", xscrollcommand=msg_info_x_scrollar_bar.set, yscrollcommand=msg_info_y_scrollar_bar.set)
        self.msg_info_box.pack(side=RIGHT, fill=BOTH, expand=1)
        msg_info_x_scrollar_bar.config(command=self.msg_info_box.xview)
        msg_info_y_scrollar_bar.config(command=self.msg_info_box.yview)
        self.msg_info_box.tag_configure("SELECT_TEXT", background="blue", foreground="yellow")
        self._deploy_menu_on_msg_info_box(self.msg_info_box)
        self.msg_info_box.bind("<Button-3>", self.popup_msg_info_box_menu)
        self.msg_info_box.bind("<ButtonRelease-1>", self.on_word_selected_in_msg_info_box)

    def _deploy_components_on_body_frame(self, frame):
        message_list_frame = Frame(frame)
        message_list_frame.pack(side=LEFT, fill=BOTH, expand=1)
        self._deploy_components_on_message_list_frame(message_list_frame)
        codec_frame = Frame(frame)
        codec_frame.pack(side=RIGHT, fill=BOTH, expand=1)
        self._deploy_components_on_codec_frame(codec_frame)
        msg_info_frame = Frame(frame)
        msg_info_frame.pack(side=LEFT, fill=BOTH, expand=1)
        self._deploy_components_on_msg_info_frame(msg_info_frame)
