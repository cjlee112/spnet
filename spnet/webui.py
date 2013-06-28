
class Table(list):
    def __init__(self, caption=None, headings=None):
        list.__init__(self)
        self.caption = caption
        self.headings = headings

    def __str__(self):
        s = '<TABLE BORDER=1>\n'
        if self.caption:
            s += '\t<CAPTION>%s</CAPTION>\n' % self.caption
        if self.headings:
            s += '\t<TR>'
            for head in self.headings:
                s += '<TH>%s</TH>' % head
            s += '\t</TR>\n'
        for row in self:
            s += '\t<TR>'
            for col in row:
                s += '\t\t<TD>%s</TD>\n' % col
            s += '\t</TR>\n'
        s += '</TABLE>\n'
        return s
        
class Data(list):
    def __str__(self):
        try:
            s='<%s>' % self.format
        except AttributeError:
            s=''
        for v in self:
            s+=str(v)
        try:
            s+='</%s>' % self.format
        except AttributeError:
            pass
        return s

class Body(Data):
    format='BODY'
class Head(Data):
    format='HEAD'
class Title(Data):
    format='TITLE'
class Document(Data):
    format='HTML'
    def __init__(self,title):
        head=Head([Title([title])])
        try:
            head.append(self._defaultHeader)
        except AttributeError:
            pass
        list.__init__(self,[head,Body()])
        self.head=head
        self.methods={}
        self.n = 0
    def append(self,x):
        'just append to body'
        self[-1].append(x)
    def __call__(self,**kwargs):
        return str(self)
    def add_text(self,text,format=None):
        data=Data([text])
        if format is not None:
            data.format=format
        self.append(data)
    def add_method(self,m):
        try:
            return self.methods[id(m)]
        except KeyError:
            pass
        if isinstance(m,Function):
            method = m
        elif callable(m):
            method = XMLRPCMethod(m)
        else:
            raise TypeError('m must be a Function or callable')
        if len(self.methods)==0:
            self.head.append('''
<script type="text/javascript" src="/jsolait/jsolait.js"></script>
<script type="text/javascript">jsolait.baseURI="/jsolait";</script>
<script type="text/javascript">

var xmlrpc=null;
try{
  var xmlrpc = imprt("xmlrpc");
}catch(e){
  alert(e);
  throw "importing of xmlrpc module failed.";
}
pyshServer="http://localhost:8000";
</script>
            ''')
        self.head.append(str(method))
        self.methods[id(m)] = method
        return method
    def assign_ID(self,e,label='input'):
        if not hasattr(e,'ID'):
            e.ID = label+str(self.n)
            self.n += 1

class Function(object):
    'to make a js function, create an instance and add name and code attributes'
    def __str__(self):
        return self.code

class ValueSetter(Function):
    def __init__(self,name,target,doc):
        self.name = name
        self.target = target
        doc.assign_ID(target)
        doc.add_method(self)
    def __str__(self):
        s = '<script type="text/javascript">\n'
        s += '%s=function(rslt,errmsg)\n{\n  %s=rslt;\n}\n</script>\n' \
             % (self.name,get_element_js(self.target))
        return s


class XMLRPCMethod(Function):
    def __init__(self,m):
        try:
            self.xmlrpc = m.__module__ + '.' + m.__name__
        except AttributeError:
            self.xmlrpc = m
        self.name = '_'.join(self.xmlrpc.split('.'))
    def __str__(self):
        s = '<script type="text/javascript">\n'
        s += '%s=new xmlrpc.XMLRPCMethod(pyshServer,"%s",null,null);\n</script>\n' \
             % (self.name,self.xmlrpc)
        return s

class Action(object):
    def __init__(self,label,doc,m,*args,**kwargs):
        self.method = doc.add_method(m)
        self.args = []
        for arg in args:
            if isinstance(arg,str):
                self.args.append("'%s'" % arg)
            elif isinstance(arg,int) or isinstance(arg,long):
                self.args.append("'%d'" % arg)
            else:
                doc.assign_ID(arg)
                try:
                    self.args.append(get_element_js(arg))
                except TypeError:
                    self.args.append(str(arg))
        try: # ADD ASYNCHRONOUS CALLBACK
            self.args.append(kwargs['callback'].name)
        except KeyError:
            pass
        self.label = label
    def __str__(self):
        return '<button type="button" onclick="%s(%s)">%s</button>' \
               % (self.method.name,','.join(self.args),self.label)


class Link(object):
    def __init__(self,url,txt,label=None):
        self.url = get_method_path(url)
        self.txt = txt
        self.label = label
    def __str__(self):
        if self.label is not None:
            return '<A HREF="%s" TITLE="%s">%s</A>' % (self.url,self.label,self.txt)
        else:
            return '<A HREF="%s">%s</A>' % (self.url,self.txt)


def get_method_path(m):
    if isinstance(m,str):
        return m
    else:
        l = ['']+m.__module__.split('.')+[m.__name__]
        return '/'.join(l)

def get_element_jsvalue(e):
    return "document.getElementById('%s').value" % e.ID

def get_element_jstext(e):
    return "document.getElementById('%s').innerHTML" % e.ID

def get_element_js(e):
    if isinstance(e,Variable):
        return get_element_jsvalue(e)
    elif isinstance(e,Data):
        return get_element_jstext(e)
    else:
        raise TypeError('e must be Variable or Data!')


class Form(list):
    def __init__(self,m,method="POST",label='Go!',**kwargs):
        list.__init__(self)
        self.url = get_method_path(m)
        self.method = method
        self.label = label
        self.kwargs = kwargs
        self.enctype = None
    def __str__(self):
        s='<FORM METHOD="%s" ACTION="%s"' % (self.method,self.url)
        if self.enctype:
            s += ' enctype="%s"' % self.enctype
        s += '>\n'
        for v in self:
            s+=str(v)
        if self.label is not None:
            s += str(Input('','submit',self.label))
        for k,v in self.kwargs.items():
            s += str(Input(k,'hidden',v))
        s += '</FORM>\n\n'
        return s
    def append(self, v):
        'automatically sets right encoding if file upload input appended'
        if isinstance(v, Upload):
            self.enctype = "multipart/form-data"
        list.append(self, v)

class Separator(object):
    def __str__(self):
        return '<BR><HR><BR>\n'

class Variable(object):
    pass

class Input(Variable):
    def __init__(self,name,type='text',value='',size=20,maxlength=None,
                 checked=None,separator=''):
        self.name=name
        self.type=type
        self.size=size
        try:
            self.value=value.items()
        except AttributeError:
            self.value=value
        self.maxlength=maxlength
        self.checked=checked
        self.separator=separator
    def field_list(self,*args):
        s = ''
        for arg in args:
            try:
                s += ' %s="%s"' % (arg,getattr(self,arg))
            except AttributeError:
                pass
        return s
    def __str__(self):
        if self.type=='text' or self.type == 'password':
            return '\t<INPUT%s/>\n' \
                   % self.field_list('type','name','size','value','ID')
        elif self.type=='hidden':
            return '\t<INPUT%s/>\n' \
                   % self.field_list('type','name','value','ID')
        elif self.type=='submit':
            return '\t<INPUT TYPE="%s" VALUE="%s"/>\n' % (self.type,self.value)
        elif self.type=='reset':
            return '\t<INPUT TYPE="%s"/>\n' % self.type
        s=''
        for k,v in self.value:
            if k==self.checked:
                s+='\t<INPUT TYPE="%s" NAME="%s" VALUE="%s" CHECKED/>%s%s\n' \
                    % (self.type,self.name,k,v,self.separator)
            else:
                s+='\t<INPUT TYPE="%s" NAME="%s" VALUE="%s"/>%s%s\n' \
                    % (self.type,self.name,k,v,self.separator)
        return s

class Upload(Variable):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '<input type="file" name="%s" />' % self.name

class Textarea(Variable):
    def __init__(self, name, value='', cols='80', rows='24', wrap='off'):
        self.name=name
        self.value = value
        self.cols = cols
        self.rows = rows
        self.wrap = wrap
    def __str__(self):
        s = '''<TEXTAREA NAME="%s" COLS=%s ROWS=%s WRAP="%s">%s</TEXTAREA>\n''' \
            % (self.name, self.cols, self.rows, self.wrap, self.value)
        return s

class Selection(Variable):
    def __init__(self, name, value, size=None, multiple=False, selected=None,
                 **kwargs):
        self.name=name
        self.size=size
        try:
            self.value=value.items()
        except AttributeError:
            self.value=value
        self.multiple=multiple
        self.selected=selected
        self.kwargs = kwargs
    def __str__(self):
        s='\t<SELECT NAME="%s"' % self.name
        if self.size is not None:
            s+=' SIZE=%d' % self.size
        if self.multiple:
            s+=' MULTIPLE'
        for t in self.kwargs.items():
            s += ' %s="%s"' % t
        s+='>\n'
        for k,v in self.value:
            if k==self.selected:
                s+='\t\t<OPTION SELECTED VALUE="%s">%s</OPTION>\n' % (k,v)
            else:
                s+='\t\t<OPTION VALUE="%s">%s</OPTION>\n' % (k,v)
        s+='\t</SELECT>\n'
        return s

class RadioSelection(Selection):
    _type = 'radio'
    def __str__(self):
        s = ''
        for k,v in self.value:
            if k == self.selected:
                s += '\t\t<INPUT TYPE="%s" NAME="%s" VALUE="%s" CHECKED>%s<BR>\n' \
                    % (self._type, self.name, k, v)
            else:
                s += '\t\t<INPUT TYPE="%s" NAME="%s" VALUE="%s">%s<BR>\n' \
                    % (self._type, self.name, k, v)
        return s
    
class CheckboxSelection(RadioSelection):
    _type = 'checkbox'
    def __init__(self, *args, **kwargs):
        RadioSelection.__init__(self, *args, **kwargs)
        if self.multiple: # make form return array of values
            self.name = self.name + '[]'
