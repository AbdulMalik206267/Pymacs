#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright � 2003 Progiciels Bourbeau-Pinard inc.
# Fran�ois Pinard <pinard@iro.umontreal.ca>, 2003-05.

"""\
Traitements Babyl ou mbox fr�quents: partie mise en commun.
"""

class Error(Exception): pass

def folder(file_name, strip201=False):
    import os
    if not os.path.isfile(file_name):
        raise Error, "%s: File not found." % file_name
    buffer = file(file_name).read()
    if strip201:
        count = buffer.count('\201')
        if count > 0:
            buffer = buffer.replace('\201', '')
    if buffer.startswith('BABYL OPTIONS:'):
        folder = Babyl(file_name, buffer)
    elif buffer.startswith('From '):
        folder = Mbox(file_name, buffer)
    else:
        raise Error, "%s: Unknown format." % file_name
    if strip201:
        folder.count201 = count
        if count > 0:
            folder.modified = True
    return folder

class Folder:
    def __init__(self, file_name, buffer=None):
        import os
        self.file_name = file_name
        if buffer is None:
            if os.path.exists(file_name):
                self.error("File already exists.")
            self.file_size = None
            self.data = []
            self.deleted = []
        else:
            self.file_size = os.path.getsize(file_name)
            self.create_data(buffer)
            self.deleted = [False] * len(self.data)
        self.modified = False

    def rescan(self):
        import os
        try:
            size = os.path.getsize(self.file_name)
        except IOError:
            if self.file_size is None:
                return
            self.error("Oops!  File vanished.")
        if size < self.file_size:
            self.error("Oops!  File shrunk.")
        if size > self.file_size:
            input = file(self.file_name)
            input.seek(self.file_size)
            self.file_size = size
            self.extend_data(input.read())
            self.deleted += [False] * (len(self.data) - len(self.deleted))

    def __len__(self):
        return len(self.data)

    def mark_deleted(self, index):
        self.deleted[index] = True
        self.modified = True

    def chars_lines(self, index):
        (data, head_being, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        return body_end - body_begin, data.count('\n', body_begin, body_end)

    def close(self, backup=None):
        if self.modified:
            import os
            if self.file_size is not None:
                if os.path.getsize(self.file_name) != self.file_size:
                    self.error("Oops!  File changed!")
                if backup is None:
                    backup = self.file_name + '~'
                if os.path.exists(backup):
                    os.remove(backup)
                os.rename(self.file_name, backup)
            write = None
            for counter in range(len(self.data)):
                if not self.deleted[counter]:
                    if write is None:
                        write = file(self.file_name, 'w').write
                        self.write_file_prefix(write)
                    self.write_indexed_message(counter, write)
            if write is not None:
                self.write_file_suffix(write)

    def error(self, message, index=None):
        if index is None:
            raise Error, '%s: %s' % (self.file_name, message)
        raise Error, '%s:%s: %s' % (self.file_name, index+1, message)

class Babyl(Folder):
    prefix = """\
BABYL OPTIONS: -*- rmail -*-
Version: 5
Labels:
Note:   This is the header of an rmail file.
Note:   If you are seeing it in rmail,
Note:    it means the file has no messages in it.
\37\
"""

    def create_data(self, buffer):
        self.data = buffer.split('\37\f\n')
        if self.data[0].startswith('BABYL OPTIONS:'):
            self.prefix = self.data.pop(0)
        else:
            self.error("Not starting like a Babyl file.")
        if self.data and self.data[-1].endswith('\37'):
            self.data[-1] = self.data[-1][:-1]
        else:
            self.error("Not ending like a Babyl file.")

    def extend_data(self, buffer):
        data = buffer.split('\37\f\n')
        if data[0].startswith('\f\n'):
            data[0] = date[0][2:]
        else:
            self.error("Not starting like a Babyl article.", len(self.data))
        if data[-1].endswith('\37'):
            data[-1] = data[-1][:-1]
        else:
            self.error("Not ending like a Babyl article.",
                       len(self.data) + len(data) - 1)
        self.data += data

    def append(self, text):
        self.data.append(text)
        self.deleted.append(False)
        self.modified = True

    def __getitem__(self, index):
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        return ('%s\n%s' % (data[head_begin:head_end],
                            data[body_begin:body_end]))

    def __setitem__(self, index, text):
        if text != self[index]:
            self.data[index] = ('0, unseen,,\n'
                                '*** EOOH ***\n'
                                + text)
            self.modified = True

    def message_headers(self, index):
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        from email import message_from_string
        from email.Errors import MessageError
        try:
            return message_from_string(data[head_begin:head_end])
        except MessageError, diagnostic:
            self.error(diagnostic, index)

    def write_file_prefix(self, write):
        write(self.prefix)

    def write_file_suffix(self, write):
        write('\37')

    def write_indexed_message(self, index, write):
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        head = data[head_begin:head_end]
        body = data[body_begin:body_end]
        write('\37\f\n'
              '0, unseen,,\n'
              '*** EOOH ***\n')
        write(head)
        write('\n')
        write(body)

    def find_head_body(self, index):
        # Returns (DATA, HEAD_BEGIN, HEAD_END, BODY_BEGIN, BODY_END), the
        # first being a string, all others being positions in that string.
        eooh_string = '\n*** EOOH ***\n'
        data = self.data[index]
        eooh = data.find(eooh_string)
        if eooh < 0:
            self.error("No EOOH within Babyl article.", index)
        double_newline = data.find('\n\n', eooh)
        if double_newline < 0:
            self.error("Unterminated head.", index)
        body_begin = double_newline + 2
        body_end = len(data)
        if data.startswith('0'):
            head_begin = eooh + len(eooh_string)
            head_end = double_newline + 1
        elif data.startswith('1'):
            newline = data.find('\n', 0, eooh)
            if newline < 0:
                self.error("Invalid Babyl article.", index)
            head_begin = newline + 1
            head_end = eooh
        else:
            self.error("Invalid Babyl flag.", index)
        return data, head_begin, head_end, body_begin, body_end

class Mbox(Folder):
    def __init__(self, *arguments):
        self.envelope = []
        Folder.__init__(self, *arguments)

    def create_data(self, buffer):
        self.data = []
        self.extend_data(buffer)

    def extend_data(self, buffer):
        data = []
        envelope = []
        start = 0
        while start < len(buffer):
            end = buffer.find('\n\nFrom ', start)
            if end < 0:
                end = len(buffer)
            newline = buffer.find('\n', start, end)
            if newline < 0:
                self.error("Unterminated envelope.",
                           len(self.data) + len(data))
            double_newline = buffer.find('\n\n', newline+1, end)
            if double_newline < 0:
                head = buffer[newline+1:end]
                if not head.endswith('\n'):
                    head += '\n'
                body = ''
            else:
                head = buffer[newline+1:double_newline+1]
                body = buffer[double_newline+2:end]
                if body.endswith('\n\n'):
                    body = body.rstrip() + '\n'
            data.append('%s\n%s' % (head, body.replace('\n>From', '\nFrom')))
            envelope.append(buffer[start+5:newline].strip())
            start = end + 2
        self.data += data
        self.envelope += envelope

    def append(self, text):
        self.data.append(text)
        import time
        self.envelope.append('Local.folder %s' % time.ctime(time.time()))
        self.deleted.append(False)
        self.modified = True

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, index, text):
        if text != self[index]:
            self.data[index] = text
            self.modified = True

    def message_headers(self, index):
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        head = data[head_begin:head_end]
        from email import message_from_string
        from email.Errors import MessageError
        try:
            return message_from_string(head)
        except MessageError, diagnostic:
            self.error(diagnostic, index)

    def write_file_prefix(self, write):
        pass

    def write_file_suffix(self, write):
        pass

    def write_indexed_message(self, index, write):
        write('From %s\n' % self.envelope[index])
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        head = data[head_begin:head_end]
        body = data[body_begin:body_end]
        write(head)
        write('\n')
        if body.startswith('From'):
            write('>')
        write(body.replace('\nFrom', '\n>From'))
        if not body.endswith('\n'):
            write('\n')
        write('\n')

    def find_head_body(self, index):
        # Returns (DATA, HEAD_BEGIN, HEAD_END, BODY_BEGIN, BODY_END), the
        # first being a string, all others being positions in that string.
        data = self.data[index]
        double_newline = data.find('\n\n')
        if double_newline < 0:
            return data, 0, len(data), len(data), len(data)
        return data, 0, double_newline + 1, double_newline + 2, len(data)
