"""Bounded SSE framing and JSON string decoding for provisional answer only."""
import json


class SSEFrames:
    def __init__(self,limit=8*1024*1024):
        self.limit=limit
        self.line=[]
        self.data=[]
        self.size=0
        self.after_cr=False

    def feed(self,chunk):
        events=[]
        for char in chunk:
            if self.after_cr:
                self.after_cr=False
                if char=='\n': continue
            if char in '\r\n':
                line=''.join(self.line);self.line=[]
                if char=='\r': self.after_cr=True
                if not line:
                    if self.data: events.append('\n'.join(self.data))
                    self.data=[];self.size=0
                elif not line.startswith(':'):
                    field,_,value=line.partition(':')
                    if value.startswith(' '): value=value[1:]
                    if field=='data': self.data.append(value)
            else:
                self.size+=len(char.encode('utf-8'))
                if self.size>self.limit: raise ValueError('Gateway frame limit.')
                self.line.append(char)
        # Undelimited EOF intentionally emits no event.
        return events


class AnswerJSON:
    def __init__(self):
        self.depth=0
        self.phase='key'
        self.key=None
        self.keys=set()
        self.string=False
        self.kind=None
        self.buffer=[]
        self.escape=False
        self.hex=None
        self.high=None
        self.answer_size=0

    def _character(self,char,output):
        value=ord(char)
        if self.high is not None:
            if not 0xDC00<=value<=0xDFFF: raise ValueError('Unpaired surrogate.')
            char=chr(0x10000+((self.high-0xD800)<<10)+(value-0xDC00));self.high=None
        elif 0xD800<=value<=0xDBFF:
            self.high=value;return
        elif 0xDC00<=value<=0xDFFF: raise ValueError('Unpaired surrogate.')
        if self.kind=='key': self.buffer.append(char)
        elif self.kind=='answer':
            self.answer_size+=1
            if self.answer_size>4000: raise ValueError('Answer limit.')
            output.append(char)

    def feed(self,fragment):
        output=[]
        for char in fragment:
            if self.string:
                if self.hex is not None:
                    if char not in '0123456789abcdefABCDEF': raise ValueError('Unicode escape.')
                    self.hex+=char
                    if len(self.hex)==4:
                        value=chr(int(self.hex,16));self.hex=None
                        self._character(value,output)
                elif self.escape:
                    self.escape=False
                    if char=='u': self.hex=''
                    else:
                        escapes={'"':'"','\\':'\\','/':'/','b':'\b','f':'\f','n':'\n','r':'\r','t':'\t'}
                        if char not in escapes: raise ValueError('JSON escape.')
                        self._character(escapes[char],output)
                elif char=='\\': self.escape=True
                elif char=='"':
                    if self.high is not None: raise ValueError('Unpaired surrogate.')
                    self.string=False
                    if self.kind=='key':
                        self.key=''.join(self.buffer)
                        if self.key in self.keys: raise ValueError('Duplicate JSON key.')
                        self.keys.add(self.key);self.phase='colon'
                    elif self.depth==1: self.phase='comma'
                else:
                    if ord(char)<32: raise ValueError('JSON control.')
                    self._character(char,output)
            elif char=='"':
                self.string=True;self.buffer=[]
                self.kind='key' if self.depth==1 and self.phase=='key' else 'answer' if self.depth==1 and self.phase=='value' and self.key=='answer' else 'other'
            elif char in '{[':
                self.depth+=1
                if self.depth>32: raise ValueError('JSON depth limit.')
                if self.depth==1: self.phase='key'
            elif char in '}]':
                self.depth-=1
                if self.depth<0: raise ValueError('JSON nesting.')
                if self.depth==1: self.phase='comma'
            elif self.depth==1 and char==':': self.phase='value'
            elif self.depth==1 and char==',': self.phase='key'
        return ''.join(output)


def complete_json(raw):
    def object_pairs(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('Duplicate JSON key.')
            result[key]=value
        return result
    def invalid_constant(value): raise ValueError('Non-finite JSON.')
    return json.loads(raw,object_pairs_hook=object_pairs,parse_constant=invalid_constant)


class SegmentAnswerJSON:
    """Emit only complete validated segment groups from the private answer.

    Adjacent text segments are checked together. Trusted calculation segments
    form explicit boundaries and never pass through the free-equation scanner.
    The underlying lexer preserves duplicate-root/escape/surrogate checks.
    """
    def __init__(self, records, *, quantities=None):
        self.lexer=AnswerJSON();self.records=records
        from app.core.chat_expressions import ExpressionRenderer
        self.expressions=ExpressionRenderer(quantities) if quantities is not None else None
        self.segment=None;self.segments=[];self.pending=[]
        self.text='';self.closed=False;self.trailing='';self.rendered_size=0
        self.classified=None
        self.basis=None;self.basis_raw=None;self.array_answer=False;self.deferred=''

    def _flush(self):
        from app.core.chat_segments import render_segment
        if not self.pending:return ''
        result=render_segment({'text':''.join(self.pending)},self.records,self.expressions)
        self.pending=[]
        return result

    def feed(self, fragment):
        from app.core.chat_segments import render_segment,render_classified_answer
        output=[]
        for char in fragment:
            lex=self.lexer
            if not lex.string and lex.depth==1 and lex.phase=='value' and lex.key=='basis' and char=='"':
                self.basis_raw=[]
            if self.basis_raw is not None:
                self.basis_raw.append(char);lex.feed(char)
                if len(self.basis_raw)>128:raise ValueError('Invalid response basis.')
                if not lex.string:
                    from app.core.chat_response_modes import response_prefix
                    self.basis=complete_json(''.join(self.basis_raw));self.basis_raw=None
                    response_prefix(self.basis)
                continue
            if not lex.string and lex.depth==1 and lex.key=='answer' and char=='[':
                self.array_answer=True
            if not lex.string and lex.depth==1 and lex.key=='answer' and char=='{':
                self.classified=[]
            if self.classified is not None:
                self.classified.append(char);lex.feed(char)
                if len(self.classified)>262144:raise ValueError('Response segment limit.')
                if not lex.string and lex.depth==1 and char=='}':
                    answer=complete_json(''.join(self.classified))
                    output.append(render_classified_answer(answer,self.expressions))
                    self.classified=None;self.closed=True
                continue
            opening=(not lex.string and lex.depth==2 and lex.key=='answer' and char=='{')
            closing=(not lex.string and lex.depth==2 and lex.key=='answer' and char==']')
            if opening:self.segment=[]
            if self.segment is not None:self.segment.append(char)
            lex.feed(char)
            if self.segment is not None and len(self.segment)>65536:
                raise ValueError('Response segment limit.')
            if self.segment is not None and not lex.string and lex.depth==2 and char=='}':
                value=complete_json(''.join(self.segment));self.segment=None
                rendered=render_segment(value,self.records,self.expressions)
                self.rendered_size+=len(rendered)
                if self.rendered_size>4000:raise ValueError('Rendered text limit.')
                self.segments.append(value)
                if len(self.segments)>128:raise ValueError('Invalid segment collection.')
                if 'text' in value:self.pending.append(rendered)
                else:output.extend([self._flush(),rendered])
            if closing:
                if not self.segments:raise ValueError('Invalid segment collection.')
                output.append(self._flush());self.closed=True
        # Match the existing public strip_whitespace contract across chunks,
        # retaining internal spaces and withholding only a possible final tail.
        result=self.deferred+''.join(output)
        if self.array_answer and self.basis is None and self.lexer.depth>0:
            self.deferred=result
            return ''
        self.deferred=''
        result=self.trailing+result
        if not self.text:
            result=result.lstrip()
            if result:
                from app.core.chat_response_modes import response_prefix
                result=(response_prefix(self.basis) if self.array_answer else '')+result
        emitted=result.rstrip()
        self.trailing=result[len(emitted):]
        result=emitted;self.text+=result
        if len(self.text)>4000:raise ValueError('Rendered text limit.')
        return result

    def finish(self):
        if not self.closed or self.segment is not None or self.pending or self.classified is not None or self.basis_raw is not None or self.deferred:
            raise ValueError('Incomplete segmented answer.')
        if not self.text:raise ValueError('Empty rendered text.')
        return self.text
