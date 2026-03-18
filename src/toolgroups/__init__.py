from pydantic import ConfigDict, Field
import abc 

from typing import List, Any, Dict, Self, Tuple, Callable, Literal
import mcp.types as mcpt
from mcp.server.mcpserver.server import _CallableT, MCPServer
import itertools
'''Extension ID used to by Tool/Group Converter classes to convert _meta entry to/from
list of groups'''
EXTENSION_ID = "org.openmcptools/groups"
    
class GroupSchema(mcpt.BaseMetadata):
    '''schema for group extension.  Inherit name, title members from BaseMetadata'''
    description: str | None = None

    parent: Self | None = None

    meta: dict[str, Any] | None = Field(alias="_meta", default=None)

    model_config = ConfigDict(extra="allow")

class AbstractBase(abc.ABC):
    DEFAULT_SEPARATOR = "."

    _name: str
    _name_separator: str = DEFAULT_SEPARATOR
    _title: str | None = None 
    _description: str | None = None
    _icons: List[mcpt.Icon] | None = None 
    _meta: dict[str, Any] | None = None 
    
    def __init__(self, 
                 name: str, 
                 name_separator: str = None, 
                 title: str = None, 
                 description: str = None, 
                 icons: List[mcpt.Icon] = None, 
                 meta: dict[str,Any] = None):
        # Validation for name parameter
        if name is None or len(name) == 0 or name.isspace():
            raise ValueError("name must not be null, empty, or blank")
        self._name = name
        if name_separator:
            self._name_separator = name_separator
        self._title = title
        self._description = description
        self._icons = icons
        self._meta = meta

    @property
    def name_separator(self):
        return self._name_separator
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, description: str):
        self._description = description

    @property
    def icons(self) -> List[mcpt.Icon]:
        return self._icons

    @icons.setter
    def icons(self, icons: List[mcpt.Icon]):
        self._icons = icons

    @property
    def meta(self) -> Dict[str, Any]:
        return self._meta

    @meta.setter
    def meta(self, meta: Dict[str, Any]):
        self._meta = meta

    def _add(self, child, l: list, fn):
        if not child in l:
            l.append(child)
            if fn:
                fn()
            return True 
        return False

    def _remove(self, child, l: list, fn):
        if child in l:
            l.remove(child)
            if fn:
                fn()
            return True 
        return False 

    @abc.abstractmethod
    def fqname(self) -> str:
        pass

class Group(AbstractBase):
    
    _child_groups: List[Self] | None
    _child_tools: List['Tool'] | None
    _parent: Self | None = None 
    
    def __init__(self, name: str, parent: Self = None, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self._child_groups = []
        self._child_tools = []
        if parent:
            parent.add_child_group(self)

    @property
    def parent(self) -> Self:
        return self._parent
    
    def _set_parent(self, parent_group: Self):
        self._parent = parent_group
        
    def is_root(self) -> bool:
        return self._parent is None
    
    def get_root(self) -> 'Group':
        if self._parent is None:
            return self
        else:
            return self._parent.get_root()

    def add_child_group(self, child_group: 'Group') -> bool:
        return self._add(child_group, self._child_groups, lambda: child_group._set_parent(self))

    def remove_child_group(self, child_group: 'Group') -> bool:
        return self._remove(child_group, self._child_groups, lambda: child_group._set_parent(None))

    def get_child_groups(self) -> List['Group']:
        return self._child_groups

    def add_child_tool(self, child_tool: 'Tool') -> bool:
        return self._add(child_tool, self._child_tools, lambda: child_tool.add_parent_group(self))

    def remove_child_tool(self, child_tool: 'Tool') -> bool:
        return self._remove(child_tool, self._child_tools, lambda: child_tool.remove_parent_group(self))

    def get_child_tools(self) -> List['Tool']:
        return self._child_tools

    def _get_fq_name(self, tg: 'Group') -> str:
        parent = tg._parent
        if parent is not None:
            parent_name = self._get_fq_name(parent)
            return parent_name + self.name_separator + tg.name
        return tg.name

    @property
    def fqname(self) -> str:
        return self._get_fq_name(self)
    
    def __str__(self):
        return f' name={self.name} fqname={self.fqname} parent={self.parent} title={self.title} description={self.description} meta={self.meta}'

class AbstractLeaf(AbstractBase):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self._parent_groups = []

    def add_parent_group(self, parent_group: Group) -> bool:
        return self._add(parent_group, self._parent_groups, None)

    def remove_parent_group(self, parent_group: Group) -> bool:
        return self._remove(parent_group, self._parent_groups, None)

    def get_parent_groups(self) -> List[Group]:
        return self._parent_groups

    def _get_primary_parent_name(self) -> str:
        return self._parent_groups[0].fqname \
            if len(self._parent_groups) > 0 else None

    @property
    def fqname(self) -> str:
        first_parent_name = self._get_primary_parent_name()
        return self.name if first_parent_name is None else first_parent_name + self.name_separator + self.name

class Tool(AbstractLeaf):
    
    _annotations: mcpt.ToolAnnotations | None = None 
    _input_schema: dict[str, Any] | None = None
    _output_schema: dict[str, Any] | None = None 
    
    def __init__(self, 
                 name: str, 
                 name_separator: str = AbstractBase.DEFAULT_SEPARATOR, 
                 parent: Group = None, 
                 title: str = None, description: str = None, 
                 icons: List[mcpt.Icon] = None, 
                 annotations: mcpt.ToolAnnotations = None, 
                 input_schema: dict = {},
                 output_schema: dict = None,
                 meta: Dict[str, Any] = None):
        super().__init__(name=name, 
                         name_separator=name_separator, 
                         title=title, 
                         description=description, 
                         icons=icons, 
                         meta=meta)
        self._annotations = annotations
        self._input_schema = input_schema
        self._output_schema = output_schema
        if parent:
            parent.add_child_tool(self)

    def get_roots(self):
        return list(dict.fromkeys(g for g in self.get_parent_groups()))
        
    @property
    def annotations(self) -> mcpt.ToolAnnotations:
        return self._annotations

    @annotations.setter
    def annotations(self, value: mcpt.ToolAnnotations):
        self._annotations = value
        
    @property
    def input_schema(self) -> dict[str, Any]:
        return self._input_schema
    
    @input_schema.setter 
    def input_schema(self, value: dict):
        self._input_schema = value
        
    @property
    def output_schema(self):
        return self._output_schema
    
    @output_schema.setter 
    def output_schema(self, value: dict):
        self._input_schema = value
        
    def __str__(self):
        return f' name={self.name} fqname={self.fqname} title={self.title} description={self.description} input_schema={self.input_schema} output_schema={self.output_schema} icons={self.icons} annotations=ToolAnnotations({self.annotations}) meta={self.meta} parent_groups={self.get_parent_groups()}'

class ToolGroupConverter():
    
    _group_cache: Dict[str, Group] = None
    
    def __init__(self):
        self._group_cache = dict()
        
    def convert_to(self, source):  
        # pydantic provides dict when deserializing
        if isinstance(source, dict):
            name = source.get('name')
            parent = source.get('parent', None)
            title = source.get('title', None)
            description = source.get('description', None)
            meta = source.get('meta', None)
        else:
            name = source.name
            parent = source.parent
            title = source.title 
            description = source.description 
            meta = source.meta
        '''get from cache if present'''
        g = self._group_cache.get(name)
        if not g:
            g = Group(name=name,
                      parent=self.convert_to(parent) if parent else None,
                      title=title,
                      description=description,
                      meta=meta)
            '''place in cache by name'''
            self._group_cache[name] = g
        return g
            
    def convert_from(self, target):
        return GroupSchema(name=target.name, 
                           parent=self.convert_from(target.parent) if target.parent else None,
                           title=target.title, 
                           description=target.description, 
                           meta=target.meta)
    
    def convert_to_list(self, sources: List[GroupSchema]) -> List[Group]:
        if not sources:
            return None
        return [self.convert_to(s) for s in sources]
    def convert_from_list(self, targets: List[Group]) -> List[GroupSchema]:
        if not targets:
            return None
        return [self.convert_from(s) for s in targets]


class ToolConverter():
    def __init__(self):
        self._group_converter = ToolGroupConverter()
        
    def _convert_from_groupex(self, t_name: str, t_meta: dict) -> Tuple :
        '''converts name and meta to a tuple with 4 elements:
        0=tool_name,1=parent,2=tool meta,3=extra parent groups'''
        name = str(t_name)
        meta = dict(t_meta) if t_meta and len(t_meta) > 0 else None 
        parent = None
        extra = []
        if meta:
            gex = self._group_converter.convert_to_list(meta.pop(EXTENSION_ID,[]))
            if gex:
                '''parent is assumed to be first in list'''
                parent = gex[0]
                '''modify the tool name by removing the parent fully qualified name'''
                name = name[len(parent.fqname)+len(parent.name_separator):]
                '''remove parent element and leave any remaining groups'''
                extra = gex[1:]
        return (name, parent, meta if meta and len(meta) > 0 else None, extra if extra else None)

    def _convert_to_groupex(self, parent_groups: List[Group], t_meta: dict) -> Tuple:
        groups = self._group_converter.convert_from_list(parent_groups)
        meta = dict(t_meta) if t_meta else dict() 
        if groups:
            meta[EXTENSION_ID] = groups
        return meta if len(meta) > 0 else None
    
    def convert_to(self, s: mcpt.Tool) -> Tool:
        '''first convert from groupex'''
        ext = self._convert_from_groupex(s.name, s.meta)
        '''tuple result: 0=tool_name, 1=parent group, 2=meta'''
        t = Tool(name=ext[0], 
                 parent=ext[1],
                 title=s.title, 
                 description=s.description, 
                 icons=s.icons,
                 input_schema=s.input_schema,
                 output_schema=s.output_schema,
                 annotations = s.annotations, 
                 meta=ext[2])
        '''tuple result 3=list of additional parents'''
        if ext[3]:
            for g in ext[3]:
                g.add_child_tool(t)
        return t
    
    def convert_to_list(self, tools: List[mcpt.Tool]) -> List[Tool]:
        return [self.convert_to(t) for t in tools]
    
    def convert_from(self, t: Tool) -> mcpt.Tool:
        '''first convert to groupex'''
        meta = self._convert_to_groupex(t.get_parent_groups(), t.meta)
        '''tuple result: 0=parent, 1=meta'''
        return mcpt.Tool(name=t.fqname,
                      title=t.title,
                      description=t.description,
                      icons=t.icons,
                      input_schema=t.input_schema,
                      output_schema=t.output_schema,
                      annotations=t.annotations,
                      meta=meta if meta and len(meta) > 0 else None)

    def convert_from_list(self, tools: List[Tool]) -> List[mcpt.Tool]:
        return [self.convert_from(t) for t in tools]
    
class ToolgroupMCPServer(MCPServer):
    '''override of MCPServer so that mcp.toolgroup class decorator and add_tool_ex (Tool) method added'''
    
    _toolgroup: Group | None
    _tool_converter: ToolConverter
    __tools_init: List[Tuple[Callable, dict]]
    '''members for processing of toolgroup class decorator processing'''
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__tools_init = []
        self._toolgroup = None 
        self._tool_converter = ToolConverter()
        
    def get_toolgroup(self) -> Group:
        return self._group
    
    def tool(self,
        *args, **kwargs)-> Callable[[_CallableT], _CallableT]:
        '''override of MCPServer.tool decoarator.  Rather than adding tools directly, this
        decorator defers the addition until after the toolgroup class decorator is called,
        so that the toolgroup can be assigned
        '''
        def decorator(fn: _CallableT) -> _CallableT:
            '''Add kwargs to __tools_init.  These will be used to add tools in
            the toolgroups decorator method'''
            self.__tools_init.append((fn, kwargs))
            return fn
        return decorator
    
    def toolgroup(self, *args, **kwargs):
        '''toolgroup class decorator.  Allows class declarations to be used to define a group of tools'''
        def decorator(cls):
            if not kwargs.get('name', None):
                kwargs['name'] = ".".join([cls.__module__,cls.__qualname__])
            self._toolgroup = Group(name=kwargs['name'],
                                    title=kwargs.get('title',None),
                                    parent=kwargs.get('parent', None),
                                    description=kwargs.get('description', None),
                                    meta=kwargs.get('meta',None))
            for fn, kw in self.__tools_init:
                if not 'name' in kw:
                    kw['name'] = fn.__name__
                self.add_tool(fn, 
                                 kw.get('name'),
                                 title=kw.get('title',None),
                                 parent=self._toolgroup,
                                 description=kw.get('description', None),
                                 annotations=kw.get('annotations', None),
                                 icons=kw.get('icons', None),
                                 meta=kw.get('meta', None), 
                                 structured_output=kw.get('structured_output',None))
        return decorator

    def add_tool(self, 
                    fn: Callable[..., Any],
                    name: str | None = None,
                    parent: Group | None = None,
                    title: str | None = None,
                    description: str | None = None,
                    annotations: mcpt.ToolAnnotations | None = None,
                    icons: list[mcpt.Icon] | None = None,
                    meta: dict[str, Any] | None = None,
                    structured_output: bool | None = None) -> mcpt.Tool:
        if not name:
            name = fn.__name__
        ct = self._tool_converter.convert_from(Tool(name=name,
                                                    parent=parent,
                                                    title=title,
                                                    description=description,
                                                    annotations=annotations,
                                                    icons=icons,
                                                    meta=meta))
        super().add_tool(fn,
                         name=ct.name, 
                         title=ct.title,
                         description=ct.description,
                         annotations=ct.annotations,
                         icons=ct.icons,
                         meta=ct.meta,
                         structured_output=structured_output)

