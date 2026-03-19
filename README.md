# MCP Toolgroups Server Extension

[MCP servers](https://modelcontextprotocol.io/docs/learn/server-concepts) frequently have a large number of mcp tools to expose. This is especially true
for enterprise servers and gateways, that need to aggregate and expose multiple tools to clients.

This project provides an extension for the [MCP python sdk](https://github.com/modelcontextprotocol/python-sdk) to support the use of
server toolgroups.

Toolgroups represent collections of MCP tools. Groups may be hierarchical or flat, as defined by the developer. These groupings may or may not be communicated to MCP clients as this decision can be made at request time, and so may be based upon arbitrary server criteria (e.g. current security boundaries, user role/authorization, organizational governance, and administration, etc).

Toolgroups also provide a way to prevent or reduce the inefficiencies in 
context exchange between clients and servers with many tools (e.g. gateways). [See here for a clear description of this context bloat and aggregation problem](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/2204?sort=new#discussioncomment-15994902).

Groups may also have their own metadata (e.g. title, description, etc) defined by the server. This metadata can be used to define
domain-appropriate abstractions for use by clients. 

## Example: Arithmetic

A common example for server-side tools in the python sdk is a simple
add function decorated with @mcp.tool decorator:

```python
mcp = MCPServer('my server')

@mcp.tool(title="Add two integers")
def add(x: int, y: int) -> int:
	'''adds to integers and returns integer result'''
	return x + y
	
...allow clients to /list tools, which will include add
```

With the toolgroups extension, it's possible to define a Arithmetic group via a class decorator called toolgroup

```python
# Create server
tg_server = ToolgroupMCPServer("toolgroup server")

# use toolgroup class annotation and mcp.tool annotations for tools
@tg_server.toolgroup(parent=trusted_groups, title="Arithmetic", description="Arithmetic Group")
class Arithmetic:
    @tg_server.tool(title="Add X and Y Integer", annotations=ToolAnnotations(read_only_hint=True), structured_output=True)
    def add(self, x: int, y: int) -> int:
        ''' add two numbers'''
        return x + y
    
    @tg_server.tool(title="Multiply X and Y", annotations=ToolAnnotations(read_only_hint=True), structured_output=True)
    def multiply(self, x: int, y: int) -> int:
        '''multiply two numbers'''
        return x * y 
```

The full source for the above is in [this example](./examples/tg_server_class.py).

Note that the Arithmetic Group has a parent trusted_groups defined:

```python
@tg_server.toolgroup(parent=trusted_groups, title="Arithmetic", description="Arithmetic Group")
...
```
trusted_groups is defined before this usage and so defines a two-level group
hierarchy

```python
# create trusted group
trusted_groups=Group(name="trustedgroup",title="Trusted Toolgroups", description="The tools and toolgroups in this group are trusted by this server")
...
```
Note that Groups may be dynamically built and added to ToolgroupsMCPServers
also.  The [examples/tg_server_dyn.py](./examples/tg_server_dyn.py) does this rather than declaring
a Arithmetic class as a toolgroup.

# API Tests

```text
uv run pytest tests/api_tests.py
```
# Running Examples

```text
uv run python examples/tg_server_class.py

or

uv run python examples/tg_server_dyn.py
```

Note: The python sdk has recently refactored the MCPServer class (previously known as FastMCP). Since there is not yet a released 
version of the python sdk, this uv dependency is on the python-sdk
git repository source code.

# Group Schema

```json
        "Group": {
            "properties": {
                "name": {
                    "type": "string"
                },
                "parent": {
                    "$ref": "#/definitions/Group",
                },
                "description": {
                    "type": "string"
                },
                "title": {
                    "type": "string"
                },
                "_meta": {
                    "additionalProperties": {},
                    "type": "object"
                }
            },
            "required": [
                "name"
            ],
            "type": "object"
        }
```
The pydantic model declaration for this class is [here](./src/toolgroups/__init__.py#L12)
