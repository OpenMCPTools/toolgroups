import pytest
from toolgroups import (
    Group, Tool, ToolGroupConverter, ToolConverter, 
    ToolgroupMCPServer, EXTENSION_ID, GroupSchema
)
import mcp.types as mcpt

def test_group_initialization_and_validation():
    # Test valid initialization
    g = Group(name="root", title="Root Group", description="Desc")
    assert g.name == "root"
    assert g.title == "Root Group"
    assert g.description == "Desc"
    assert g.is_root() is True

    # Test name validation
    with pytest.raises(ValueError, match="name must not be null, empty, or blank"):
        Group(name="")
    with pytest.raises(ValueError, match="name must not be null, empty, or blank"):
        Group(name="   ")

def test_group_hierarchy():
    root = Group(name="root")
    child = Group(name="child", parent=root)
    grandchild = Group(name="grandchild")
    
    assert child.parent == root
    assert child in root.get_child_groups()
    assert child.fqname == "root.child"
    
    child.add_child_group(grandchild)
    assert grandchild.parent == child
    assert grandchild.fqname == "root.child.grandchild"
    assert grandchild.get_root() == root
    
    # Test removal
    root.remove_child_group(child)
    assert child.parent is None
    assert child.is_root() is True
    assert child.fqname == "child"

def test_tool_and_group_association():
    root = Group(name="math")
    tool = Tool(name="add", parent=root, description="Add numbers")
    
    assert tool.name == "add"
    assert tool.fqname == "math.add"
    assert root in tool.get_parent_groups()
    assert tool in root.get_child_tools()
    
    # Test multi-parent
    other_group = Group(name="utils")
    tool.add_parent_group(other_group)
    assert other_group in tool.get_parent_groups()
    assert len(tool.get_parent_groups()) == 2

def test_fqname_custom_separator():
    root = Group(name="a", name_separator="/")
    child = Group(name="b", parent=root, name_separator="/")
    tool = Tool(name="c", parent=child, name_separator="/")
    
    assert child.fqname == "a/b"
    assert tool.fqname == "a/b/c"

def test_tool_group_converter():
    converter = ToolGroupConverter()
    
    # Test convert_from (Group -> GroupSchema)
    g = Group(name="test_group", title="Title", meta={"key": "value"})
    schema = converter.convert_from(g)
    assert isinstance(schema, GroupSchema)
    assert schema.name == "test_group"
    assert schema.title == "Title"
    assert schema.meta == {"key": "value"}
    
    # Test convert_to (GroupSchema/dict -> Group)
    # Using dict (as pydantic might)
    source_dict = {"name": "cached_group", "title": "Cached"}
    g_converted = converter.convert_to(source_dict)
    assert g_converted.name == "cached_group"
    
    # Test caching
    g_cached = converter.convert_to({"name": "cached_group"})
    assert g_converted is g_cached

def test_tool_converter():
    tc = ToolConverter()
    
    # Test convert_from (Internal Tool -> mcpt.Tool)
    g = Group(name="grp")
    t = Tool(name="mytool", parent=g, description="desc")
    mcp_tool = tc.convert_from(t)
    
    assert mcp_tool.name == "grp.mytool"
    assert EXTENSION_ID in mcp_tool.meta
    # The first element in meta[EXTENSION_ID] should represent the parent group
    group_meta = mcp_tool.meta[EXTENSION_ID][0]
    assert group_meta.name == "grp"

    # Test convert_to (mcpt.Tool -> Internal Tool)
    # Re-using the converted mcp_tool
    t_back = tc.convert_to(mcp_tool)
    assert t_back.name == "mytool"
    assert t_back.fqname == "grp.mytool"
    assert t_back.get_parent_groups()[0].name == "grp"

def test_toolgroup_mcp_server_decorator():
    # Since MCPServer might require a name and complex setup, we mock where needed
    # but here we test the logic of the decorators in ToolgroupMCPServer.
    server = ToolgroupMCPServer("test-server")
    
    root_group = Group(name="external")

    @server.toolgroup(parent=root_group, name="mygroup", title="My Group Title")
    class MyTools:
        @server.tool(name="action", title="Action Tool")
        def do_something(self, val: int) -> int:
            return val

    # Verify the group was created and assigned
    assert server._toolgroup is not None
    assert server._toolgroup.name == "mygroup"
    assert server._toolgroup.parent == root_group
    assert server._toolgroup.title == "My Group Title"
    
    # Verify the tool was added to the MCPServer (internal list)
    # In MCPServer, tools are usually stored in a way we can check via list_tools or internal state
    # ToolgroupMCPServer calls super().add_tool which populates the server's tool registry.
    
    # We can check if the tool is in the group
    child_tools = server._toolgroup.get_child_tools()
    assert len(child_tools) == 1
    assert child_tools[0].name == "action"
    assert child_tools[0].fqname == "external.mygroup.action"

def test_toolgroup_mcp_server_add_tool_direct():
    server = ToolgroupMCPServer("test-server")
    g = Group(name="manual")
    
    def my_fn(x: int): return x
    
    server.add_tool(my_fn, name="manual_tool", parent=g, title="Manual")
    
    # Check if tool is associated with group
    assert len(g.get_child_tools()) == 1
    assert g.get_child_tools()[0].name == "manual_tool"
    assert g.get_child_tools()[0].fqname == "manual.manual_tool"

def test_abstract_base_properties():
    class Concrete(Group): # Group is a concrete impl of AbstractBase
        pass
    
    obj = Concrete(name="test")
    obj.title = "New Title"
    obj.description = "New Desc"
    icons = [mcpt.Icon(src="uri", type="image/png")]
    obj.icons = icons
    meta = {"foo": "bar"}
    obj.meta = meta
    
    assert obj.title == "New Title"
    assert obj.description == "New Desc"
    assert obj.icons == icons
    assert obj.meta == meta
